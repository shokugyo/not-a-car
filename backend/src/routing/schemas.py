from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

from src.llm.schemas import RouteRecommendation, RouteFeatures


class Coordinates(BaseModel):
    """座標"""
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="経度")


# デフォルト出発地点（東京駅）
DEFAULT_ORIGIN = Coordinates(latitude=35.6812, longitude=139.7671)


class RoutingRequest(BaseModel):
    """ルーティングリクエスト（フロントエンド互換）"""
    query: str = Field(..., description="ユーザーの要望（自然言語）")
    origin: Optional[Coordinates] = Field(None, description="出発地点（省略時は東京駅）")
    desired_arrival: Optional[datetime] = Field(None, description="希望到着時刻")
    preferences: list[str] = Field(default_factory=list, description="ユーザーの好み")


class RouteDestination(BaseModel):
    """ルートの目的地情報"""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    category: Optional[str] = None
    estimatedDuration: Optional[int] = None  # minutes


class RouteWaypoint(BaseModel):
    """ルートの経由地点"""
    destination: RouteDestination
    arrivalTime: Optional[str] = None
    departureTime: Optional[str] = None
    stayDuration: Optional[int] = None  # minutes


class Route(BaseModel):
    """フロントエンド互換のルート形式"""
    id: str
    name: str
    description: str
    waypoints: list[RouteWaypoint]
    totalDuration: int  # minutes
    totalDistance: float  # km
    estimatedCost: int  # yen
    highlights: list[str]
    vehicleTypes: list[str]
    polyline: Optional[str] = None  # Encoded polyline for map display


class LLMStepMetadata(BaseModel):
    """LLM処理ステップのメタデータ"""
    step_name: str = Field(..., description="ステップ名")
    model_name: str = Field(..., description="使用したモデル名")
    duration_ms: int = Field(..., ge=0, description="処理時間（ミリ秒）")
    provider: str = Field(..., description="プロバイダー (local, cloud, mock)")


class ProcessingMetadata(BaseModel):
    """処理全体のメタデータ"""
    total_duration_ms: int = Field(..., ge=0, description="総処理時間（ミリ秒）")
    steps: list[LLMStepMetadata] = Field(default_factory=list, description="各ステップのメタデータ")
    reasoning_steps: list[str] = Field(default_factory=list, description="LLMの思考過程")


class RouteSuggestionResponse(BaseModel):
    """ルート提案レスポンス（フロントエンド互換）"""
    routes: list[Route]
    query: str
    generatedAt: str  # ISO format
    processing: Optional[ProcessingMetadata] = Field(None, description="処理メタデータ")


# 内部用のレガシー型（mock_generator等で使用）
class LegacyRoutingRequest(BaseModel):
    """レガシーリクエスト形式（内部使用）"""
    origin: Coordinates = Field(..., description="出発地点")
    user_request: str = Field(..., description="ユーザーの要望（自然言語）")
    desired_arrival: Optional[datetime] = Field(None, description="希望到着時刻")
    vehicle_id: int = Field(..., description="対象車両ID")
    preferences: list[str] = Field(default_factory=list, description="ユーザーの好み")


# ストリーミング関連の型定義
class StreamEventType(str, Enum):
    """ストリーミングイベントの種類"""
    STEP_START = "step_start"       # ステップ開始
    THINKING = "thinking"           # 思考トークン
    TOKEN = "token"                 # 出力トークン
    STEP_COMPLETE = "step_complete" # ステップ完了
    ROUTES = "routes"               # ルート結果
    DONE = "done"                   # 完了
    ERROR = "error"                 # エラー


class StreamEvent(BaseModel):
    """ストリーミングイベント"""
    event: StreamEventType = Field(..., description="イベント種別")
    step_name: Optional[str] = Field(None, description="ステップ名")
    step_index: Optional[int] = Field(None, description="ステップインデックス")
    content: Optional[str] = Field(None, description="コンテンツ（トークンなど）")
    data: Optional[dict] = Field(None, description="データペイロード")


# 利用可能車両取得用スキーマ
class AvailableVehiclesRequest(BaseModel):
    """利用可能車両リクエスト"""
    routeId: str = Field(..., description="ルートID")
    departureTime: str = Field(..., description="出発希望時刻（ISO形式）")
    origin_latitude: float = Field(35.6812, description="出発地点の緯度（デフォルト: 東京駅）")
    origin_longitude: float = Field(139.7671, description="出発地点の経度（デフォルト: 東京駅）")


class TripVehicleResponse(BaseModel):
    """トリップ用車両情報"""
    id: int = Field(..., description="車両ID")
    name: Optional[str] = Field(None, description="車両名")
    model: Optional[str] = Field(None, description="車両モデル")
    currentMode: str = Field(..., description="現在のモード")
    latitude: float = Field(..., description="現在地の緯度")
    longitude: float = Field(..., description="現在地の経度")
    batteryLevel: float = Field(..., description="バッテリー残量（%）")
    rangeKm: float = Field(..., description="航続距離（km）")
    hourlyRate: float = Field(..., description="時間あたり料金")
    estimatedPickupTime: int = Field(..., description="ピックアップ予想時間（分）")
    features: list[str] = Field(default_factory=list, description="車両機能リスト")


class AvailableVehiclesResponse(BaseModel):
    """利用可能車両レスポンス"""
    vehicles: list[TripVehicleResponse] = Field(default_factory=list, description="利用可能車両リスト")
