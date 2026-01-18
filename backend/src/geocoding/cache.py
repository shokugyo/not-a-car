"""座標キャッシュローダーと検索機能"""

import json
import logging
from pathlib import Path
from typing import Optional

from .models import Location, LocationType, SearchResult

logger = logging.getLogger(__name__)

# デフォルトのキャッシュファイルパス
DEFAULT_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "locations.json"


class LocationCache:
    """
    座標キャッシュ

    主要都市・観光地の座標情報をメモリ内に保持し、
    高速な検索を提供する。
    """

    def __init__(self, cache_path: Optional[Path] = None):
        self.cache_path = cache_path or DEFAULT_CACHE_PATH
        self._locations: dict[str, Location] = {}  # id -> Location
        self._name_index: dict[str, list[str]] = {}  # name/alias -> [ids]
        self._type_index: dict[LocationType, list[str]] = {}  # type -> [ids]
        self._tag_index: dict[str, list[str]] = {}  # tag -> [ids]
        self._prefecture_index: dict[str, list[str]] = {}  # prefecture -> [ids]
        self._loaded = False

    def load(self) -> bool:
        """キャッシュファイルを読み込む"""
        if self._loaded:
            return True

        if not self.cache_path.exists():
            logger.warning(f"Cache file not found: {self.cache_path}")
            return False

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            locations = data.get("locations", [])
            for loc_data in locations:
                location = Location(**loc_data)
                self._add_to_index(location)

            self._loaded = True
            logger.info(f"Loaded {len(self._locations)} locations from cache")
            return True

        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return False

    def _add_to_index(self, location: Location) -> None:
        """インデックスに追加"""
        self._locations[location.id] = location

        # 名前インデックス
        name_lower = location.name.lower()
        if name_lower not in self._name_index:
            self._name_index[name_lower] = []
        self._name_index[name_lower].append(location.id)

        # エイリアスもインデックス
        for alias in location.aliases:
            alias_lower = alias.lower()
            if alias_lower not in self._name_index:
                self._name_index[alias_lower] = []
            self._name_index[alias_lower].append(location.id)

        # タイプインデックス
        if location.type not in self._type_index:
            self._type_index[location.type] = []
        self._type_index[location.type].append(location.id)

        # タグインデックス
        for tag in location.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._tag_index:
                self._tag_index[tag_lower] = []
            self._tag_index[tag_lower].append(location.id)

        # 施設もタグとして追加
        for facility in location.facilities:
            facility_lower = facility.lower()
            if facility_lower not in self._tag_index:
                self._tag_index[facility_lower] = []
            self._tag_index[facility_lower].append(location.id)

        # 都道府県インデックス
        pref = location.prefecture
        if pref not in self._prefecture_index:
            self._prefecture_index[pref] = []
        self._prefecture_index[pref].append(location.id)

    def get_by_id(self, location_id: str) -> Optional[Location]:
        """IDで取得"""
        self._ensure_loaded()
        return self._locations.get(location_id)

    def get_by_name(self, name: str) -> Optional[Location]:
        """名前で取得（完全一致）"""
        self._ensure_loaded()
        ids = self._name_index.get(name.lower(), [])
        if ids:
            return self._locations.get(ids[0])
        return None

    def search_by_name(self, query: str) -> list[Location]:
        """名前で検索（部分一致）"""
        self._ensure_loaded()
        results = []
        query_lower = query.lower()

        for name, ids in self._name_index.items():
            if query_lower in name or name in query_lower:
                for loc_id in ids:
                    loc = self._locations.get(loc_id)
                    if loc and loc not in results:
                        results.append(loc)

        return results

    def search_by_type(self, location_type: LocationType) -> list[Location]:
        """タイプで検索"""
        self._ensure_loaded()
        ids = self._type_index.get(location_type, [])
        return [self._locations[loc_id] for loc_id in ids if loc_id in self._locations]

    def search_by_tags(self, tags: list[str]) -> list[Location]:
        """タグで検索（OR検索）"""
        self._ensure_loaded()
        result_ids: set[str] = set()

        for tag in tags:
            tag_lower = tag.lower()
            # 完全一致
            if tag_lower in self._tag_index:
                result_ids.update(self._tag_index[tag_lower])
            # 部分一致
            for indexed_tag, ids in self._tag_index.items():
                if tag_lower in indexed_tag or indexed_tag in tag_lower:
                    result_ids.update(ids)

        return [self._locations[loc_id] for loc_id in result_ids if loc_id in self._locations]

    def search(
        self,
        place_names: Optional[list[str]] = None,
        facility_types: Optional[list[str]] = None,
        amenities: Optional[list[str]] = None,
        atmosphere: Optional[list[str]] = None,
        prefecture: Optional[str] = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        複合検索

        LLMで抽出した情報を元に、マッチする場所を検索する。
        """
        self._ensure_loaded()
        scores: dict[str, tuple[float, list[str]]] = {}  # id -> (score, reasons)

        def add_score(loc_id: str, score: float, reason: str):
            if loc_id not in scores:
                scores[loc_id] = (0.0, [])
            current_score, reasons = scores[loc_id]
            scores[loc_id] = (current_score + score, reasons + [reason])

        # 地名マッチ（最重要）
        if place_names:
            for place in place_names:
                place_lower = place.lower()
                # 完全一致
                if place_lower in self._name_index:
                    for loc_id in self._name_index[place_lower]:
                        add_score(loc_id, 15.0, f"地名完全一致: {place}")
                # 部分一致
                for name, ids in self._name_index.items():
                    if place_lower in name or name in place_lower:
                        for loc_id in ids:
                            if loc_id not in [lid for lid in self._name_index.get(place_lower, [])]:
                                add_score(loc_id, 8.0, f"地名部分一致: {place}")

        # 施設種別マッチ
        if facility_types:
            type_mapping = {
                "温泉": LocationType.ONSEN,
                "道の駅": LocationType.MICHINOEKI,
                "キャンプ場": LocationType.CAMP,
                "rvパーク": LocationType.RV_PARK,
                "サービスエリア": LocationType.SA_PA,
                "sa": LocationType.SA_PA,
                "pa": LocationType.SA_PA,
                "神社": LocationType.SHRINE_TEMPLE,
                "寺": LocationType.SHRINE_TEMPLE,
                "公園": LocationType.PARK,
                "湖": LocationType.LAKE,
                "山": LocationType.MOUNTAIN,
                "海": LocationType.BEACH,
                "ビーチ": LocationType.BEACH,
            }

            for facility_type in facility_types:
                ft_lower = facility_type.lower()
                # タイプマッピング
                for keyword, loc_type in type_mapping.items():
                    if keyword in ft_lower or ft_lower in keyword:
                        for loc_id in self._type_index.get(loc_type, []):
                            add_score(loc_id, 10.0, f"施設種別: {facility_type}")
                # タグ検索
                for tag, ids in self._tag_index.items():
                    if ft_lower in tag or tag in ft_lower:
                        for loc_id in ids:
                            add_score(loc_id, 5.0, f"タグ: {facility_type}")

        # 設備マッチ
        if amenities:
            amenity_mapping = {
                "ev充電": "ev_charging",
                "充電": "ev_charging",
                "wifi": "wifi",
                "シャワー": "シャワー",
                "トイレ": "トイレ",
                "温泉": "温泉",
                "サウナ": "サウナ",
            }

            for amenity in amenities:
                am_lower = amenity.lower()
                # タグ検索
                for tag, ids in self._tag_index.items():
                    if am_lower in tag or tag in am_lower:
                        for loc_id in ids:
                            add_score(loc_id, 3.0, f"設備: {amenity}")
                # EV充電特別処理
                if "充電" in am_lower or "ev" in am_lower:
                    for loc_id, loc in self._locations.items():
                        if loc.ev_charging:
                            add_score(loc_id, 5.0, "EV充電設備あり")

        # 雰囲気マッチ
        if atmosphere:
            for atm in atmosphere:
                atm_lower = atm.lower()
                for loc_id, loc in self._locations.items():
                    # 静かさ
                    if "静か" in atm_lower and loc.noise_level == "low":
                        add_score(loc_id, 4.0, "静かな環境")
                    # 景色
                    if ("景色" in atm_lower or "眺め" in atm_lower) and loc.scenery_score >= 4.0:
                        add_score(loc_id, 3.0, "景観が良い")
                    # 自然
                    if "自然" in atm_lower and loc.type in [
                        LocationType.CAMP, LocationType.LAKE, LocationType.MOUNTAIN,
                        LocationType.SCENIC, LocationType.PARK
                    ]:
                        add_score(loc_id, 3.0, "自然豊か")

        # 都道府県フィルタ
        if prefecture:
            pref_ids = set(self._prefecture_index.get(prefecture, []))
            scores = {
                loc_id: data for loc_id, data in scores.items()
                if loc_id in pref_ids
            }

        # スコアでソートして返却
        sorted_results = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)

        results = []
        for loc_id, (score, reasons) in sorted_results[:limit]:
            loc = self._locations.get(loc_id)
            if loc:
                results.append(SearchResult(
                    location=loc,
                    score=score,
                    match_reasons=reasons,
                ))

        return results

    def get_all(self) -> list[Location]:
        """全件取得"""
        self._ensure_loaded()
        return list(self._locations.values())

    def _ensure_loaded(self) -> None:
        """ロード済みを保証"""
        if not self._loaded:
            self.load()

    @property
    def count(self) -> int:
        """登録件数"""
        self._ensure_loaded()
        return len(self._locations)


# シングルトンインスタンス
_cache_instance: Optional[LocationCache] = None


def get_location_cache() -> LocationCache:
    """キャッシュのシングルトンを取得"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LocationCache()
        _cache_instance.load()
    return _cache_instance
