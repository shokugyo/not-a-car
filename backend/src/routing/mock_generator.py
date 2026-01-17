import random
from datetime import datetime, timedelta
from typing import Optional

from src.llm.schemas import RouteFeatures
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
        },
        {
            "name": "RVパーク 河口湖",
            "lat": 35.50,
            "lng": 138.75,
            "noise_level": "low",
            "scenery_score": 5.0,
            "facilities": ["トイレ", "シャワー", "WiFi", "EV充電"],
            "charging": True,
        },
        {
            "name": "道の駅 箱根峠",
            "lat": 35.18,
            "lng": 139.02,
            "noise_level": "medium",
            "scenery_score": 4.0,
            "facilities": ["トイレ", "レストラン", "お土産"],
            "charging": False,
        },
        {
            "name": "SA 足柄",
            "lat": 35.28,
            "lng": 138.95,
            "noise_level": "high",
            "scenery_score": 3.0,
            "facilities": ["トイレ", "コンビニ", "ガソリンスタンド", "EV充電"],
            "charging": True,
        },
        {
            "name": "キャンプ場 朝霧高原",
            "lat": 35.38,
            "lng": 138.58,
            "noise_level": "low",
            "scenery_score": 4.8,
            "facilities": ["トイレ", "シャワー", "バーベキュー"],
            "charging": False,
        },
        {
            "name": "温泉施設 伊豆長岡",
            "lat": 35.03,
            "lng": 138.93,
            "noise_level": "low",
            "scenery_score": 4.2,
            "facilities": ["温泉", "サウナ", "レストラン", "駐車場"],
            "charging": False,
        },
        {
            "name": "道の駅 伊東マリンタウン",
            "lat": 34.96,
            "lng": 139.10,
            "noise_level": "medium",
            "scenery_score": 4.0,
            "facilities": ["トイレ", "温泉", "レストラン", "お土産"],
            "charging": True,
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
    ) -> list[RouteFeatures]:
        """
        モック候補を生成

        Args:
            origin: 出発地点
            count: 生成する候補数（3〜5推奨）
            current_time: 現在時刻
            preferences: ユーザーの好み（マッチする目的地を優先）

        Returns:
            ルート候補リスト
        """
        current_time = current_time or datetime.now()
        count = min(count, len(self.MOCK_DESTINATIONS))

        # 好みに基づいて目的地をソート
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
