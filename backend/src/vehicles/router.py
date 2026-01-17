from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import get_current_owner
from src.auth.models import Owner
from .schemas import (
    VehicleCreate, VehicleUpdate, VehicleResponse, VehicleStatus,
    ModeChange, VehicleLocation, ScheduleCreate, ScheduleResponse
)
from .service import VehicleService


router = APIRouter()


@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get all vehicles owned by current user"""
    service = VehicleService(db)
    vehicles = await service.get_vehicles_by_owner(current_owner.id)
    return vehicles


@router.post("", response_model=VehicleResponse)
async def create_vehicle(
    data: VehicleCreate,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Register a new vehicle"""
    service = VehicleService(db)
    vehicle = await service.create_vehicle(current_owner.id, data)
    return vehicle


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get vehicle details"""
    service = VehicleService(db)
    vehicle = await service.get_vehicle_by_id(vehicle_id, current_owner.id)
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Update vehicle info"""
    service = VehicleService(db)
    vehicle = await service.update_vehicle(vehicle_id, current_owner.id, data)
    return vehicle


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Delete a vehicle"""
    service = VehicleService(db)
    await service.delete_vehicle(vehicle_id, current_owner.id)
    return {"message": "Vehicle deleted"}


@router.get("/{vehicle_id}/status", response_model=VehicleStatus)
async def get_vehicle_status(
    vehicle_id: int,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get real-time vehicle status"""
    service = VehicleService(db)
    vehicle = await service.get_vehicle_by_id(vehicle_id, current_owner.id)

    # Calculate active duration
    active_duration = None
    if vehicle.mode_started_at:
        delta = datetime.now(timezone.utc) - vehicle.mode_started_at.replace(tzinfo=timezone.utc)
        active_duration = int(delta.total_seconds() / 60)

    return VehicleStatus(
        id=vehicle.id,
        name=vehicle.name,
        current_mode=vehicle.current_mode,
        interior_mode=vehicle.interior_mode,
        is_available=vehicle.is_available,
        latitude=vehicle.latitude,
        longitude=vehicle.longitude,
        battery_level=vehicle.battery_level,
        range_km=vehicle.range_km,
        current_hourly_rate=vehicle.current_hourly_rate,
        today_earnings=vehicle.today_earnings,
        mode_started_at=vehicle.mode_started_at,
        active_duration_minutes=active_duration,
    )


@router.post("/{vehicle_id}/mode", response_model=VehicleResponse)
async def change_vehicle_mode(
    vehicle_id: int,
    mode_change: ModeChange,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Change vehicle operation mode"""
    service = VehicleService(db)
    vehicle = await service.change_mode(vehicle_id, current_owner.id, mode_change)
    return vehicle


@router.put("/{vehicle_id}/location", response_model=VehicleResponse)
async def update_vehicle_location(
    vehicle_id: int,
    location: VehicleLocation,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Update vehicle location"""
    service = VehicleService(db)
    vehicle = await service.update_location(
        vehicle_id, current_owner.id, location.latitude, location.longitude
    )
    return vehicle


@router.get("/{vehicle_id}/schedule", response_model=List[ScheduleResponse])
async def get_vehicle_schedule(
    vehicle_id: int,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get vehicle schedule"""
    service = VehicleService(db)
    schedules = await service.get_schedules(vehicle_id, current_owner.id)
    return schedules


@router.post("/{vehicle_id}/schedule", response_model=ScheduleResponse)
async def create_vehicle_schedule(
    vehicle_id: int,
    data: ScheduleCreate,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create vehicle schedule entry"""
    service = VehicleService(db)
    schedule = await service.create_schedule(vehicle_id, current_owner.id, data)
    return schedule
