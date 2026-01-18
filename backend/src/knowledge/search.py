"""知識検索サービス"""

import logging
from typing import Optional
from dataclasses import dataclass

from src.geocoding import get_location_cache, Location

logger = logging.getLogger(__name__)


@dataclass
class LocationKnowledge:
    """地点の知識情報（LLMコンテキスト用）"""
    id: str
    name: str
    prefecture: str
    type: str
    description: str
    specialties: list[str]
    best_season: str
    tips: str
    facilities: list[str]
    ev_charging: bool
    overnight_parking: bool
    scenery_score: float
    relevance_score: float  # 検索クエリとの関連度（0-1、高いほど関連）

    def to_context_string(self) -> str:
        """LLMコンテキスト用の文字列に変換"""
        lines = [
            f"【{self.name}】（{self.prefecture}）",
            f"  種別: {self.type}",
        ]

        if self.description:
            lines.append(f"  概要: {self.description}")

        if self.specialties:
            lines.append(f"  名物: {', '.join(self.specialties)}")

        if self.best_season:
            lines.append(f"  おすすめ時期: {self.best_season}")

        if self.tips:
            lines.append(f"  ヒント: {self.tips}")

        features = []
        if self.ev_charging:
            features.append("EV充電可")
        if self.overnight_parking:
            features.append("車中泊可")
        if self.scenery_score >= 4.5:
            features.append("景観◎")

        if features:
            lines.append(f"  特徴: {', '.join(features)}")

        return "\n".join(lines)


class KnowledgeSearch:
    """
    地点知識検索サービス

    ベクトル検索とキーワード検索を組み合わせて、
    ユーザークエリに最も関連する地点情報を取得する。
    """

    def __init__(self, use_vector_search: bool = True):
        """
        Args:
            use_vector_search: Trueの場合、ベクトル検索を使用
                               Falseの場合、キーワード検索のみ
        """
        self.use_vector_search = use_vector_search
        self._vector_store = None
        self._location_cache = None

    def _get_location_cache(self):
        """LocationCacheを取得"""
        if self._location_cache is None:
            self._location_cache = get_location_cache()
        return self._location_cache

    def _get_vector_store(self):
        """ベクトルストアを取得（遅延初期化）"""
        if self._vector_store is None and self.use_vector_search:
            try:
                from .vector_store import get_vector_store
                self._vector_store = get_vector_store()
                self._vector_store.initialize()
            except ImportError:
                logger.warning("Vector store not available, falling back to keyword search")
                self.use_vector_search = False
            except Exception as e:
                logger.warning(f"Failed to initialize vector store: {e}")
                self.use_vector_search = False
        return self._vector_store

    def _location_to_knowledge(
        self,
        location: Location,
        relevance_score: float = 0.5,
    ) -> LocationKnowledge:
        """LocationをLocationKnowledgeに変換"""
        return LocationKnowledge(
            id=location.id,
            name=location.name,
            prefecture=location.prefecture,
            type=location.type.value,
            description=location.description or "",
            specialties=location.specialties,
            best_season=location.best_season or "",
            tips=location.tips or "",
            facilities=location.facilities,
            ev_charging=location.ev_charging,
            overnight_parking=location.overnight_parking,
            scenery_score=location.scenery_score,
            relevance_score=relevance_score,
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        require_ev_charging: bool = False,
        require_overnight_parking: bool = False,
    ) -> list[LocationKnowledge]:
        """
        クエリに関連する地点知識を検索

        Args:
            query: 検索クエリ（自然言語）
            n_results: 返す結果の数
            require_ev_charging: EV充電必須フィルタ
            require_overnight_parking: 車中泊可能必須フィルタ

        Returns:
            関連度順にソートされたLocationKnowledgeのリスト
        """
        results = []

        # ベクトル検索を試行
        if self.use_vector_search:
            vector_store = self._get_vector_store()
            if vector_store:
                # フィルタ構築
                filter_dict = None
                if require_ev_charging or require_overnight_parking:
                    filter_dict = {}
                    if require_ev_charging:
                        filter_dict["ev_charging"] = True
                    if require_overnight_parking:
                        filter_dict["overnight_parking"] = True

                vector_results = vector_store.search(
                    query=query,
                    n_results=n_results,
                    filter_dict=filter_dict,
                )

                # 結果をLocationKnowledgeに変換
                cache = self._get_location_cache()
                for vr in vector_results:
                    location = cache.get_by_id(vr["id"])
                    if location:
                        # 距離を関連度スコアに変換（距離が小さいほどスコアが高い）
                        # ChromaDBの距離は通常0-2の範囲
                        relevance = max(0, 1 - (vr["distance"] / 2))
                        results.append(self._location_to_knowledge(location, relevance))

                return results

        # フォールバック: キーワード検索
        return self._keyword_search(
            query=query,
            n_results=n_results,
            require_ev_charging=require_ev_charging,
            require_overnight_parking=require_overnight_parking,
        )

    def _keyword_search(
        self,
        query: str,
        n_results: int = 5,
        require_ev_charging: bool = False,
        require_overnight_parking: bool = False,
    ) -> list[LocationKnowledge]:
        """キーワードベースの検索（フォールバック）"""
        cache = self._get_location_cache()

        # クエリからキーワードを抽出（日本語対応）
        # スペース・句読点で分割 + 主要な日本語キーワードを抽出
        import re
        keywords = re.split(r'[\s、。・]+', query)
        # 日本語の重要キーワードを個別抽出
        japanese_keywords = [
            "温泉", "キャンプ", "道の駅", "RVパーク", "車中泊", "充電",
            "海", "山", "湖", "川", "滝", "森", "紅葉", "桜", "夜景",
            "静か", "景色", "絶景", "自然", "リラックス", "観光",
            "富士山", "箱根", "河口湖", "軽井沢", "日光", "草津",
        ]
        for kw in japanese_keywords:
            if kw in query and kw not in keywords:
                keywords.append(kw)
        keywords = [k for k in keywords if k]  # 空文字を除去

        # 全地点をスコアリング
        scored_locations = []
        for location in cache.get_all():
            # フィルタチェック
            if require_ev_charging and not location.ev_charging:
                continue
            if require_overnight_parking and not location.overnight_parking:
                continue

            # キーワードマッチングでスコア計算
            score = 0
            searchable_text = " ".join([
                location.name,
                location.prefecture,
                " ".join(location.aliases),
                " ".join(location.tags),
                location.description or "",
                " ".join(location.specialties),
                " ".join(location.facilities),
            ]).lower()

            for keyword in keywords:
                if keyword.lower() in searchable_text:
                    score += 1

            if score > 0:
                # スコアを0-1に正規化
                relevance = min(1.0, score / len(keywords)) if keywords else 0.5
                scored_locations.append((location, relevance))

        # スコア順にソート
        scored_locations.sort(key=lambda x: x[1], reverse=True)

        # 上位N件を返す
        results = []
        for location, relevance in scored_locations[:n_results]:
            results.append(self._location_to_knowledge(location, relevance))

        # 結果が少ない場合は景観スコアで補完
        if len(results) < n_results:
            existing_ids = {r.id for r in results}
            remaining = n_results - len(results)

            for location in cache.get_all():
                if location.id in existing_ids:
                    continue
                if require_ev_charging and not location.ev_charging:
                    continue
                if require_overnight_parking and not location.overnight_parking:
                    continue

                results.append(self._location_to_knowledge(location, 0.3))
                if len(results) >= n_results:
                    break

        return results

    def get_context_for_llm(
        self,
        query: str,
        n_results: int = 5,
        max_tokens: int = 1500,
    ) -> str:
        """
        LLMに渡すコンテキスト文字列を生成

        Args:
            query: 検索クエリ
            n_results: 検索結果数
            max_tokens: おおよその最大トークン数（文字数で概算）

        Returns:
            LLMコンテキスト用の文字列
        """
        results = self.search(query, n_results=n_results)

        if not results:
            return "（該当する地点情報が見つかりませんでした）"

        context_parts = ["## 候補地点情報\n"]
        current_length = len(context_parts[0])

        for result in results:
            context_string = result.to_context_string()
            # おおよそのトークン数を文字数で概算（日本語は1文字≈1-2トークン）
            estimated_tokens = len(context_string) * 1.5

            if current_length + estimated_tokens > max_tokens:
                break

            context_parts.append(context_string)
            context_parts.append("")  # 空行
            current_length += estimated_tokens

        return "\n".join(context_parts)

    def get_available_locations_summary(self) -> str:
        """利用可能な地点の概要を取得（LLMへの事前情報用）"""
        cache = self._get_location_cache()
        locations = cache.get_all()

        # 種別ごとにグループ化
        by_type: dict[str, list[str]] = {}
        for loc in locations:
            type_name = loc.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(loc.name)

        lines = ["## 利用可能な地点一覧\n"]
        for type_name, names in by_type.items():
            lines.append(f"- {type_name}: {', '.join(names[:5])}" +
                        (f" 他{len(names)-5}件" if len(names) > 5 else ""))

        return "\n".join(lines)


# シングルトンインスタンス
_knowledge_search_instance: Optional[KnowledgeSearch] = None


def get_knowledge_search(use_vector_search: bool = True) -> KnowledgeSearch:
    """KnowledgeSearchのシングルトンを取得"""
    global _knowledge_search_instance
    if _knowledge_search_instance is None:
        _knowledge_search_instance = KnowledgeSearch(use_vector_search=use_vector_search)
    return _knowledge_search_instance
