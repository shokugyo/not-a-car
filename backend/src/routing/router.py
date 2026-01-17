from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import get_current_owner
from src.auth.models import Owner
from .schemas import RoutingRequest, RouteSuggestionResponse
from .service import RoutingService

router = APIRouter()


@router.post("/suggest", response_model=RouteSuggestionResponse)
async def suggest_route(
    request: RoutingRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    ルート提案を取得

    ユーザーの要望と車両状態に基づき、最適なルートを提案します。

    - 自然言語でリクエスト（例: 「22時に静かな場所で寝たい」）
    - 希望到着時刻を指定可能
    - AI がルート候補を評価し、最適なルートを推奨
    """
    service = RoutingService(db)

    try:
        # 車両を取得
        vehicle = await service.get_vehicle(request.vehicle_id, owner.id)
        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail=f"車両ID {request.vehicle_id} が見つかりません",
            )

        # ルート提案を取得
        result = await service.suggest_route(request, vehicle)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ルート提案に失敗しました: {str(e)}",
        )
    finally:
        await service.close()


@router.get("/destinations")
async def list_destinations(
    owner: Owner = Depends(get_current_owner),
):
    """
    利用可能な目的地リストを取得

    モック実装のため、ハードコードされた目的地リストを返します。
    将来的にはデータベースや外部APIから取得します。
    """
    from .mock_generator import MockRouteGenerator

    generator = MockRouteGenerator()
    return {
        "destinations": [
            {
                "name": dest["name"],
                "coordinates": {"latitude": dest["lat"], "longitude": dest["lng"]},
                "facilities": dest["facilities"],
                "charging_available": dest["charging"],
            }
            for dest in generator.MOCK_DESTINATIONS
        ]
    }
