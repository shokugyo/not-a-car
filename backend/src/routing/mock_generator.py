import random
from datetime import datetime, timedelta
from typing import Optional

from src.llm.schemas import RouteFeatures, DestinationExtraction
from .schemas import Coordinates


class MockRouteGenerator:
    """
    デモ用モックルート候補生成

    将来的にはOSRM/Valhalla/GraphHopperなどの
    ルーティングエンジンに置き換える
    """

    MOCK_DESTINATIONS = [
        {
            "name": "道の駅 富士川",
            "lat": 35.12,
            "lng": 138.45,
            "noise_level": "low",
            "scenery_score": 4.5,
            "facilities": ["トイレ", "コンビニ", "温泉", "EV充電"],
            "charging": True,
            # 検索マッチング用タグ
            "place_tags": ["富士", "静岡"],
            "facility_tags": ["道の駅", "温泉"],
            "amenity_tags": ["EV充電", "トイレ", "コンビニ"],
            "atmosphere_tags": ["静か", "景色が良い", "自然"],
        },
        {
            "name": "RVパーク 河口湖",
            "lat": 35.50,
            "lng": 138.75,
            "noise_level": "low",
            "scenery_score": 5.0,
            "facilities": ["トイレ", "シャワー", "WiFi", "EV充電"],
            "charging": True,
            "place_tags": ["河口湖", "山梨", "富士山"],
            "facility_tags": ["RVパーク", "キャンプ場"],
            "amenity_tags": ["EV充電", "WiFi", "シャワー", "トイレ"],
            "atmosphere_tags": ["静か", "景色が良い", "自然", "湖"],
        },
        {
            "name": "道の駅 箱根峠",
            "lat": 35.18,
            "lng": 139.02,
            "noise_level": "medium",
            "scenery_score": 4.0,
            "facilities": ["トイレ", "レストラン", "お土産"],
            "charging": False,
            "place_tags": ["箱根", "神奈川"],
            "facility_tags": ["道の駅"],
            "amenity_tags": ["トイレ", "レストラン"],
            "atmosphere_tags": ["景色が良い", "山"],
        },
        {
            "name": "SA 足柄",
            "lat": 35.28,
            "lng": 138.95,
            "noise_level": "high",
            "scenery_score": 3.0,
            "facilities": ["トイレ", "コンビニ", "ガソリンスタンド", "EV充電"],
            "charging": True,
            "place_tags": ["足柄", "静岡", "神奈川"],
            "facility_tags": ["サービスエリア", "SA"],
            "amenity_tags": ["EV充電", "トイレ", "コンビニ", "ガソリン"],
            "atmosphere_tags": [],
        },
        {
            "name": "キャンプ場 朝霧高原",
            "lat": 35.38,
            "lng": 138.58,
            "noise_level": "low",
            "scenery_score": 4.8,
            "facilities": ["トイレ", "シャワー", "バーベキュー"],
            "charging": False,
            "place_tags": ["朝霧高原", "静岡", "富士山"],
            "facility_tags": ["キャンプ場"],
            "amenity_tags": ["トイレ", "シャワー", "バーベキュー"],
            "atmosphere_tags": ["静か", "自然", "景色が良い", "星空"],
        },
        {
            "name": "温泉施設 伊豆長岡",
            "lat": 35.03,
            "lng": 138.93,
            "noise_level": "low",
            "scenery_score": 4.2,
            "facilities": ["温泉", "サウナ", "レストラン", "駐車場"],
            "charging": False,
            "place_tags": ["伊豆", "静岡"],
            "facility_tags": ["温泉", "温泉施設"],
            "amenity_tags": ["温泉", "サウナ", "レストラン", "駐車場"],
            "atmosphere_tags": ["静か", "リラックス"],
        },
        {
            "name": "道の駅 伊東マリンタウン",
            "lat": 34.96,
            "lng": 139.10,
            "noise_level": "medium",
            "scenery_score": 4.0,
            "facilities": ["トイレ", "温泉", "レストラン", "お土産"],
            "charging": True,
            "place_tags": ["伊東", "伊豆", "静岡"],
            "facility_tags": ["道の駅", "温泉"],
            "amenity_tags": ["EV充電", "温泉", "トイレ", "レストラン"],
            "atmosphere_tags": ["海", "景色が良い"],
        },
    ]

    ROUTE_IDS = ["A", "B", "C", "D", "E"]

    def __init__(self):
        pass

    def generate_candidates(
        self,
        origin: Coordinates,
        count: int = 4,
        current_time: Optional[datetime] = None,
        preferences: Optional[list[str]] = None,
        extraction: Optional[DestinationExtraction] = None,
    ) -> list[RouteFeatures]:
        """
        モック候補を生成

        Args:
            origin: 出発地点
            count: 生成する候補数（3〜5推奨）
            current_time: 現在時刻
            preferences: ユーザーの好み（マッチする目的地を優先）
            extraction: LLMで抽出した目的地情報

        Returns:
            ルート候補リスト
        """
        current_time = current_time or datetime.now()
        count = min(count, len(self.MOCK_DESTINATIONS))

        # 抽出結果に基づいてスコアリング
        if extraction:
            destinations = self._sort_by_extraction(
                self.MOCK_DESTINATIONS.copy(),
                extraction,
            )
        else:
            # 旧来の好みに基づくソート（後方互換性）
            destinations = self._sort_by_preferences(
                self.MOCK_DESTINATIONS.copy(),
                preferences or [],
            )

        # 上位count件を選択
        selected = destinations[:count]

        candidates = []
        for i, dest in enumerate(selected):
            route_id = self.ROUTE_IDS[i]
            candidates.append(self._create_route_feature(
                route_id=route_id,
                destination=dest,
                origin=origin,
                current_time=current_time,
            ))

        return candidates

    def _sort_by_extraction(
        self,
        destinations: list[dict],
        extraction: DestinationExtraction,
    ) -> list[dict]:
        """LLM抽出結果に基づいて目的地をスコア付けしてソート"""

        def match_score(items: list[str], tags: list[str]) -> int:
            """アイテムリストとタグのマッチスコアを計算"""
            score = 0
            for item in items:
                item_lower = item.lower()
                for tag in tags:
                    tag_lower = tag.lower()
                    # 完全一致
                    if item_lower == tag_lower:
                        score += 5
                    # 部分一致
                    elif item_lower in tag_lower or tag_lower in item_lower:
                        score += 3
            return score

        def score(dest: dict) -> float:
            total_score = 0

            # 地名マッチ（最重要）
            place_tags = dest.get("place_tags", [])
            total_score += match_score(extraction.place_names, place_tags) * 3

            # 施設種別マッチ
            facility_tags = dest.get("facility_tags", [])
            total_score += match_score(extraction.facility_types, facility_tags) * 2

            # 設備マッチ
            amenity_tags = dest.get("amenity_tags", [])
            total_score += match_score(extraction.amenities, amenity_tags) * 1.5

            # 雰囲気マッチ
            atmosphere_tags = dest.get("atmosphere_tags", [])
            total_score += match_score(extraction.atmosphere, atmosphere_tags) * 1.5

            # アクティビティに基づくボーナス
            for activity in extraction.activities:
                activity_lower = activity.lower()
                if "車中泊" in activity_lower and dest["noise_level"] == "low":
                    total_score += 5
                if "ドライブ" in activity_lower and dest["scenery_score"] >= 4.0:
                    total_score += 3
                if "リフレッシュ" in activity_lower or "リラックス" in activity_lower:
                    if dest["noise_level"] == "low":
                        total_score += 3

            # 景観スコアをベースラインとして追加
            total_score += dest["scenery_score"]

            return total_score

        # スコアでソート（高い順）+ ランダム性を少し追加
        random.shuffle(destinations)
        destinations.sort(key=score, reverse=True)
        return destinations

    def _sort_by_preferences(
        self,
        destinations: list[dict],
        preferences: list[str],
    ) -> list[dict]:
        """好みに基づいて目的地をスコア付けしてソート"""
        def score(dest: dict) -> float:
            match_score = 0
            for pref in preferences:
                pref_lower = pref.lower()
                # 施設名でマッチ
                for facility in dest["facilities"]:
                    if pref_lower in facility.lower():
                        match_score += 2

                # 静かさの好み
                if "静か" in pref and dest["noise_level"] == "low":
                    match_score += 3

                # 充電の好み
                if "充電" in pref and dest["charging"]:
                    match_score += 2

            return match_score + dest["scenery_score"]

        # スコアでソート（高い順）+ ランダム性を追加
        random.shuffle(destinations)
        destinations.sort(key=score, reverse=True)
        return destinations

    def _create_route_feature(
        self,
        route_id: str,
        destination: dict,
        origin: Coordinates,
        current_time: datetime,
    ) -> RouteFeatures:
        """RouteFeatures オブジェクトを生成"""
        # 距離を計算（簡易的な直線距離 × 係数）
        lat_diff = abs(destination["lat"] - origin.latitude)
        lng_diff = abs(destination["lng"] - origin.longitude)
        distance_km = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111 * 1.3

        # 所要時間（平均速度50km/hで計算）
        duration_minutes = int(distance_km / 50 * 60)

        # 到着予定時刻
        eta = current_time + timedelta(minutes=duration_minutes)

        # 高速料金（距離に応じて概算）
        toll_fee = int(distance_km * 25) if distance_km > 30 else 0

        return RouteFeatures(
            id=route_id,
            destination_name=destination["name"],
            eta=eta,
            distance_km=round(distance_km, 1),
            duration_minutes=duration_minutes,
            toll_fee=toll_fee,
            charging_available=destination["charging"],
            noise_level=destination["noise_level"],
            scenery_score=destination["scenery_score"],
            nearby_facilities=destination["facilities"],
        )
