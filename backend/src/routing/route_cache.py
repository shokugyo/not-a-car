"""事前計算ルートキャッシュ"""

import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# デフォルトのキャッシュファイルパス
DEFAULT_ROUTE_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "route_cache.json"


class CachedRoute(BaseModel):
    """事前計算されたルート情報"""
    origin_id: str = Field(..., description="出発地点ID")
    destination_id: str = Field(..., description="目的地ID")
    distance_km: float = Field(..., description="道路距離 (km)")
    duration_minutes: int = Field(..., description="所要時間 (分)")
    polyline: str = Field("", description="エンコードされたポリライン（地図表示用）")
    waypoints: list[list[float]] = Field(
        default_factory=list,
        description="経由地点の座標リスト [[lat, lng], ...]"
    )


class RouteCache:
    """
    事前計算ルートキャッシュ

    主要地点間のルート情報（距離、時間、ポリライン）を
    メモリ内に保持し、高速な検索を提供する。
    """

    def __init__(self, cache_path: Optional[Path] = None):
        self.cache_path = cache_path or DEFAULT_ROUTE_CACHE_PATH
        self._routes: dict[str, CachedRoute] = {}  # "origin_id:destination_id" -> CachedRoute
        self._loaded = False

    def _make_key(self, origin_id: str, destination_id: str) -> str:
        """キャッシュキーを生成"""
        return f"{origin_id}:{destination_id}"

    def load(self) -> bool:
        """キャッシュファイルを読み込む"""
        if self._loaded:
            return True

        if not self.cache_path.exists():
            logger.warning(f"Route cache file not found: {self.cache_path}")
            return False

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            routes = data.get("routes", [])
            for route_data in routes:
                route = CachedRoute(**route_data)
                key = self._make_key(route.origin_id, route.destination_id)
                self._routes[key] = route

            self._loaded = True
            logger.info(f"Loaded {len(self._routes)} routes from cache")
            return True

        except Exception as e:
            logger.error(f"Failed to load route cache: {e}")
            return False

    def get(self, origin_id: str, destination_id: str) -> Optional[CachedRoute]:
        """
        ルートを取得

        Args:
            origin_id: 出発地点ID
            destination_id: 目的地ID

        Returns:
            キャッシュされたルート情報、なければNone
        """
        self._ensure_loaded()
        key = self._make_key(origin_id, destination_id)
        return self._routes.get(key)

    def get_from_default_origin(self, destination_id: str) -> Optional[CachedRoute]:
        """
        デフォルト出発地点（東京駅）からのルートを取得

        Args:
            destination_id: 目的地ID

        Returns:
            キャッシュされたルート情報
        """
        return self.get("tokyo_station", destination_id)

    def has_route(self, origin_id: str, destination_id: str) -> bool:
        """ルートがキャッシュされているか確認"""
        self._ensure_loaded()
        key = self._make_key(origin_id, destination_id)
        return key in self._routes

    def get_all_from_origin(self, origin_id: str) -> list[CachedRoute]:
        """指定出発地点からの全ルートを取得"""
        self._ensure_loaded()
        prefix = f"{origin_id}:"
        return [
            route for key, route in self._routes.items()
            if key.startswith(prefix)
        ]

    def _ensure_loaded(self) -> None:
        """ロード済みを保証"""
        if not self._loaded:
            self.load()

    @property
    def count(self) -> int:
        """登録件数"""
        self._ensure_loaded()
        return len(self._routes)


# シングルトンインスタンス
_route_cache_instance: Optional[RouteCache] = None


def get_route_cache() -> RouteCache:
    """ルートキャッシュのシングルトンを取得"""
    global _route_cache_instance
    if _route_cache_instance is None:
        _route_cache_instance = RouteCache()
        _route_cache_instance.load()
    return _route_cache_instance
