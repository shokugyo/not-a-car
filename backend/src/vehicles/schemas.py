from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .models import VehicleMode, InteriorMode


class VehicleBase(BaseModel):
    name: Optional[str] = None
    license_plate: str
    model: Optional[str] = None
    year: Optional[int] = None
    vin: Optional[str] = None


class VehicleCreate(VehicleBase):
    allowed_modes: List[str] = ["accommodation", "delivery", "rideshare"]
    auto_mode_switch: bool = True


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    allowed_modes: Optional[List[str]] = None
    auto_mode_switch: Optional[bool] = None
    is_active: Optional[bool] = None


class VehicleResponse(VehicleBase):
    id: int
    owner_id: int
    current_mode: VehicleMode
    interior_mode: InteriorMode
    is_active: bool
    is_available: bool
    latitude: float
    longitude: float
    battery_level: float
    range_km: float
    allowed_modes: List[str]
    auto_mode_switch: bool
    current_hourly_rate: float
    today_earnings: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VehicleStatus(BaseModel):
    id: int
    name: Optional[str]
    current_mode: VehicleMode
    interior_mode: InteriorMode
    is_available: bool
    latitude: float
    longitude: float
    battery_level: float
    range_km: float
    current_hourly_rate: float
    today_earnings: float
    mode_started_at: Optional[datetime]
    active_duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class ModeChange(BaseModel):
    mode: VehicleMode
    force: bool = False  # Force change even if busy


class VehicleLocation(BaseModel):
    latitude: float
    longitude: float


class ScheduleCreate(BaseModel):
    day_of_week: int  # 0-6
    start_time: str   # "09:00"
    end_time: str     # "18:00"
    allowed_mode: VehicleMode
    priority: int = 0


class ScheduleResponse(ScheduleCreate):
    id: int
    vehicle_id: int
    is_active: bool

    class Config:
        from_attributes = True
