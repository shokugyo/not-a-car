from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from src.database import get_db
from src.auth.service import AuthService
from src.vehicles.service import VehicleService
from src.earnings.service import EarningsService
from src.yield_engine.optimizer import YieldOptimizer
from src.websocket import manager


router = APIRouter()


async def get_owner_from_token(token: str, db: AsyncSession) -> Optional[int]:
    """Validate token and return owner_id"""
    try:
        auth_service = AuthService(db)
        payload = auth_service.decode_token(token)
        if payload.get("type") != "access":
            return None
        return int(payload.get("sub"))
    except Exception:
        return None


@router.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """
    Main WebSocket endpoint for realtime updates.

    Connect with token as query param: /ws/realtime?token=<access_token>

    Receives:
    - Vehicle status updates
    - Earnings updates
    - AI recommendations
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    # Get DB session
    async for db in get_db():
        owner_id = await get_owner_from_token(token, db)
        if not owner_id:
            await websocket.close(code=4002, reason="Invalid token")
            return

        await manager.connect(websocket, owner_id)

        try:
            # Send initial data
            vehicle_service = VehicleService(db)
            earnings_service = EarningsService(db)
            optimizer = YieldOptimizer()

            vehicles = await vehicle_service.get_vehicles_by_owner(owner_id)
            realtime_earnings = await earnings_service.get_realtime_earnings(owner_id)

            await websocket.send_json({
                "type": "initial",
                "data": {
                    "vehicles": [
                        {
                            "id": v.id,
                            "name": v.name,
                            "current_mode": v.current_mode.value,
                            "current_hourly_rate": v.current_hourly_rate,
                            "today_earnings": v.today_earnings,
                            "battery_level": v.battery_level,
                        }
                        for v in vehicles
                    ],
                    "earnings": [e.model_dump() for e in realtime_earnings],
                }
            })

            # Keep connection alive and handle messages
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=30.0
                    )

                    # Handle ping
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})

                    # Handle refresh request
                    elif data.get("type") == "refresh":
                        vehicles = await vehicle_service.get_vehicles_by_owner(owner_id)
                        realtime_earnings = await earnings_service.get_realtime_earnings(owner_id)

                        # Get predictions for each vehicle
                        predictions = {}
                        for v in vehicles:
                            pred = optimizer.optimize(v)
                            predictions[v.id] = {
                                "message_ja": pred.message_ja,
                                "potential_gain": pred.potential_gain,
                                "best_mode": pred.best_recommendation.mode.value if pred.best_recommendation else None,
                                "best_rate": pred.best_recommendation.predicted_hourly_rate if pred.best_recommendation else 0,
                            }

                        await websocket.send_json({
                            "type": "refresh",
                            "data": {
                                "earnings": [e.model_dump() for e in realtime_earnings],
                                "predictions": predictions,
                            }
                        })

                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_json({"type": "heartbeat"})

        except WebSocketDisconnect:
            manager.disconnect(websocket, owner_id)
        except Exception as e:
            manager.disconnect(websocket, owner_id)
            await websocket.close(code=1011, reason=str(e))
        break
