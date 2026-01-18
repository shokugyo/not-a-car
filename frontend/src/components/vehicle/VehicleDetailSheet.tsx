import { Vehicle, VehicleMode } from '../../types/vehicle';
import { YieldPrediction, ModeRecommendation } from '../../types/yield';
import { VehicleDetailHeader } from './VehicleDetailHeader';
import { VehicleImage } from './VehicleImage';
import { VehicleStats } from './VehicleStats';
import { ModeSelector } from './ModeSelector';
import { TrendingUp, Sparkles } from 'lucide-react';

interface VehicleDetailSheetProps {
  vehicle: Vehicle;
  prediction: YieldPrediction | null;
  onBack: () => void;
  onModeChange: (vehicleId: number, mode: VehicleMode) => Promise<void>;
  isChangingMode?: boolean;
}

export function VehicleDetailSheet({
  vehicle,
  prediction,
  onBack,
  onModeChange,
  isChangingMode = false,
}: VehicleDetailSheetProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleModeChange = async (mode: VehicleMode) => {
    await onModeChange(vehicle.id, mode);
  };

  const bestRecommendation = prediction?.best_recommendation;

  const currentRecommendation = prediction?.recommendations?.find(
    (r: ModeRecommendation) => r.mode === vehicle.current_mode
  );

  const potentialIncrease = prediction?.potential_gain ?? 0;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <VehicleDetailHeader vehicle={vehicle} onBack={onBack} />

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {/* Vehicle Image */}
        <VehicleImage
          vehicleId={vehicle.id}
          modelName={vehicle.model}
          className="h-48 w-full"
        />

        {/* Stats */}
        <VehicleStats vehicle={vehicle} />

        {/* Mode Selector */}
        <ModeSelector
          currentMode={vehicle.current_mode}
          allowedModes={vehicle.allowed_modes}
          onModeChange={handleModeChange}
          isLoading={isChangingMode}
        />

        {/* AI Recommendation */}
        {prediction && bestRecommendation && potentialIncrease > 0 && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Sparkles className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-blue-900 mb-1">AI推奨</h4>
                <p className="text-sm text-blue-700">
                  <span className="font-semibold">{getModeLabel(bestRecommendation.mode)}</span>
                  モードに切り替えると
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  <span className="text-lg font-bold text-emerald-600">
                    +{formatCurrency(potentialIncrease)}/時
                  </span>
                  <span className="text-sm text-gray-600">の収益増見込み</span>
                </div>
                {bestRecommendation.mode !== vehicle.current_mode && (
                  <button
                    onClick={() => handleModeChange(bestRecommendation.mode)}
                    disabled={isChangingMode}
                    className="mt-3 w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isChangingMode ? 'モード変更中...' : 'モードを変更する'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Current Prediction Info */}
        {currentRecommendation && (
          <div className="bg-gray-50 rounded-xl p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">現在の予測</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500">予測時給</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatCurrency(currentRecommendation.predicted_hourly_rate)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">信頼度</p>
                <p className="text-lg font-semibold text-gray-900">
                  {Math.round(currentRecommendation.confidence * 100)}%
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getModeLabel(mode: VehicleMode): string {
  const labels: Record<VehicleMode, string> = {
    idle: '待機',
    accommodation: '宿泊',
    delivery: '配送',
    rideshare: 'ライドシェア',
    maintenance: 'メンテナンス',
    charging: '充電',
    transit: '回送',
  };
  return labels[mode] || mode;
}
