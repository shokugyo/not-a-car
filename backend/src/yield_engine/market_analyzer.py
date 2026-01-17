from datetime import datetime, timezone
import random
import math

from .schemas import MarketCondition


class MarketAnalyzer:
    """
    Analyzes market conditions for each operation mode.
    In MVP, this uses simulated data. In production, would connect to real APIs.
    """

    def __init__(self):
        # Demand patterns by hour (0-23)
        self.accommodation_hourly_demand = {
            0: 0.9, 1: 0.9, 2: 0.8, 3: 0.7, 4: 0.6, 5: 0.5,
            6: 0.4, 7: 0.3, 8: 0.2, 9: 0.2, 10: 0.3, 11: 0.3,
            12: 0.3, 13: 0.3, 14: 0.4, 15: 0.5, 16: 0.6, 17: 0.7,
            18: 0.8, 19: 0.85, 20: 0.9, 21: 0.95, 22: 0.95, 23: 0.9,
        }

        self.delivery_hourly_demand = {
            0: 0.1, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.1, 5: 0.2,
            6: 0.4, 7: 0.6, 8: 0.7, 9: 0.6, 10: 0.5, 11: 0.8,
            12: 0.9, 13: 0.7, 14: 0.5, 15: 0.4, 16: 0.5, 17: 0.7,
            18: 0.9, 19: 0.95, 20: 0.8, 21: 0.5, 22: 0.3, 23: 0.2,
        }

        self.rideshare_hourly_demand = {
            0: 0.7, 1: 0.5, 2: 0.3, 3: 0.2, 4: 0.2, 5: 0.3,
            6: 0.5, 7: 0.8, 8: 0.9, 9: 0.7, 10: 0.5, 11: 0.5,
            12: 0.6, 13: 0.5, 14: 0.5, 15: 0.6, 16: 0.7, 17: 0.9,
            18: 0.95, 19: 0.9, 20: 0.85, 21: 0.8, 22: 0.85, 23: 0.8,
        }

    def get_market_condition(
        self,
        latitude: float,
        longitude: float,
    ) -> MarketCondition:
        """Get current market conditions for a location"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        is_weekend = now.weekday() >= 5

        # Base demand from hourly patterns
        acc_demand = self.accommodation_hourly_demand.get(hour, 0.5)
        del_demand = self.delivery_hourly_demand.get(hour, 0.5)
        ride_demand = self.rideshare_hourly_demand.get(hour, 0.5)

        # Weekend adjustments
        if is_weekend:
            acc_demand *= 1.3  # More accommodation demand on weekends
            del_demand *= 0.8  # Less delivery
            ride_demand *= 1.2  # More rideshare

        # Location-based adjustments (simulate urban vs suburban)
        # Using Tokyo coordinates as reference
        tokyo_lat, tokyo_lng = 35.6762, 139.6503
        distance_from_center = math.sqrt(
            (latitude - tokyo_lat) ** 2 + (longitude - tokyo_lng) ** 2
        )

        # Closer to center = higher demand for all modes
        location_factor = max(0.5, 1 - distance_from_center * 10)

        acc_demand = min(1.0, acc_demand * location_factor)
        del_demand = min(1.0, del_demand * location_factor)
        ride_demand = min(1.0, ride_demand * location_factor)

        # Add some randomness for realism
        acc_demand = min(1.0, acc_demand * random.uniform(0.9, 1.1))
        del_demand = min(1.0, del_demand * random.uniform(0.9, 1.1))
        ride_demand = min(1.0, ride_demand * random.uniform(0.9, 1.1))

        # Calculate prices based on demand
        acc_base_price = 4000  # Base hourly rate
        del_base_price = 1500
        ride_base_price = 2000

        # Surge pricing based on demand
        acc_price = acc_base_price * (1 + acc_demand * 0.5)
        del_price = del_base_price * (1 + del_demand * 0.3)
        ride_price = ride_base_price * (1 + ride_demand * 0.8)

        # Rideshare surge multiplier
        surge = 1.0 + (ride_demand - 0.5) * 1.5 if ride_demand > 0.7 else 1.0

        return MarketCondition(
            timestamp=now,
            latitude=latitude,
            longitude=longitude,
            accommodation_demand=round(acc_demand, 2),
            accommodation_avg_price=round(acc_price, 0),
            nearby_hotels_occupancy=round(0.5 + acc_demand * 0.4, 2),
            delivery_demand=round(del_demand, 2),
            delivery_avg_price=round(del_price, 0),
            pending_delivery_jobs=int(del_demand * 50),
            rideshare_demand=round(ride_demand, 2),
            rideshare_surge_multiplier=round(surge, 2),
            rideshare_avg_price=round(ride_price, 0),
        )
