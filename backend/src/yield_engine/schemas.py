from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from src.vehicles.models import VehicleMode


class MarketCondition(BaseModel):
    timestamp: datetime
    latitude: float
    longitude: float

    # Accommodation market
    accommodation_demand: float  # 0-1
    accommodation_avg_price: float
    nearby_hotels_occupancy: float

    # Delivery market
    delivery_demand: float
    delivery_avg_price: float
    pending_delivery_jobs: int

    # Rideshare market
    rideshare_demand: float
    rideshare_surge_multiplier: float
    rideshare_avg_price: float


class ModePrediction(BaseModel):
    mode: VehicleMode
    predicted_hourly_rate: float
    utilization: float  # 0-1
    total_revenue: float  # For time horizon
    confidence: float  # 0-1
    reasoning: str


class ModeRecommendation(BaseModel):
    mode: VehicleMode
    predicted_hourly_rate: float
    confidence: float
    reasoning: str
    transition_cost: float
    net_benefit: float
    is_recommended: bool = False


class YieldPrediction(BaseModel):
    vehicle_id: int
    current_mode: VehicleMode
    current_hourly_rate: float
    recommendations: List[ModeRecommendation]
    best_recommendation: Optional[ModeRecommendation] = None
    potential_gain: float  # Difference from current
    message: str  # User-friendly message
    message_ja: str  # Japanese message


class ModeComparison(BaseModel):
    vehicle_id: int
    time_horizon_hours: int
    modes: List[ModePrediction]
    current_mode: VehicleMode
    optimal_mode: VehicleMode
    potential_revenue_increase: float
