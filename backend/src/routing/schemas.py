from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from src.llm.schemas import RouteRecommendation, RouteFeatures


class Coordinates(BaseModel):
    """座標"""
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="経度")


class RoutingRequest(BaseModel):
    """ルーティングリクエスト"""
    origin: Coordinates = Field(..., description="出発地点")
    user_request: str = Field(..., description="ユーザーの要望（自然言語）")
    desired_arrival: Optional[datetime] = Field(None, description="希望到着時刻")
    vehicle_id: int = Field(..., description="対象車両ID")
    preferences: list[str] = Field(default_factory=list, description="ユーザーの好み")


class RouteSuggestionResponse(BaseModel):
    """ルート提案レスポンス"""
    recommendation: RouteRecommendation = Field(..., description="AI推奨結果")
    candidates: list[RouteFeatures] = Field(..., description="評価されたルート候補")
    processing_time_ms: int = Field(..., description="処理時間（ミリ秒）")
