from typing import List

from src.vehicles.models import Vehicle, VehicleMode, InteriorMode
from .schemas import MarketCondition, ModeRecommendation, YieldPrediction
from .predictor import ModePredictor
from .market_analyzer import MarketAnalyzer


# Interior change time in minutes
INTERIOR_CHANGE_TIME = {
    (InteriorMode.STANDARD, InteriorMode.BED): 30,
    (InteriorMode.STANDARD, InteriorMode.CARGO): 20,
    (InteriorMode.STANDARD, InteriorMode.PASSENGER): 15,
    (InteriorMode.BED, InteriorMode.CARGO): 45,
    (InteriorMode.BED, InteriorMode.PASSENGER): 40,
    (InteriorMode.CARGO, InteriorMode.BED): 45,
    (InteriorMode.CARGO, InteriorMode.PASSENGER): 25,
    (InteriorMode.PASSENGER, InteriorMode.BED): 40,
    (InteriorMode.PASSENGER, InteriorMode.CARGO): 25,
}

MODE_TO_INTERIOR = {
    VehicleMode.ACCOMMODATION: InteriorMode.BED,
    VehicleMode.DELIVERY: InteriorMode.CARGO,
    VehicleMode.RIDESHARE: InteriorMode.PASSENGER,
    VehicleMode.IDLE: InteriorMode.STANDARD,
}


class YieldOptimizer:
    """
    Yield-Drive AI Engine
    Optimizes vehicle mode selection for maximum revenue.
    """

    def __init__(self):
        self.predictor = ModePredictor()
        self.market_analyzer = MarketAnalyzer()

    def calculate_transition_cost(
        self,
        current_interior: InteriorMode,
        target_mode: VehicleMode,
        current_hourly_rate: float,
    ) -> float:
        """Calculate cost of switching modes (opportunity cost)"""
        target_interior = MODE_TO_INTERIOR.get(target_mode, InteriorMode.STANDARD)

        if current_interior == target_interior:
            return 0.0

        # Get transition time
        transition_time = INTERIOR_CHANGE_TIME.get(
            (current_interior, target_interior),
            30  # Default 30 minutes
        )

        # Opportunity cost = time * current rate
        opportunity_cost = (transition_time / 60) * current_hourly_rate

        return round(opportunity_cost, 0)

    def optimize(
        self,
        vehicle: Vehicle,
        time_horizon_hours: int = 4,
    ) -> YieldPrediction:
        """
        Generate optimal mode recommendations for a vehicle.
        Returns predictions with user-friendly messages.
        """
        # Get market conditions for vehicle's location
        market = self.market_analyzer.get_market_condition(
            vehicle.latitude,
            vehicle.longitude,
        )

        recommendations: List[ModeRecommendation] = []

        # Predict for each mode
        modes_to_predict = [
            (VehicleMode.ACCOMMODATION, self.predictor.predict_accommodation),
            (VehicleMode.DELIVERY, self.predictor.predict_delivery),
            (VehicleMode.RIDESHARE, self.predictor.predict_rideshare),
        ]

        for mode, predict_func in modes_to_predict:
            # Check if mode is allowed
            if mode.value not in vehicle.allowed_modes:
                continue

            prediction = predict_func(
                market=market,
                battery_level=vehicle.battery_level,
                hours=time_horizon_hours,
            )

            # Calculate transition cost
            transition_cost = self.calculate_transition_cost(
                vehicle.interior_mode,
                mode,
                vehicle.current_hourly_rate,
            )

            # Net benefit = predicted revenue - transition cost
            net_benefit = prediction.total_revenue - transition_cost

            recommendations.append(ModeRecommendation(
                mode=mode,
                predicted_hourly_rate=prediction.predicted_hourly_rate,
                confidence=prediction.confidence,
                reasoning=prediction.reasoning,
                transition_cost=transition_cost,
                net_benefit=net_benefit,
            ))

        # Sort by net benefit
        recommendations.sort(key=lambda x: x.net_benefit, reverse=True)

        # Mark best as recommended
        if recommendations:
            recommendations[0].is_recommended = True

        # Calculate potential gain
        current_revenue = vehicle.current_hourly_rate * time_horizon_hours
        best_revenue = recommendations[0].net_benefit if recommendations else 0
        potential_gain = best_revenue - current_revenue

        # Generate user-friendly messages
        best_rec = recommendations[0] if recommendations else None

        if best_rec and potential_gain > 0:
            mode_names = {
                VehicleMode.ACCOMMODATION: ("hotel rental", "ホテル貸出"),
                VehicleMode.DELIVERY: ("delivery", "配送業務"),
                VehicleMode.RIDESHARE: ("rideshare", "ライドシェア"),
            }
            mode_en, mode_ja = mode_names.get(best_rec.mode, (best_rec.mode.value, best_rec.mode.value))

            message = f"Switch to {mode_en} for {best_rec.predicted_hourly_rate:,.0f}/hr (potential +{potential_gain:,.0f})"
            message_ja = f"{mode_ja}に切り替えれば時給{best_rec.predicted_hourly_rate:,.0f}円が見込めます"
        else:
            message = "Current mode is optimal"
            message_ja = "現在のモードが最適です"

        return YieldPrediction(
            vehicle_id=vehicle.id,
            current_mode=vehicle.current_mode,
            current_hourly_rate=vehicle.current_hourly_rate,
            recommendations=recommendations,
            best_recommendation=best_rec,
            potential_gain=potential_gain,
            message=message,
            message_ja=message_ja,
        )
