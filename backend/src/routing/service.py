import logging
import time
from datetime import datetime, timedelta
from typing import Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.service import LLMService
from src.llm.schemas import (
    UserRequest,
    VehicleState,
    RoutingContext,
    RouteFeatures,
    DestinationExtraction,
    WaypointType,
)
from src.geocoding import get_location_cache, LocationCache
from src.vehicles.models import Vehicle
from .schemas import (
    RoutingRequest,
    RouteSuggestionResponse,
    Route,
    RouteWaypoint,
    RouteDestination,
    DEFAULT_ORIGIN,
    Coordinates,
    LLMStepMetadata,
    ProcessingMetadata,
    StreamEvent,
    StreamEventType,
    TripVehicleResponse,
)
from .route_generator import CachedRouteGenerator
from .mock_generator import MockRouteGenerator

logger = logging.getLogger(__name__)


class RoutingService:
    """ルーティング統合サービス"""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None,
        location_cache: Optional[LocationCache] = None,
    ):
        self.db = db
        self.llm = llm_service or LLMService()
        self.location_cache = location_cache or get_location_cache()
        self.route_generator = CachedRouteGenerator(self.location_cache)
        # フォールバック用
        self.mock_generator = MockRouteGenerator()

    def _convert_route_features_to_route(
        self,
        features: RouteFeatures,
        ranking_position: int,
        extraction: Optional[DestinationExtraction] = None,
    ) -> Route:
        """RouteFeatures（内部形式）をRoute（フロントエンド形式）に変換"""
        waypoints_list: list[RouteWaypoint] = []

        # waypointsがある場合はextraction情報から複数waypointsを生成
        if extraction and extraction.waypoints:
            waypoints_list = self._create_waypoints_from_extraction(
                extraction=extraction,
                features=features,
            )
        else:
            # waypointsがない場合（抽象的クエリ）: featuresから単一waypointを生成
            waypoints_list = [self._create_waypoint_from_features(features, ranking_position)]

        highlights = []
        if features.charging_available:
            highlights.append("充電スポットあり")
        if features.noise_level == "low":
            highlights.append("静かな環境")
        if features.scenery_score >= 4.0:
            highlights.append("景観が良い")
        if features.nearby_facilities:
            # 「経由:」で始まる項目を先に追加
            for facility in features.nearby_facilities:
                if facility.startswith("経由:"):
                    highlights.insert(0, facility)
                elif len(highlights) < 5:  # ハイライトは5件まで
                    highlights.append(facility)

        estimated_cost = features.toll_fee + int(features.distance_km * 15)

        vehicle_types = ["standard"]
        if features.distance_km > 100:
            vehicle_types.append("long_range")
        if features.noise_level == "low":
            vehicle_types.append("accommodation")

        # ルート説明文を経由地情報付きで生成
        description = self._generate_route_description(features, extraction)

        return Route(
            id=features.id,
            name=features.destination_name,
            description=description,
            waypoints=waypoints_list,
            totalDuration=features.duration_minutes,
            totalDistance=features.distance_km,
            estimatedCost=estimated_cost,
            highlights=highlights,
            vehicleTypes=vehicle_types,
            polyline=features.polyline,
        )

    def _create_waypoint_from_features(
        self,
        features: RouteFeatures,
        ranking_position: int,
    ) -> RouteWaypoint:
        """featuresから単一waypointを作成（waypointsがない場合用）"""
        location = self.location_cache.get_by_name(features.destination_name)
        if location:
            lat = location.lat
            lng = location.lng
            address = location.address or f"{location.prefecture} {features.destination_name}"
            category = location.type.value
        else:
            lat = DEFAULT_ORIGIN.latitude + 0.1 * ranking_position
            lng = DEFAULT_ORIGIN.longitude + 0.1 * ranking_position
            address = f"{features.destination_name}周辺"
            category = "destination"

        destination = RouteDestination(
            id=f"dest_{features.id}",
            name=features.destination_name,
            address=address,
            latitude=lat,
            longitude=lng,
            category=category,
            estimatedDuration=features.duration_minutes,
        )

        return RouteWaypoint(
            destination=destination,
            arrivalTime=features.eta.isoformat(),
            departureTime=None,
            stayDuration=None,
        )

    def _create_waypoints_from_extraction(
        self,
        extraction: DestinationExtraction,
        features: RouteFeatures,
    ) -> list[RouteWaypoint]:
        """extractionから複数のwaypointsを生成"""
        waypoints_list: list[RouteWaypoint] = []
        sorted_waypoints = sorted(extraction.waypoints, key=lambda w: w.order)

        # nearby_facilitiesから展開された経由地名を抽出
        # （抽象経由地が具体名に展開された場合に使用）
        expanded_via_name = self._extract_via_name_from_facilities(features.nearby_facilities)

        # 累積時間を計算するための変数
        current_time = datetime.now()
        cumulative_minutes = 0

        for i, wp in enumerate(sorted_waypoints):
            # waypointの名前を決定
            waypoint_name = wp.name

            if wp.type == WaypointType.FINAL:
                # 最終目的地の場合: features.destination_nameを使用
                # （抽象的な目的地が具体名に展開されている場合に対応）
                waypoint_name = features.destination_name
            elif expanded_via_name:
                # 経由地で展開された名前がある場合はそちらを使用
                waypoint_name = expanded_via_name

            # キャッシュから座標を取得
            location = self.location_cache.get_by_name(waypoint_name)

            if location:
                lat = location.lat
                lng = location.lng
                address = location.address or f"{location.prefecture} {waypoint_name}"
                category = location.type.value
            else:
                # 見つからない場合はデフォルト値を使用
                lat = DEFAULT_ORIGIN.latitude + 0.05 * i
                lng = DEFAULT_ORIGIN.longitude + 0.05 * i
                address = f"{waypoint_name}周辺"
                category = "waypoint" if wp.type != WaypointType.FINAL else "destination"

            # 経由地までの所要時間を概算（均等分割）
            if wp.type == WaypointType.FINAL:
                segment_duration = features.duration_minutes - cumulative_minutes
            else:
                # 経由地の場合: 全体時間を均等分割
                segment_duration = features.duration_minutes // len(sorted_waypoints)
                cumulative_minutes += segment_duration

            arrival_time = current_time + timedelta(minutes=cumulative_minutes if wp.type != WaypointType.FINAL else features.duration_minutes)

            # 滞在時間のパース
            stay_duration = None
            if wp.duration_hint:
                stay_duration = self._parse_duration_hint(wp.duration_hint)

            destination = RouteDestination(
                id=f"dest_{features.id}_{i}",
                name=waypoint_name,
                address=address,
                latitude=lat,
                longitude=lng,
                category=category,
                estimatedDuration=segment_duration,
            )

            waypoint = RouteWaypoint(
                destination=destination,
                arrivalTime=arrival_time.isoformat(),
                departureTime=None,
                stayDuration=stay_duration,
            )

            waypoints_list.append(waypoint)

        return waypoints_list

    def _parse_duration_hint(self, hint: str) -> Optional[int]:
        """滞在時間のヒントを分に変換"""
        import re
        # 「30分程度」「1時間」などをパース
        if match := re.search(r'(\d+)\s*分', hint):
            return int(match.group(1))
        if match := re.search(r'(\d+)\s*時間', hint):
            return int(match.group(1)) * 60
        return None

    def _extract_via_name_from_facilities(
        self, nearby_facilities: list[str]
    ) -> Optional[str]:
        """
        nearby_facilitiesから経由地名を抽出

        「経由: 伊豆長岡温泉」のような形式から地名を取得する。
        抽象経由地が具体名に展開された場合に使用。

        Args:
            nearby_facilities: 周辺施設リスト

        Returns:
            抽出された経由地名（なければNone）
        """
        for facility in nearby_facilities:
            if facility.startswith("経由:"):
                # "経由: 伊豆長岡温泉" → "伊豆長岡温泉"
                via_name = facility.replace("経由:", "").strip()
                # カンマ区切りの場合は最初のものを使用
                if "," in via_name:
                    via_name = via_name.split(",")[0].strip()
                return via_name
        return None

    def _generate_route_description(
        self,
        features: RouteFeatures,
        extraction: Optional[DestinationExtraction],
    ) -> str:
        """経由地情報付きのルート説明文を生成"""
        if extraction and extraction.waypoints:
            waypoint_names = [
                w.name for w in extraction.waypoints
                if w.type != WaypointType.FINAL
            ]
            if waypoint_names:
                via_text = "→".join(waypoint_names)
                return f"{via_text}経由で{features.destination_name}への約{features.duration_minutes}分のルート"

        return f"{features.destination_name}への約{features.duration_minutes}分のルート"

    async def suggest_route(
        self,
        request: RoutingRequest,
    ) -> RouteSuggestionResponse:
        """
        ルート提案のメインフロー（車両なし版）

        1. LLMでクエリから目的地情報を抽出
        2. 抽出結果に基づいてモック候補を生成
        3. コンテキスト構築（デフォルト車両状態を使用）
        4. LLM評価・ランキング
        5. フロントエンド形式に変換

        Args:
            request: ルーティングリクエスト

        Returns:
            ルート提案結果（routes配列）
        """
        total_start_time = time.time()
        current_time = datetime.now()
        processing_steps: list[LLMStepMetadata] = []

        origin = request.origin or DEFAULT_ORIGIN

        # Step 1: LLMでクエリから目的地情報を抽出
        step1_start = time.time()
        extraction = await self.llm.extract_destination(request.query)
        step1_duration = int((time.time() - step1_start) * 1000)

        processing_steps.append(LLMStepMetadata(
            step_name="目的地抽出",
            model_name=self.llm.client.model_name_fast,
            duration_ms=step1_duration,
            provider=self.llm.client.provider.value,
        ))

        logger.info(f"Extracted destination info: places={extraction.place_names}, "
                    f"facilities={extraction.facility_types}, amenities={extraction.amenities}")

        # Step 2: キャッシュベースで候補を生成
        if self.location_cache.count > 0:
            candidates = self.route_generator.generate_candidates(
                origin=origin,
                extraction=extraction,
                count=4,
                current_time=current_time,
            )
            logger.info(f"Generated {len(candidates)} candidates from cache")
        else:
            # キャッシュが空の場合はフォールバック
            logger.warning("Location cache is empty, falling back to mock generator")
            candidates = self.mock_generator.generate_candidates(
                origin=origin,
                count=4,
                current_time=current_time,
                preferences=request.preferences,
                extraction=extraction,
            )

        default_vehicle_state = VehicleState(
            vehicle_id=0,
            battery_level=80.0,
            range_km=300.0,
            current_mode="idle",
            interior_mode="standard",
            latitude=origin.latitude,
            longitude=origin.longitude,
        )

        context = RoutingContext(
            user_request=UserRequest(
                text=request.query,
                desired_arrival=request.desired_arrival,
                preferences=request.preferences,
            ),
            current_time=current_time,
            vehicle_state=default_vehicle_state,
            route_candidates=candidates,
        )

        # Step 3: LLMでルート評価
        step2_start = time.time()
        recommendation = await self.llm.evaluate_routes(context)
        step2_duration = int((time.time() - step2_start) * 1000)

        processing_steps.append(LLMStepMetadata(
            step_name="ルート評価",
            model_name=self.llm.client.model_name,
            duration_ms=step2_duration,
            provider=self.llm.client.provider.value,
        ))

        # 経由地情報をログに出力
        if extraction.waypoints:
            logger.info(f"Route with waypoints: {[w.name for w in extraction.waypoints]}")

        routes = []
        for i, route_id in enumerate(recommendation.ranking):
            candidate = next((c for c in candidates if c.id == route_id), None)
            if candidate:
                routes.append(self._convert_route_features_to_route(candidate, i, extraction))

        for candidate in candidates:
            if candidate.id not in recommendation.ranking:
                routes.append(
                    self._convert_route_features_to_route(candidate, len(routes), extraction)
                )

        # 処理メタデータを構築
        total_duration_ms = int((time.time() - total_start_time) * 1000)
        processing_metadata = ProcessingMetadata(
            total_duration_ms=total_duration_ms,
            steps=processing_steps,
            reasoning_steps=recommendation.reasoning_steps,
        )

        return RouteSuggestionResponse(
            routes=routes,
            query=request.query,
            generatedAt=current_time.isoformat(),
            processing=processing_metadata,
        )

    async def suggest_route_stream(
        self,
        request: RoutingRequest,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        ストリーミングでルート提案

        SSE経由でリアルタイムにLLM推論過程を配信

        Args:
            request: ルーティングリクエスト

        Yields:
            StreamEvent - ストリーミングイベント
        """
        current_time = datetime.now()
        origin = request.origin or DEFAULT_ORIGIN

        try:
            # Step 1: 目的地抽出開始
            yield StreamEvent(
                event=StreamEventType.STEP_START,
                step_name="目的地抽出",
                step_index=0,
            )

            # ストリーミングで目的地抽出
            extraction: Optional[DestinationExtraction] = None
            async for token, result in self.llm.extract_destination_stream(request.query):
                if token:
                    yield StreamEvent(
                        event=StreamEventType.THINKING,
                        step_index=0,
                        content=token,
                    )
                if result:
                    extraction = result

            yield StreamEvent(
                event=StreamEventType.STEP_COMPLETE,
                step_index=0,
            )

            # extractionがNoneの場合はデフォルト
            if extraction is None:
                from src.llm.schemas import DestinationExtraction
                extraction = DestinationExtraction(
                    waypoints=[],
                    facility_types=[],
                    amenities=[],
                    atmosphere=[],
                    activities=[],
                    time_constraints=None,
                    distance_preference=None,
                    original_query=request.query,
                )


            # Step 2: ルート候補生成
            yield StreamEvent(
                event=StreamEventType.STEP_START,
                step_name="ルート候補生成",
                step_index=1,
            )

            if self.location_cache.count > 0:
                candidates = self.route_generator.generate_candidates(
                    origin=origin,
                    extraction=extraction,
                    count=4,
                    current_time=current_time,
                )
            else:
                candidates = self.mock_generator.generate_candidates(
                    origin=origin,
                    count=4,
                    current_time=current_time,
                    preferences=request.preferences,
                    extraction=extraction,
                )

            yield StreamEvent(
                event=StreamEventType.STEP_COMPLETE,
                step_index=1,
                content=f"{len(candidates)}件の候補を生成",
            )

            # Step 3: ルート評価開始
            yield StreamEvent(
                event=StreamEventType.STEP_START,
                step_name="ルート評価",
                step_index=2,
            )

            default_vehicle_state = VehicleState(
                vehicle_id=0,
                battery_level=80.0,
                range_km=300.0,
                current_mode="idle",
                interior_mode="standard",
                latitude=origin.latitude,
                longitude=origin.longitude,
            )

            context = RoutingContext(
                user_request=UserRequest(
                    text=request.query,
                    desired_arrival=request.desired_arrival,
                    preferences=request.preferences,
                ),
                current_time=current_time,
                vehicle_state=default_vehicle_state,
                route_candidates=candidates,
            )

            # ストリーミングでルート評価
            recommendation = None
            async for token, result in self.llm.evaluate_routes_stream(context):
                if token:
                    yield StreamEvent(
                        event=StreamEventType.THINKING,
                        step_index=2,
                        content=token,
                    )
                if result:
                    recommendation = result

            yield StreamEvent(
                event=StreamEventType.STEP_COMPLETE,
                step_index=2,
            )

            # ルートを変換
            routes = []
            if recommendation:
                for i, route_id in enumerate(recommendation.ranking):
                    candidate = next((c for c in candidates if c.id == route_id), None)
                    if candidate:
                        routes.append(self._convert_route_features_to_route(candidate, i, extraction))

            for candidate in candidates:
                if not recommendation or candidate.id not in recommendation.ranking:
                    routes.append(
                        self._convert_route_features_to_route(candidate, len(routes), extraction)
                    )

            # ルート結果を送信
            yield StreamEvent(
                event=StreamEventType.ROUTES,
                data={
                    "routes": [r.model_dump() for r in routes],
                    "query": request.query,
                    "generatedAt": current_time.isoformat(),
                },
            )

            # 完了
            yield StreamEvent(event=StreamEventType.DONE)

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield StreamEvent(
                event=StreamEventType.ERROR,
                content=str(e),
            )

    async def get_vehicle(self, vehicle_id: int, owner_id: int) -> Optional[Vehicle]:
        """車両を取得"""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Vehicle).where(
                Vehicle.id == vehicle_id,
                Vehicle.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_available_vehicles(
        self,
        route_id: str,
        departure_time: str,
        origin_lat: float,
        origin_lng: float,
    ) -> list[TripVehicleResponse]:
        """
        利用可能な車両を取得

        条件:
        - is_active = True
        - is_available = True
        - battery_level >= 20%
        - current_mode in ['idle', 'rideshare']（すぐ利用可能なモード）

        Args:
            route_id: ルートID（将来的な拡張用）
            departure_time: 出発希望時刻
            origin_lat: 出発地点の緯度
            origin_lng: 出発地点の経度

        Returns:
            利用可能車両リスト（ピックアップ時間順）
        """
        from sqlalchemy import select
        from src.vehicles.models import VehicleMode, InteriorMode
        import math

        # 利用可能モードのマッピング
        INTERIOR_MODE_FEATURES = {
            InteriorMode.STANDARD: ["標準シート", "基本収納"],
            InteriorMode.BED: ["睡眠モード", "自動運転快適機能"],
            InteriorMode.CARGO: ["大型荷室", "温度管理"],
            InteriorMode.PASSENGER: ["乗客向け快適機能", "エンターテイメント"],
            InteriorMode.OFFICE: ["デスク", "WiFi完備"],
        }

        def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """2点間の距離をkm単位で計算（Haversine公式）"""
            R = 6371  # 地球の半径（km）
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)

            a = math.sin(delta_lat / 2) ** 2 + \
                math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            return R * c

        def calculate_pickup_time(distance_km: float) -> int:
            """ピックアップ時間を分単位で計算（平均速度30km/h）"""
            avg_speed_kmh = 30
            hours = distance_km / avg_speed_kmh
            return max(1, int(hours * 60))

        # 利用可能車両を取得（利用者モードでは全オーナーの車両を検索）
        query = select(Vehicle).where(
            Vehicle.is_active == True,
            Vehicle.is_available == True,
            Vehicle.battery_level >= 20.0,
            Vehicle.current_mode.in_([VehicleMode.IDLE, VehicleMode.RIDESHARE]),
        )

        result = await self.db.execute(query)
        vehicles = result.scalars().all()

        # レスポンスを構築
        trip_vehicles: list[TripVehicleResponse] = []
        for vehicle in vehicles:
            distance = haversine_distance(
                vehicle.latitude or 35.6762,
                vehicle.longitude or 139.6503,
                origin_lat,
                origin_lng,
            )
            pickup_time = calculate_pickup_time(distance)

            features = INTERIOR_MODE_FEATURES.get(
                vehicle.interior_mode,
                ["標準シート", "基本収納"],
            )

            # バッテリー残量が多い場合は追加機能
            if vehicle.battery_level >= 80:
                features = features + ["長距離対応"]
            if vehicle.range_km >= 300:
                features = features + ["航続距離: 300km+"]

            trip_vehicles.append(TripVehicleResponse(
                id=vehicle.id,
                name=vehicle.name,
                model=vehicle.model,
                currentMode=vehicle.current_mode.value if vehicle.current_mode else "idle",
                latitude=vehicle.latitude or 35.6762,
                longitude=vehicle.longitude or 139.6503,
                batteryLevel=vehicle.battery_level or 0.0,
                rangeKm=vehicle.range_km or 0.0,
                hourlyRate=vehicle.current_hourly_rate or 1500.0,  # デフォルト1500円/h
                estimatedPickupTime=pickup_time,
                features=features,
            ))

        # ピックアップ時間順にソート
        trip_vehicles.sort(key=lambda v: v.estimatedPickupTime)

        return trip_vehicles

    async def close(self):
        """サービスを閉じる"""
        await self.llm.close()
