from src.vehicles.models import VehicleMode
from .schemas import MarketCondition, ModePrediction


class ModePredictor:
    """Predicts revenue for each operation mode"""

    def predict_accommodation(
        self,
        market: MarketCondition,
        battery_level: float,
        hours: int = 4,
    ) -> ModePrediction:
        """Predict accommodation mode revenue"""
        demand = market.accommodation_demand
        base_rate = market.accommodation_avg_price
        hotel_occupancy = market.nearby_hotels_occupancy

        # Factors affecting price
        scarcity_factor = 1 + (hotel_occupancy - 0.5) * 0.5
        demand_factor = 1 + (demand - 0.5) * 0.3

        predicted_rate = base_rate * scarcity_factor * demand_factor

        # Utilization based on demand
        utilization = min(0.95, demand * 1.1)

        # Battery doesn't affect accommodation much (parked)
        if battery_level < 20:
            utilization *= 0.8  # Need to charge before starting

        total_revenue = predicted_rate * hours * utilization
        confidence = 0.85 if demand > 0.5 else 0.65

        reasoning = f"需要: {demand:.0%}, 周辺ホテル稼働率: {hotel_occupancy:.0%}"

        return ModePrediction(
            mode=VehicleMode.ACCOMMODATION,
            predicted_hourly_rate=round(predicted_rate, 0),
            utilization=round(utilization, 2),
            total_revenue=round(total_revenue, 0),
            confidence=round(confidence, 2),
            reasoning=reasoning,
        )

    def predict_delivery(
        self,
        market: MarketCondition,
        battery_level: float,
        hours: int = 4,
    ) -> ModePrediction:
        """Predict delivery mode revenue"""
        demand = market.delivery_demand
        base_rate = market.delivery_avg_price
        pending_jobs = market.pending_delivery_jobs

        # More jobs = higher potential
        job_factor = 1 + min(pending_jobs / 50, 0.5)
        demand_factor = 1 + (demand - 0.5) * 0.4

        predicted_rate = base_rate * job_factor * demand_factor

        # Higher utilization potential with many jobs
        utilization = min(0.9, (demand + pending_jobs / 100) * 0.7)

        # Battery is important for delivery
        if battery_level < 30:
            utilization *= 0.6
            predicted_rate *= 0.8

        total_revenue = predicted_rate * hours * utilization
        confidence = 0.8 if pending_jobs > 20 else 0.6

        reasoning = f"需要: {demand:.0%}, 待機配送: {pending_jobs}"

        return ModePrediction(
            mode=VehicleMode.DELIVERY,
            predicted_hourly_rate=round(predicted_rate, 0),
            utilization=round(utilization, 2),
            total_revenue=round(total_revenue, 0),
            confidence=round(confidence, 2),
            reasoning=reasoning,
        )

    def predict_rideshare(
        self,
        market: MarketCondition,
        battery_level: float,
        hours: int = 4,
    ) -> ModePrediction:
        """Predict rideshare mode revenue"""
        demand = market.rideshare_demand
        base_rate = market.rideshare_avg_price
        surge = market.rideshare_surge_multiplier

        # Surge pricing
        predicted_rate = base_rate * surge

        # Demand affects utilization
        utilization = min(0.85, demand * 0.9)

        # Battery is critical for rideshare
        if battery_level < 40:
            utilization *= 0.5
            predicted_rate *= 0.7

        total_revenue = predicted_rate * hours * utilization
        confidence = 0.75 if surge > 1.2 else 0.65

        reasoning = f"需要: {demand:.0%}, サージ: {surge:.1f}x"

        return ModePrediction(
            mode=VehicleMode.RIDESHARE,
            predicted_hourly_rate=round(predicted_rate, 0),
            utilization=round(utilization, 2),
            total_revenue=round(total_revenue, 0),
            confidence=round(confidence, 2),
            reasoning=reasoning,
        )
