import { VehicleMode } from './vehicle';

export interface ModeRecommendation {
  mode: VehicleMode;
  predicted_hourly_rate: number;
  confidence: number;
  reasoning: string;
  transition_cost: number;
  net_benefit: number;
  is_recommended: boolean;
}

export interface YieldPrediction {
  vehicle_id: number;
  current_mode: VehicleMode;
  current_hourly_rate: number;
  recommendations: ModeRecommendation[];
  best_recommendation: ModeRecommendation | null;
  potential_gain: number;
  message: string;
  message_ja: string;
}

export interface MarketCondition {
  timestamp: string;
  latitude: number;
  longitude: number;
  accommodation_demand: number;
  accommodation_avg_price: number;
  nearby_hotels_occupancy: number;
  delivery_demand: number;
  delivery_avg_price: number;
  pending_delivery_jobs: number;
  rideshare_demand: number;
  rideshare_surge_multiplier: number;
  rideshare_avg_price: number;
}

export interface ModePrediction {
  mode: VehicleMode;
  predicted_hourly_rate: number;
  utilization: number;
  total_revenue: number;
  confidence: number;
  reasoning: string;
}

export interface ModeComparison {
  vehicle_id: number;
  time_horizon_hours: number;
  modes: ModePrediction[];
  current_mode: VehicleMode;
  optimal_mode: VehicleMode;
  potential_revenue_increase: number;
}
