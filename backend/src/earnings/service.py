from datetime import datetime, timezone, timedelta
from typing import List, Optional
import random

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.vehicles.models import Vehicle, VehicleMode
from .models import Earning
from .schemas import EarningCreate, EarningsSummary, RealtimeEarning, ModeEarnings


class EarningsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_earning(self, owner_id: int, data: EarningCreate) -> Earning:
        platform_fee = data.amount * (settings.default_platform_fee_percent / 100)
        net_amount = data.amount - platform_fee

        earning = Earning(
            owner_id=owner_id,
            vehicle_id=data.vehicle_id,
            amount=data.amount,
            mode=data.mode,
            description=data.description,
            reference_id=data.reference_id,
            reference_type=data.reference_type,
            start_time=data.start_time,
            end_time=data.end_time,
            duration_minutes=data.duration_minutes,
            platform_fee=platform_fee,
            net_amount=net_amount,
        )
        self.db.add(earning)
        await self.db.commit()
        await self.db.refresh(earning)
        return earning

    async def get_earnings_by_owner(
        self,
        owner_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        vehicle_id: Optional[int] = None,
    ) -> List[Earning]:
        query = select(Earning).where(Earning.owner_id == owner_id)

        if start_date:
            query = query.where(Earning.created_at >= start_date)
        if end_date:
            query = query.where(Earning.created_at <= end_date)
        if vehicle_id:
            query = query.where(Earning.vehicle_id == vehicle_id)

        query = query.order_by(Earning.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_earnings_summary(
        self,
        owner_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> EarningsSummary:
        earnings = await self.get_earnings_by_owner(owner_id, start_date, end_date)

        total_earnings = sum(e.amount for e in earnings)
        total_net_earnings = sum(e.net_amount for e in earnings)
        total_platform_fees = sum(e.platform_fee for e in earnings)

        earnings_by_mode = {}
        for e in earnings:
            mode_key = e.mode.value
            earnings_by_mode[mode_key] = earnings_by_mode.get(mode_key, 0) + e.net_amount

        earnings_by_vehicle = {}
        for e in earnings:
            earnings_by_vehicle[e.vehicle_id] = (
                earnings_by_vehicle.get(e.vehicle_id, 0) + e.net_amount
            )

        return EarningsSummary(
            total_earnings=total_earnings,
            total_net_earnings=total_net_earnings,
            total_platform_fees=total_platform_fees,
            earnings_by_mode=earnings_by_mode,
            earnings_by_vehicle=earnings_by_vehicle,
            period_start=start_date,
            period_end=end_date,
        )

    async def get_realtime_earnings(self, owner_id: int) -> List[RealtimeEarning]:
        """Get realtime earnings status for all vehicles"""
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.owner_id == owner_id)
        )
        vehicles = result.scalars().all()

        realtime = []
        for vehicle in vehicles:
            # Calculate active time
            active_minutes = 0
            if vehicle.mode_started_at:
                delta = datetime.now(timezone.utc) - vehicle.mode_started_at.replace(tzinfo=timezone.utc)
                active_minutes = int(delta.total_seconds() / 60)

            # Determine status
            if vehicle.current_mode in [VehicleMode.MAINTENANCE, VehicleMode.CHARGING]:
                status = "maintenance"
            elif vehicle.current_mode == VehicleMode.IDLE:
                status = "idle"
            else:
                status = "earning"

            realtime.append(RealtimeEarning(
                vehicle_id=vehicle.id,
                vehicle_name=vehicle.name,
                current_mode=vehicle.current_mode,
                hourly_rate=vehicle.current_hourly_rate,
                today_total=vehicle.today_earnings,
                active_minutes=active_minutes,
                status=status,
            ))

        return realtime

    async def get_mode_earnings(self, owner_id: int) -> List[ModeEarnings]:
        """Get earnings breakdown by mode"""
        earnings = await self.get_earnings_by_owner(owner_id)

        mode_data = {}
        for e in earnings:
            mode_key = e.mode.value
            if mode_key not in mode_data:
                mode_data[mode_key] = {
                    "total": 0,
                    "hours": 0,
                    "count": 0,
                }
            mode_data[mode_key]["total"] += e.net_amount
            mode_data[mode_key]["hours"] += (e.duration_minutes or 0) / 60
            mode_data[mode_key]["count"] += 1

        result = []
        for mode_key, data in mode_data.items():
            avg_rate = data["total"] / data["hours"] if data["hours"] > 0 else 0
            result.append(ModeEarnings(
                mode=VehicleMode(mode_key),
                total_amount=data["total"],
                total_hours=data["hours"],
                average_hourly_rate=avg_rate,
                transaction_count=data["count"],
            ))

        return result

    async def simulate_earnings(self, owner_id: int) -> None:
        """
        Simulate earnings for demo purposes.
        In production, this would be triggered by actual bookings/tasks.
        """
        result = await self.db.execute(
            select(Vehicle).where(
                Vehicle.owner_id == owner_id,
                Vehicle.current_mode.notin_([VehicleMode.IDLE, VehicleMode.MAINTENANCE, VehicleMode.CHARGING])
            )
        )
        vehicles = result.scalars().all()

        for vehicle in vehicles:
            if vehicle.current_hourly_rate > 0:
                # Simulate 1 hour of earnings
                amount = vehicle.current_hourly_rate * random.uniform(0.8, 1.2)
                await self.create_earning(
                    owner_id=owner_id,
                    data=EarningCreate(
                        vehicle_id=vehicle.id,
                        amount=amount,
                        mode=vehicle.current_mode,
                        description=f"Auto-generated {vehicle.current_mode.value} earnings",
                        duration_minutes=60,
                        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
                        end_time=datetime.now(timezone.utc),
                    )
                )

                # Update vehicle's today earnings
                vehicle.today_earnings += amount * 0.85  # After platform fee
                await self.db.commit()
