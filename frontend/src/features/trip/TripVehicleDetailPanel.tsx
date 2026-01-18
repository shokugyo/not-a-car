import { X, Battery, Clock, Gauge, Zap } from 'lucide-react';
import { TripVehicle } from '../../types/trip';
import { VehicleImage } from '../../components/vehicle/VehicleImage';

interface TripVehicleDetailPanelProps {
  vehicle: TripVehicle;
  onClose: () => void;
  onSelect: () => void;
  isSelected: boolean;
}

export function TripVehicleDetailPanel({
  vehicle,
  onClose,
  onSelect,
  isSelected,
}: TripVehicleDetailPanelProps) {
  const getBatteryColor = (level: number) => {
    if (level >= 70) return 'text-green-500';
    if (level >= 30) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getBatteryBgColor = (level: number) => {
    if (level >= 70) return 'bg-green-500';
    if (level >= 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header with close button */}
      <div className="relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-10 p-2 rounded-full bg-black/30 backdrop-blur-sm hover:bg-black/50 transition-colors"
          aria-label="閉じる"
        >
          <X size={18} className="text-white" />
        </button>

        {/* Vehicle Image */}
        <VehicleImage
          vehicleId={vehicle.id}
          modelName={vehicle.model}
          className="h-48 w-full"
        />
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Vehicle Name and Price */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              {vehicle.name || `車両 #${vehicle.id}`}
            </h3>
            {vehicle.model && (
              <p className="text-sm text-gray-500">{vehicle.model}</p>
            )}
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-primary-600">
              ¥{vehicle.hourlyRate.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">/時間</p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3">
          {/* Battery */}
          <div className="bg-gray-50 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <Battery className={`w-4 h-4 ${getBatteryColor(vehicle.batteryLevel)}`} />
              <span className="text-xs text-gray-500">バッテリー</span>
            </div>
            <div className="flex items-end gap-1">
              <span className={`text-2xl font-bold ${getBatteryColor(vehicle.batteryLevel)}`}>
                {vehicle.batteryLevel}
              </span>
              <span className="text-sm text-gray-500 mb-1">%</span>
            </div>
            <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getBatteryBgColor(vehicle.batteryLevel)} transition-all`}
                style={{ width: `${vehicle.batteryLevel}%` }}
              />
            </div>
          </div>

          {/* Range */}
          <div className="bg-gray-50 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-gray-500">航続距離</span>
            </div>
            <div className="flex items-end gap-1">
              <span className="text-2xl font-bold text-gray-900">
                {vehicle.rangeKm}
              </span>
              <span className="text-sm text-gray-500 mb-1">km</span>
            </div>
          </div>

          {/* Pickup Time */}
          <div className="bg-gray-50 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-amber-500" />
              <span className="text-xs text-gray-500">到着予定</span>
            </div>
            <div className="flex items-end gap-1">
              <span className="text-2xl font-bold text-amber-600">
                {vehicle.estimatedPickupTime}
              </span>
              <span className="text-sm text-gray-500 mb-1">分</span>
            </div>
          </div>

          {/* Mode */}
          <div className="bg-gray-50 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-purple-500" />
              <span className="text-xs text-gray-500">現在の状態</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-purple-600">
                {getModeLabel(vehicle.currentMode)}
              </span>
            </div>
          </div>
        </div>

        {/* Features */}
        {vehicle.features.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">車両機能</h4>
            <div className="flex flex-wrap gap-2">
              {vehicle.features.map((feature, index) => (
                <span
                  key={index}
                  className="px-3 py-1.5 bg-primary-50 text-primary-700 rounded-lg text-sm font-medium"
                >
                  {feature}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Select Button */}
        <button
          onClick={onSelect}
          className={`w-full py-3 rounded-xl font-medium transition-all ${
            isSelected
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {isSelected ? '選択中' : 'この車両を選択'}
        </button>
      </div>
    </div>
  );
}

function getModeLabel(mode: string): string {
  const labels: Record<string, string> = {
    idle: '待機中',
    accommodation: '宿泊',
    delivery: '配送',
    rideshare: '配車可能',
    maintenance: 'メンテナンス',
    charging: '充電中',
    transit: '回送中',
  };
  return labels[mode] || mode;
}
