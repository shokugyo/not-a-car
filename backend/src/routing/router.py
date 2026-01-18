from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from src.database import get_db
from src.auth.dependencies import get_current_owner
from src.auth.models import Owner
from .schemas import (
    RoutingRequest,
    RouteSuggestionResponse,
    AvailableVehiclesRequest,
    AvailableVehiclesResponse,
)
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

    ユーザーの要望に基づき、最適なルートを提案します。

    - 自然言語でリクエスト（例: 「22時に静かな場所で寝たい」）
    - 希望到着時刻を指定可能
    - AI がルート候補を評価し、最適なルートを推奨

    リクエスト例:
    ```json
    {
        "query": "22時に静かな場所で寝たい"
    }
    ```

    レスポンス例:
    ```json
    {
        "routes": [
            {
                "id": "A",
                "name": "道の駅 富士川楽座",
                "description": "道の駅 富士川楽座への約45分のルート",
                "waypoints": [...],
                "totalDuration": 45,
                "totalDistance": 35.5,
                "estimatedCost": 1532,
                "highlights": ["静かな環境", "充電スポットあり"],
                "vehicleTypes": ["standard", "accommodation"]
            },
            ...
        ],
        "query": "22時に静かな場所で寝たい",
        "generatedAt": "2024-01-18T21:30:00"
    }
    ```
    """
    service = RoutingService(db)

    try:
        result = await service.suggest_route(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ルート提案に失敗しました: {str(e)}",
        )
    finally:
        await service.close()


@router.post("/suggest/stream")
async def suggest_route_stream(
    request: RoutingRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    ストリーミングでルート提案を取得（SSE）

    LLMの推論過程をリアルタイムで配信します。

    イベントタイプ:
    - step_start: ステップ開始
    - thinking: LLMの思考トークン
    - step_complete: ステップ完了
    - routes: ルート結果
    - done: 完了
    - error: エラー

    使用例（JavaScript）:
    ```javascript
    const response = await fetch('/api/v1/routing/suggest/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: '箱根で温泉' }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        // SSEイベントをパース
        const events = parseSSE(chunk);
        events.forEach(event => console.log(event));
    }
    ```
    """
    service = RoutingService(db)

    async def generate():
        try:
            async for event in service.suggest_route_stream(request):
                yield {
                    "event": event.event.value,
                    "data": event.model_dump_json(),
                }
        finally:
            await service.close()

    return EventSourceResponse(generate())


@router.post("/vehicles/available", response_model=AvailableVehiclesResponse)
async def get_available_vehicles(
    request: AvailableVehiclesRequest,
    owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    指定されたルートと出発時刻に利用可能な車両を取得

    利用者モードで車両を選択する際に使用します。
    利用可能な車両の条件:
    - is_active = True
    - is_available = True
    - battery_level >= 20%
    - current_mode in ['idle', 'rideshare']

    リクエスト例:
    ```json
    {
        "routeId": "A",
        "departureTime": "2026-01-18T10:00:00"
    }
    ```

    レスポンス例:
    ```json
    {
        "vehicles": [
            {
                "id": 1,
                "name": "Tesla Model Y",
                "model": "Model Y",
                "currentMode": "idle",
                "latitude": 35.6812,
                "longitude": 139.7671,
                "batteryLevel": 85.0,
                "rangeKm": 400.0,
                "hourlyRate": 1500.0,
                "estimatedPickupTime": 5,
                "features": ["標準シート", "基本収納", "長距離対応"]
            }
        ]
    }
    ```
    """
    service = RoutingService(db)

    try:
        vehicles = await service.get_available_vehicles(
            route_id=request.routeId,
            departure_time=request.departureTime,
            origin_lat=request.origin_latitude,
            origin_lng=request.origin_longitude,
        )
        return AvailableVehiclesResponse(vehicles=vehicles)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"利用可能車両の取得に失敗しました: {str(e)}",
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
