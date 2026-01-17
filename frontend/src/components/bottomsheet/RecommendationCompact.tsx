import { Sparkles, ArrowRight, TrendingUp } from 'lucide-react';
import { YieldPrediction } from '../../types/yield';
import { Vehicle, VehicleMode } from '../../types/vehicle';
import { ModeIndicator } from '../vehicle/ModeIndicator';

interface RecommendationCompactProps {
  predictions: Record<number, YieldPrediction>;
  vehicles: Vehicle[];
  onModeChange: (vehicleId: number, mode: VehicleMode) => void;
}

export function RecommendationCompact({
  predictions,
  vehicles,
  onModeChange,
}: RecommendationCompactProps) {
  // Find recommendations with potential gain
  const recommendations = vehicles
    .map(vehicle => ({
      vehicle,
      prediction: predictions[vehicle.id],
    }))
    .filter(({ prediction }) =>
      prediction?.best_recommendation?.is_recommended &&
      prediction.potential_gain > 0
    )
    .sort((a, b) => (b.prediction?.potential_gain || 0) - (a.prediction?.potential_gain || 0))
    .slice(0, 3);

  if (recommendations.length === 0) {
    return (
      <div className="flex items-center gap-2 py-3 text-gray-500 text-sm">
        <Sparkles size={16} className="text-gray-400" />
        <span>現在の設定が最適です</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles size={16} className="text-amber-500" />
        <h3 className="text-sm font-medium text-gray-900">AI推奨</h3>
      </div>

      <div className="space-y-2">
        {recommendations.map(({ vehicle, prediction }) => {
          const rec = prediction.best_recommendation!;

          return (
            <div
              key={vehicle.id}
              className="flex items-center justify-between p-3 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl"
            >
              <div className="flex items-center gap-3">
                {/* Vehicle Info */}
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {vehicle.name || vehicle.license_plate}
                  </p>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <ModeIndicator mode={vehicle.current_mode} size="sm" showLabel={false} />
                    <ArrowRight size={12} className="text-gray-400" />
                    <ModeIndicator mode={rec.mode} size="sm" showLabel={false} />
                  </div>
                </div>
              </div>

              {/* Action */}
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <div className="flex items-center gap-1 text-green-600 text-sm font-medium">
                    <TrendingUp size={12} />
                    <span>+¥{Math.round(prediction.potential_gain).toLocaleString()}/h</span>
                  </div>
                </div>
                <button
                  onClick={() => onModeChange(vehicle.id, rec.mode)}
                  className="px-3 py-1.5 bg-primary-500 text-white text-xs font-medium rounded-lg hover:bg-primary-600 active:bg-primary-700 transition-colors"
                >
                  切替
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
