"""ChromaDBを使用したベクトルストア"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Any

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None  # type: ignore
    ChromaSettings = None  # type: ignore
    CHROMADB_AVAILABLE = False

if TYPE_CHECKING:
    from chromadb import Client as ChromaClient

from src.geocoding import get_location_cache, Location

logger = logging.getLogger(__name__)

# デフォルトのChromaDB永続化パス
DEFAULT_CHROMA_PATH = Path(__file__).parent.parent.parent / "data" / "chroma_db"

# 日本語対応の軽量埋め込みモデル
# sentence-transformersが利用できない場合はChromaDBのデフォルト埋め込みを使用
DEFAULT_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class LocationVectorStore:
    """
    地点情報のベクトルストア

    ChromaDBを使用して地点情報を埋め込みベクトルとして保存し、
    セマンティック検索を可能にする。
    """

    COLLECTION_NAME = "locations"

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        embedding_model: Optional[str] = None,
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb is not installed. "
                "Install with: pip install chromadb sentence-transformers"
            )

        self.persist_directory = persist_directory or DEFAULT_CHROMA_PATH
        self.embedding_model = embedding_model or DEFAULT_EMBEDDING_MODEL
        self._client: Optional[ChromaClient] = None
        self._collection: Any = None
        self._initialized = False

    def _get_client(self) -> ChromaClient:
        """ChromaDBクライアントを取得（遅延初期化）"""
        if self._client is None:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.persist_directory),
                anonymized_telemetry=False,
            ))
        return self._client

    def _get_embedding_function(self):
        """埋め込み関数を取得"""
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}. Using default.")
            return None

    def _get_collection(self):
        """コレクションを取得または作成"""
        if self._collection is None:
            client = self._get_client()
            embedding_fn = self._get_embedding_function()

            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=embedding_fn,
                metadata={"description": "Location knowledge base for RAG"}
            )
        return self._collection

    def _location_to_document(self, location: Location) -> str:
        """Locationを検索用ドキュメント文字列に変換"""
        parts = [
            f"名前: {location.name}",
            f"都道府県: {location.prefecture}",
            f"種別: {location.type.value}",
        ]

        if location.description:
            parts.append(f"説明: {location.description}")

        if location.tags:
            parts.append(f"特徴: {', '.join(location.tags)}")

        if location.specialties:
            parts.append(f"名物: {', '.join(location.specialties)}")

        if location.best_season:
            parts.append(f"おすすめ時期: {location.best_season}")

        if location.facilities:
            parts.append(f"設備: {', '.join(location.facilities)}")

        if location.tips:
            parts.append(f"ヒント: {location.tips}")

        if location.ev_charging:
            parts.append("EV充電: 可能")

        if location.overnight_parking:
            parts.append("車中泊: 可能")

        return "\n".join(parts)

    def _location_to_metadata(self, location: Location) -> dict:
        """Locationをメタデータに変換"""
        return {
            "id": location.id,
            "name": location.name,
            "prefecture": location.prefecture,
            "type": location.type.value,
            "lat": location.lat,
            "lng": location.lng,
            "ev_charging": location.ev_charging,
            "overnight_parking": location.overnight_parking,
            "scenery_score": location.scenery_score,
            "noise_level": location.noise_level,
        }

    def initialize(self, force_rebuild: bool = False) -> bool:
        """
        ベクトルストアを初期化

        LocationCacheから全地点を読み込み、ベクトル化して保存。

        Args:
            force_rebuild: Trueの場合、既存データを削除して再構築

        Returns:
            成功した場合True
        """
        try:
            collection = self._get_collection()

            # 既存データのチェック
            existing_count = collection.count()
            if existing_count > 0 and not force_rebuild:
                logger.info(f"Vector store already initialized with {existing_count} documents")
                self._initialized = True
                return True

            # 強制再構築の場合は削除
            if force_rebuild and existing_count > 0:
                logger.info("Rebuilding vector store...")
                client = self._get_client()
                client.delete_collection(self.COLLECTION_NAME)
                self._collection = None
                collection = self._get_collection()

            # LocationCacheから全地点を取得
            location_cache = get_location_cache()
            locations = location_cache.get_all()

            if not locations:
                logger.warning("No locations found in cache")
                return False

            # ドキュメントを準備
            documents = []
            metadatas = []
            ids = []

            for location in locations:
                documents.append(self._location_to_document(location))
                metadatas.append(self._location_to_metadata(location))
                ids.append(location.id)

            # バッチで追加
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Initialized vector store with {len(locations)} locations")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[dict] = None,
    ) -> list[dict]:
        """
        セマンティック検索を実行

        Args:
            query: 検索クエリ
            n_results: 返す結果の数
            filter_dict: フィルタ条件（例: {"ev_charging": True}）

        Returns:
            検索結果のリスト。各結果は以下を含む:
            - id: 地点ID
            - document: ドキュメント文字列
            - metadata: メタデータ
            - distance: クエリとの距離（小さいほど類似）
        """
        if not self._initialized:
            self.initialize()

        collection = self._get_collection()

        # 検索実行
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict,
            include=["documents", "metadatas", "distances"],
        )

        # 結果を整形
        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, id_ in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": id_,
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                })

        return formatted_results

    @property
    def is_initialized(self) -> bool:
        """初期化済みかどうか"""
        return self._initialized

    @property
    def count(self) -> int:
        """ドキュメント数"""
        if not self._initialized:
            return 0
        return self._get_collection().count()


# シングルトンインスタンス
_vector_store_instance: Optional[LocationVectorStore] = None


def get_vector_store() -> LocationVectorStore:
    """ベクトルストアのシングルトンを取得"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = LocationVectorStore()
    return _vector_store_instance
