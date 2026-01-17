import { Battery, MapPin, Clock, TrendingUp } from 'lucide-react';
import { Vehicle } from '../../types/vehicle';

interface VehicleStatsProps {
  vehicle: Vehicle;
}

export function VehicleStats({ vehicle }: VehicleStatsProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getBatteryColor = (level: number) => {
    if (level >= 60) return 'text-green-500';
    if (level >= 30) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getBatteryBgColor = (level: number) => {
    if (level >= 60) return 'bg-green-500';
    if (level >= 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Battery */}
      <div className="bg-gray-50 rounded-xl p-3">
        <div className="flex items-center gap-2 mb-2">
          <Battery className={`w-4 h-4 ${getBatteryColor(vehicle.battery_level)}`} />
          <span className="text-xs text-gray-500">バッテリー</span>
        </div>
        <div className="flex items-end gap-1">
          <span className={`text-2xl font-bold ${getBatteryColor(vehicle.battery_level)}`}>
            {vehicle.battery_level}
          </span>
          <span className="text-sm text-gray-500 mb-1">%</span>
        </div>
        <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getBatteryBgColor(vehicle.battery_level)} transition-all`}
            style={{ width: `${vehicle.battery_level}%` }}
          />
        </div>
      </div>

      {/* Range */}
      <div className="bg-gray-50 rounded-xl p-3">
        <div className="flex items-center gap-2 mb-2">
          <MapPin className="w-4 h-4 text-blue-500" />
          <span className="text-xs text-gray-500">走行可能距離</span>
        </div>
        <div className="flex items-end gap-1">
          <span className="text-2xl font-bold text-gray-900">
            {vehicle.range_km}
          </span>
          <span className="text-sm text-gray-500 mb-1">km</span>
        </div>
      </div>

      {/* Today's Earnings */}
      <div className="bg-gray-50 rounded-xl p-3">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="w-4 h-4 text-emerald-500" />
          <span className="text-xs text-gray-500">本日の収益</span>
        </div>
        <div className="flex items-end gap-1">
          <span className="text-2xl font-bold text-emerald-600">
            {formatCurrency(vehicle.today_earnings)}
          </span>
        </div>
      </div>

      {/* Hourly Rate */}
      <div className="bg-gray-50 rounded-xl p-3">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="w-4 h-4 text-purple-500" />
          <span className="text-xs text-gray-500">時給</span>
        </div>
        <div className="flex items-end gap-1">
          <span className="text-2xl font-bold text-purple-600">
            {formatCurrency(vehicle.current_hourly_rate)}
          </span>
          <span className="text-sm text-gray-500 mb-1">/時</span>
        </div>
      </div>
    </div>
  );
}
