from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import get_current_owner
from src.auth.models import Owner
from src.vehicles.service import VehicleService
from .schemas import YieldPrediction, MarketCondition, ModeComparison
from .optimizer import YieldOptimizer
from .market_analyzer import MarketAnalyzer


router = APIRouter()


@router.get("/prediction/{vehicle_id}", response_model=YieldPrediction)
async def get_yield_prediction(
    vehicle_id: int,
    time_horizon: int = 4,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Get revenue prediction and mode recommendations for a vehicle.

    Returns:
    - Current mode and hourly rate
    - Recommendations for each mode (sorted by potential revenue)
    - User-friendly message like "ホテル貸出に切り替えれば時給5,000円が見込めます"
    """
    vehicle_service = VehicleService(db)
    vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id, current_owner.id)

    optimizer = YieldOptimizer()
    prediction = optimizer.optimize(vehicle, time_horizon)

    return prediction


@router.get("/recommendation/{vehicle_id}", response_model=YieldPrediction)
async def get_recommendation(
    vehicle_id: int,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the best mode recommendation for a vehicle.
    Shorthand for /prediction with default time horizon.
    """
    vehicle_service = VehicleService(db)
    vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id, current_owner.id)

    optimizer = YieldOptimizer()
    prediction = optimizer.optimize(vehicle, time_horizon_hours=4)

    return prediction


@router.get("/market-data", response_model=MarketCondition)
async def get_market_data(
    latitude: float = 35.6762,
    longitude: float = 139.6503,
    current_owner: Owner = Depends(get_current_owner),
):
    """
    Get current market conditions for a location.
    Includes demand and pricing for each mode.
    """
    analyzer = MarketAnalyzer()
    market = analyzer.get_market_condition(latitude, longitude)
    return market


@router.get("/compare-modes/{vehicle_id}", response_model=ModeComparison)
async def compare_modes(
    vehicle_id: int,
    time_horizon: int = 4,
    current_owner: Owner = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare potential revenue across all modes for a vehicle.
    Useful for detailed analysis and decision making.
    """
    vehicle_service = VehicleService(db)
    vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id, current_owner.id)

    optimizer = YieldOptimizer()
    analyzer = MarketAnalyzer()

    market = analyzer.get_market_condition(vehicle.latitude, vehicle.longitude)

    # Get predictions for all modes
    predictions = [
        optimizer.predictor.predict_accommodation(market, vehicle.battery_level, time_horizon),
        optimizer.predictor.predict_delivery(market, vehicle.battery_level, time_horizon),
        optimizer.predictor.predict_rideshare(market, vehicle.battery_level, time_horizon),
    ]

    # Find optimal
    optimal = max(predictions, key=lambda p: p.total_revenue)

    # Calculate potential increase
    current_revenue = vehicle.current_hourly_rate * time_horizon
    potential_increase = optimal.total_revenue - current_revenue

    return ModeComparison(
        vehicle_id=vehicle.id,
        time_horizon_hours=time_horizon,
        modes=predictions,
        current_mode=vehicle.current_mode,
        optimal_mode=optimal.mode,
        potential_revenue_increase=potential_increase,
    )
