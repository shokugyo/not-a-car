from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserRequest(BaseModel):
    """ユーザーの要望"""
    text: str = Field(..., description="ユーザーの自然言語リクエスト（例: 22時に静かな場所で寝たい）")
    desired_arrival: Optional[datetime] = Field(None, description="希望到着時刻")
    preferences: list[str] = Field(default_factory=list, description="ユーザーの好み（例: ['サウナ', '温泉', '静か']）")


class VehicleState(BaseModel):
    """車両の現在状態"""
    vehicle_id: int
    battery_level: float = Field(..., ge=0, le=100, description="バッテリー残量（%）")
    range_km: float = Field(..., ge=0, description="走行可能距離（km）")
    current_mode: str = Field(..., description="現在の運用モード")
    interior_mode: str = Field(..., description="内装モード")
    latitude: float
    longitude: float


class RouteFeatures(BaseModel):
    """ルート候補の特徴量"""
    id: str = Field(..., description="ルートID（例: A, B, C）")
    destination_name: str = Field(..., description="目的地名")
    eta: datetime = Field(..., description="到着予定時刻")
    distance_km: float = Field(..., ge=0, description="距離（km）")
    duration_minutes: int = Field(..., ge=0, description="所要時間（分）")
    toll_fee: int = Field(default=0, ge=0, description="高速料金（円）")
    charging_available: bool = Field(default=False, description="充電スポットの有無")
    noise_level: str = Field(default="medium", description="騒音レベル（low/medium/high）")
    scenery_score: float = Field(default=3.0, ge=1.0, le=5.0, description="景観スコア（1.0-5.0）")
    nearby_facilities: list[str] = Field(default_factory=list, description="周辺施設（例: ['温泉', 'コンビニ', 'トイレ']）")


class RoutingContext(BaseModel):
    """LLMへの入力コンテキスト"""
    user_request: UserRequest
    current_time: datetime
    vehicle_state: VehicleState
    route_candidates: list[RouteFeatures] = Field(..., min_length=1, max_length=10, description="ルート候補（3〜5件推奨）")


class RouteRecommendation(BaseModel):
    """LLMからの出力"""
    ranking: list[str] = Field(..., description="推奨順のルートIDリスト")
    recommended_id: str = Field(..., description="最推奨ルートID")
    explanation: str = Field(..., description="推奨理由（日本語）")
    confidence: float = Field(..., ge=0.0, le=1.0, description="確信度（0.0-1.0）")
    follow_up_question: Optional[str] = Field(None, description="追加質問（あれば）")
    reasoning_steps: list[str] = Field(default_factory=list, description="思考過程（デバッグ用）")


class ChatRequest(BaseModel):
    """汎用チャットリクエスト"""
    message: str = Field(..., description="ユーザーメッセージ")
    context: Optional[dict] = Field(None, description="追加コンテキスト情報")


class ChatResponse(BaseModel):
    """汎用チャットレスポンス"""
    message: str = Field(..., description="AIからのレスポンス")
    metadata: Optional[dict] = Field(None, description="追加メタデータ")
