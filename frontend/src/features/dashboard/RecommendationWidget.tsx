import { Lightbulb, ArrowRight, TrendingUp } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { ModeIndicator } from '../../components/vehicle/ModeIndicator';
import { YieldPrediction } from '../../types/yield';
import { VehicleMode } from '../../types/vehicle';

interface RecommendationWidgetProps {
  predictions: Record<number, YieldPrediction>;
  vehicleNames: Record<number, string>;
  onModeChange: (vehicleId: number, mode: VehicleMode) => void;
  isLoading?: boolean;
}

export function RecommendationWidget({
  predictions,
  vehicleNames,
  onModeChange,
  isLoading,
}: RecommendationWidgetProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Filter predictions with positive potential gain
  const gainPredictions = Object.values(predictions).filter(
    (p) => p.potential_gain > 0 && p.best_recommendation
  );

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="text-yellow-500" size={20} />
            AI推奨
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="text-yellow-500" size={20} />
          AI推奨 - Yield-Drive AI
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {gainPredictions.length > 0 ? (
          gainPredictions.map((prediction) => {
            const rec = prediction.best_recommendation!;
            const vehicleName =
              vehicleNames[prediction.vehicle_id] ||
              `車両 #${prediction.vehicle_id}`;

            return (
              <div
                key={prediction.vehicle_id}
                className="p-4 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-lg border border-yellow-200"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-medium text-gray-900">{vehicleName}</p>
                    <div className="flex items-center gap-2 mt-1 text-sm text-gray-600">
                      <ModeIndicator mode={prediction.current_mode} size="sm" />
                      <ArrowRight size={14} />
                      <ModeIndicator mode={rec.mode} size="sm" />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">期待時給</p>
                    <p className="text-lg font-bold text-green-600">
                      {formatCurrency(rec.predicted_hourly_rate)}
                    </p>
                  </div>
                </div>

                {/* Recommendation Message */}
                <p className="text-sm text-amber-800 mb-3 flex items-start gap-2">
                  <TrendingUp size={16} className="mt-0.5 flex-shrink-0" />
                  {prediction.message_ja}
                </p>

                {/* Potential Gain */}
                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    <span className="text-gray-500">予想増益: </span>
                    <span className="font-semibold text-green-600">
                      +{formatCurrency(prediction.potential_gain)}
                    </span>
                    <span className="text-gray-400 ml-1">(4時間)</span>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => onModeChange(prediction.vehicle_id, rec.mode)}
                  >
                    切り替える
                  </Button>
                </div>

                {/* Confidence */}
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-gray-500">信頼度:</span>
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full"
                      style={{ width: `${rec.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500">
                    {(rec.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Lightbulb size={32} className="mx-auto mb-2 text-gray-300" />
            <p>現在のモードが最適です</p>
            <p className="text-sm mt-1">
              より良い収益機会が見つかり次第お知らせします
            </p>
          </div>
        )}

        {Object.keys(predictions).length === 0 && (
          <div className="text-center py-6 text-gray-500">
            <p>車両を登録して収益予測を開始しましょう</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
