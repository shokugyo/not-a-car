import time
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.service import LLMService
from src.llm.schemas import (
    UserRequest,
    VehicleState,
    RoutingContext,
    RouteRecommendation,
)
from src.vehicles.models import Vehicle
from .schemas import RoutingRequest, RouteSuggestionResponse
from .mock_generator import MockRouteGenerator


class RoutingService:
    """ルーティング統合サービス"""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None,
    ):
        self.db = db
        self.llm = llm_service or LLMService()
        self.mock_generator = MockRouteGenerator()

    async def suggest_route(
        self,
        request: RoutingRequest,
        vehicle: Vehicle,
    ) -> RouteSuggestionResponse:
        """
        ルート提案のメインフロー

        1. モック候補生成（将来: OSRM呼び出し）
        2. コンテキスト構築
        3. LLM評価

        Args:
            request: ルーティングリクエスト
            vehicle: 対象車両

        Returns:
            ルート提案結果（推奨 + 候補リスト）
        """
        start_time = time.time()
        current_time = datetime.now()

        # 1. モック候補生成（将来: OSRM/Valhalla/GraphHopper呼び出し）
        candidates = self.mock_generator.generate_candidates(
            origin=request.origin,
            count=4,
            current_time=current_time,
            preferences=request.preferences,
        )

        # 2. コンテキスト構築
        context = RoutingContext(
            user_request=UserRequest(
                text=request.user_request,
                desired_arrival=request.desired_arrival,
                preferences=request.preferences,
            ),
            current_time=current_time,
            vehicle_state=VehicleState(
                vehicle_id=vehicle.id,
                battery_level=vehicle.battery_level,
                range_km=vehicle.range_km,
                current_mode=vehicle.current_mode.value,
                interior_mode=vehicle.interior_mode.value,
                latitude=vehicle.latitude,
                longitude=vehicle.longitude,
            ),
            route_candidates=candidates,
        )

        # 3. LLM評価
        recommendation = await self.llm.evaluate_routes(context)

        # 処理時間計算
        processing_time_ms = int((time.time() - start_time) * 1000)

        return RouteSuggestionResponse(
            recommendation=recommendation,
            candidates=candidates,
            processing_time_ms=processing_time_ms,
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

    async def close(self):
        """サービスを閉じる"""
        await self.llm.close()
