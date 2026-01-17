import React from 'react';
import { Battery, MapPin } from 'lucide-react';
import { Vehicle } from '../../types/vehicle';
import { Card } from '../ui/Card';
import { ModeIndicator } from './ModeIndicator';

interface VehicleCardProps {
  vehicle: Vehicle;
  onClick?: () => void;
}

export function VehicleCard({ vehicle, onClick }: VehicleCardProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Card
      className={`cursor-pointer hover:shadow-md transition-shadow ${!vehicle.is_active ? 'opacity-60' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-gray-900">
            {vehicle.name || vehicle.license_plate}
          </h3>
          <p className="text-sm text-gray-500">
            {vehicle.model} {vehicle.year && `(${vehicle.year})`}
          </p>
        </div>
        <ModeIndicator mode={vehicle.current_mode} />
      </div>

      <div className="space-y-3">
        {/* Hourly Rate */}
        {vehicle.current_hourly_rate > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">時給</span>
            <span className="font-semibold text-green-600">
              {formatCurrency(vehicle.current_hourly_rate)}
            </span>
          </div>
        )}

        {/* Today's Earnings */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">本日収益</span>
          <span className="font-semibold text-gray-900">
            {formatCurrency(vehicle.today_earnings)}
          </span>
        </div>

        {/* Battery */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <Battery size={14} />
            バッテリー
          </span>
          <div className="flex items-center gap-2">
            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  vehicle.battery_level > 50
                    ? 'bg-green-500'
                    : vehicle.battery_level > 20
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${vehicle.battery_level}%` }}
              />
            </div>
            <span className="text-sm font-medium">{vehicle.battery_level.toFixed(0)}%</span>
          </div>
        </div>

        {/* Location hint */}
        <div className="flex items-center text-xs text-gray-400 pt-2">
          <MapPin size={12} className="mr-1" />
          <span>
            {vehicle.latitude.toFixed(4)}, {vehicle.longitude.toFixed(4)}
          </span>
        </div>
      </div>
    </Card>
  );
}
