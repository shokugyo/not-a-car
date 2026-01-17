from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.exceptions import NotFoundException, ForbiddenException, NotACarException
from .models import Vehicle, VehicleMode, InteriorMode, VehicleSchedule
from .schemas import VehicleCreate, VehicleUpdate, ModeChange, ScheduleCreate


# Mode to interior mapping
MODE_INTERIOR_MAP = {
    VehicleMode.ACCOMMODATION: InteriorMode.BED,
    VehicleMode.DELIVERY: InteriorMode.CARGO,
    VehicleMode.RIDESHARE: InteriorMode.PASSENGER,
    VehicleMode.IDLE: InteriorMode.STANDARD,
    VehicleMode.MAINTENANCE: InteriorMode.STANDARD,
    VehicleMode.CHARGING: InteriorMode.STANDARD,
    VehicleMode.TRANSIT: InteriorMode.STANDARD,
}


class VehicleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vehicles_by_owner(self, owner_id: int) -> List[Vehicle]:
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def get_vehicle_by_id(self, vehicle_id: int, owner_id: int) -> Vehicle:
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.id == vehicle_id)
        )
        vehicle = result.scalar_one_or_none()

        if not vehicle:
            raise NotFoundException(f"Vehicle {vehicle_id} not found")

        if vehicle.owner_id != owner_id:
            raise ForbiddenException("You don't own this vehicle")

        return vehicle

    async def create_vehicle(self, owner_id: int, data: VehicleCreate) -> Vehicle:
        # Check if license plate already exists
        existing = await self.db.execute(
            select(Vehicle).where(Vehicle.license_plate == data.license_plate)
        )
        if existing.scalar_one_or_none():
            raise NotACarException("License plate already registered")

        vehicle = Vehicle(
            owner_id=owner_id,
            name=data.name,
            license_plate=data.license_plate,
            model=data.model,
            year=data.year,
            vin=data.vin,
            allowed_modes=data.allowed_modes,
            auto_mode_switch=data.auto_mode_switch,
        )
        self.db.add(vehicle)
        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle

    async def update_vehicle(
        self, vehicle_id: int, owner_id: int, data: VehicleUpdate
    ) -> Vehicle:
        vehicle = await self.get_vehicle_by_id(vehicle_id, owner_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(vehicle, key, value)

        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle

    async def delete_vehicle(self, vehicle_id: int, owner_id: int) -> None:
        vehicle = await self.get_vehicle_by_id(vehicle_id, owner_id)
        await self.db.delete(vehicle)
        await self.db.commit()

    async def change_mode(
        self, vehicle_id: int, owner_id: int, mode_change: ModeChange
    ) -> Vehicle:
        vehicle = await self.get_vehicle_by_id(vehicle_id, owner_id)

        # Check if mode is allowed
        if mode_change.mode.value not in vehicle.allowed_modes and mode_change.mode not in [
            VehicleMode.IDLE, VehicleMode.MAINTENANCE, VehicleMode.CHARGING
        ]:
            raise NotACarException(f"Mode {mode_change.mode.value} is not allowed for this vehicle")

        # Check if vehicle is available (unless forcing)
        if not vehicle.is_available and not mode_change.force:
            raise NotACarException("Vehicle is currently busy. Use force=true to override")

        # Update mode and interior
        vehicle.current_mode = mode_change.mode
        vehicle.interior_mode = MODE_INTERIOR_MAP.get(mode_change.mode, InteriorMode.STANDARD)
        vehicle.mode_started_at = datetime.now(timezone.utc)

        # Set hourly rate based on mode (mock data for MVP)
        hourly_rates = {
            VehicleMode.ACCOMMODATION: 5000,
            VehicleMode.DELIVERY: 2000,
            VehicleMode.RIDESHARE: 3000,
            VehicleMode.IDLE: 0,
            VehicleMode.MAINTENANCE: 0,
            VehicleMode.CHARGING: 0,
            VehicleMode.TRANSIT: 0,
        }
        vehicle.current_hourly_rate = hourly_rates.get(mode_change.mode, 0)

        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle

    async def update_location(
        self, vehicle_id: int, owner_id: int, latitude: float, longitude: float
    ) -> Vehicle:
        vehicle = await self.get_vehicle_by_id(vehicle_id, owner_id)
        vehicle.latitude = latitude
        vehicle.longitude = longitude
        vehicle.last_location_update = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle

    async def get_schedules(self, vehicle_id: int, owner_id: int) -> List[VehicleSchedule]:
        vehicle = await self.get_vehicle_by_id(vehicle_id, owner_id)
        result = await self.db.execute(
            select(VehicleSchedule).where(VehicleSchedule.vehicle_id == vehicle.id)
        )
        return list(result.scalars().all())

    async def create_schedule(
        self, vehicle_id: int, owner_id: int, data: ScheduleCreate
    ) -> VehicleSchedule:
        vehicle = await self.get_vehicle_by_id(vehicle_id, owner_id)

        schedule = VehicleSchedule(
            vehicle_id=vehicle.id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            allowed_mode=data.allowed_mode,
            priority=data.priority,
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule
