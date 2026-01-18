import { X, Battery, Sparkles, ChevronUp, Bed, Package, Car, Pause } from 'lucide-react';
import { Vehicle, VehicleMode } from '../../types/vehicle';
import { YieldPrediction } from '../../types/yield';
import { ModeIndicator, getModeLabel } from './ModeIndicator';

interface VehiclePreviewCardProps {
  vehicle: Vehicle;
  prediction: YieldPrediction | null;
  onViewDetail: () => void;
  onClose: () => void;
  onModeChange: (vehicleId: number, mode: VehicleMode) => void;
  isChangingMode?: boolean;
}

const modeOptions: {
  mode: VehicleMode;
  icon: React.ElementType;
  label: string;
  activeColor: string;
  activeBg: string;
  borderColor: string;
}[] = [
  {
    mode: 'idle',
    icon: Pause,
    label: '待機',
    activeColor: 'text-gray-700',
    activeBg: 'bg-gray-100',
    borderColor: 'border-gray-300',
  },
  {
    mode: 'accommodation',
    icon: Bed,
    label: '宿泊',
    activeColor: 'text-purple-700',
    activeBg: 'bg-purple-50',
    borderColor: 'border-purple-300',
  },
  {
    mode: 'delivery',
    icon: Package,
    label: '配送',
    activeColor: 'text-amber-700',
    activeBg: 'bg-amber-50',
    borderColor: 'border-amber-300',
  },
  {
    mode: 'rideshare',
    icon: Car,
    label: 'ライド',
    activeColor: 'text-blue-700',
    activeBg: 'bg-blue-50',
    borderColor: 'border-blue-300',
  },
];

export function VehiclePreviewCard({
  vehicle,
  prediction,
  onViewDetail,
  onClose,
  onModeChange,
  isChangingMode = false,
}: VehiclePreviewCardProps) {
  const bestRecommendation = prediction?.best_recommendation;
  const hasBetterMode = bestRecommendation && bestRecommendation.mode !== vehicle.current_mode;

  const handleModeChange = (mode: VehicleMode) => {
    if (mode !== vehicle.current_mode && !isChangingMode) {
      onModeChange(vehicle.id, mode);
    }
  };

  return (
    <div className="bg-white rounded-t-2xl">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors z-10"
        aria-label="閉じる"
      >
        <X size={18} className="text-gray-600" />
      </button>

      {/* Vehicle Header */}
      <div className="mb-3">
        <h2 className="text-lg font-bold text-gray-900 pr-10">
          {vehicle.name || `車両 ${vehicle.id}`}
        </h2>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-sm text-gray-500">{vehicle.license_plate}</span>
          {vehicle.model && (
            <>
              <span className="text-gray-300">•</span>
              <span className="text-sm text-gray-500">{vehicle.model}</span>
            </>
          )}
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg mb-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <Battery size={16} className="text-green-500" />
            <span className="text-sm font-medium text-gray-700">
              {vehicle.battery_level}%
            </span>
          </div>
          <ModeIndicator mode={vehicle.current_mode} size="sm" />
        </div>
        <div className="text-right">
          <span className="text-base font-bold text-gray-900">
            ¥{vehicle.today_earnings.toLocaleString()}
          </span>
          <span className="text-xs text-gray-500 ml-1">本日</span>
        </div>
      </div>

      {/* AI Recommendation + Quick Action */}
      {hasBetterMode && (
        <button
          onClick={() => handleModeChange(bestRecommendation.mode)}
          disabled={isChangingMode}
          className="w-full mb-3 p-3 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl text-white
                     hover:from-indigo-600 hover:to-purple-600 transition-all active:scale-[0.98]
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-white/90" />
              <div className="text-left">
                <p className="text-sm font-medium">
                  AI推奨: {getModeLabel(bestRecommendation.mode)}に切替
                </p>
                <p className="text-xs text-white/80">
                  +¥{Math.round(bestRecommendation.net_benefit).toLocaleString()}/時 見込み
                </p>
              </div>
            </div>
            <div className="bg-white/20 rounded-lg px-3 py-1.5 text-sm font-medium">
              切替
            </div>
          </div>
        </button>
      )}

      {/* Mode Switch Buttons */}
      <div className="mb-3">
        <p className="text-xs text-gray-500 mb-2">モード切替</p>
        <div className="grid grid-cols-4 gap-2">
          {modeOptions.map(({ mode, icon: Icon, label, activeColor, activeBg, borderColor }) => {
            const isActive = vehicle.current_mode === mode;
            const isRecommended = bestRecommendation?.mode === mode && !isActive;

            return (
              <button
                key={mode}
                onClick={() => handleModeChange(mode)}
                disabled={isActive || isChangingMode}
                className={`
                  flex flex-col items-center justify-center py-2.5 px-1 rounded-xl border-2 transition-all
                  ${isActive
                    ? `${activeBg} ${borderColor} ${activeColor}`
                    : isRecommended
                      ? 'bg-indigo-50 border-indigo-200 text-indigo-600'
                      : 'bg-white border-gray-200 text-gray-500 hover:border-gray-300 hover:bg-gray-50'
                  }
                  ${isActive ? 'cursor-default' : 'active:scale-95'}
                  disabled:opacity-60
                `}
              >
                <Icon size={20} className="mb-0.5" />
                <span className="text-xs font-medium">{label}</span>
                {isRecommended && (
                  <Sparkles size={10} className="absolute -top-1 -right-1 text-indigo-500" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* View Detail Button */}
      <button
        onClick={onViewDetail}
        className="w-full py-2.5 bg-gray-100 text-gray-700 rounded-xl font-medium
                   flex items-center justify-center gap-1.5 hover:bg-gray-200 transition-colors text-sm"
      >
        <span>詳細・3Dビュー</span>
        <ChevronUp size={16} />
      </button>
    </div>
  );
}
