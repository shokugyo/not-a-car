from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict
from src.vehicles.models import VehicleMode


class EarningBase(BaseModel):
    vehicle_id: int
    amount: float
    mode: VehicleMode
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None


class EarningCreate(EarningBase):
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class EarningResponse(EarningBase):
    id: int
    owner_id: int
    currency: str
    platform_fee: float
    net_amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class EarningsSummary(BaseModel):
    total_earnings: float
    total_net_earnings: float
    total_platform_fees: float
    earnings_by_mode: Dict[str, float]
    earnings_by_vehicle: Dict[int, float]
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class RealtimeEarning(BaseModel):
    vehicle_id: int
    vehicle_name: Optional[str]
    current_mode: VehicleMode
    hourly_rate: float
    today_total: float
    active_minutes: int
    status: str  # "earning", "idle", "maintenance"

    @property
    def active_time_display(self) -> str:
        hours = self.active_minutes // 60
        mins = self.active_minutes % 60
        if hours > 0:
            return f"{hours}{mins}"
        return f"{mins}"


class ModeEarnings(BaseModel):
    mode: VehicleMode
    total_amount: float
    total_hours: float
    average_hourly_rate: float
    transaction_count: int


class DailyEarnings(BaseModel):
    date: date
    total_amount: float
    by_mode: Dict[str, float]
