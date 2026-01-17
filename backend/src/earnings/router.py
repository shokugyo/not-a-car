from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import get_current_owner
from src.auth.models import Owner
from .schemas import EarningResponse, EarningsSummary, RealtimeEarning, ModeEarnings
from .service import EarningsService


router = APIRouter()


@router.get("", response_model=EarningsSummary)
async def get_earnings_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get earnings summary for current owner"""
    service = EarningsService(db)

    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    summary = await service.get_earnings_summary(
        current_owner.id, start_date, end_date
    )
    return summary


@router.get("/realtime", response_model=List[RealtimeEarning])
async def get_realtime_earnings(
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Get realtime earnings status for all vehicles.
    Shows current hourly rate and status for each vehicle.
    """
    service = EarningsService(db)
    realtime = await service.get_realtime_earnings(current_owner.id)
    return realtime


@router.get("/history", response_model=List[EarningResponse])
async def get_earnings_history(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get earnings history with optional filters"""
    service = EarningsService(db)
    earnings = await service.get_earnings_by_owner(
        current_owner.id, start_date, end_date, vehicle_id
    )
    return earnings[:limit]


@router.get("/by-mode", response_model=List[ModeEarnings])
async def get_earnings_by_mode(
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get earnings breakdown by operation mode"""
    service = EarningsService(db)
    mode_earnings = await service.get_mode_earnings(current_owner.id)
    return mode_earnings


@router.get("/by-vehicle/{vehicle_id}", response_model=EarningsSummary)
async def get_earnings_by_vehicle(
    vehicle_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get earnings summary for a specific vehicle"""
    service = EarningsService(db)

    # Get earnings filtered by vehicle
    earnings = await service.get_earnings_by_owner(
        current_owner.id, start_date, end_date, vehicle_id
    )

    total_earnings = sum(e.amount for e in earnings)
    total_net_earnings = sum(e.net_amount for e in earnings)
    total_platform_fees = sum(e.platform_fee for e in earnings)

    earnings_by_mode = {}
    for e in earnings:
        mode_key = e.mode.value
        earnings_by_mode[mode_key] = earnings_by_mode.get(mode_key, 0) + e.net_amount

    return EarningsSummary(
        total_earnings=total_earnings,
        total_net_earnings=total_net_earnings,
        total_platform_fees=total_platform_fees,
        earnings_by_mode=earnings_by_mode,
        earnings_by_vehicle={vehicle_id: total_net_earnings},
        period_start=start_date,
        period_end=end_date,
    )


@router.post("/simulate")
async def simulate_earnings(
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Simulate earnings for demo purposes.
    This generates mock earnings for active vehicles.
    """
    service = EarningsService(db)
    await service.simulate_earnings(current_owner.id)
    return {"message": "Earnings simulated"}
