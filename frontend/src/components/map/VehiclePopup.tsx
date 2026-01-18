import { Popup } from 'react-leaflet';
import { Battery, MapPin, Zap } from 'lucide-react';
import { Vehicle } from '../../types/vehicle';
import { ModeIndicator } from '../vehicle/ModeIndicator';

interface VehiclePopupProps {
  vehicle: Vehicle;
}

export function VehiclePopup({ vehicle }: VehiclePopupProps) {
  return (
    <Popup
      position={[vehicle.latitude, vehicle.longitude]}
      closeButton={false}
      className="vehicle-popup"
    >
      <div className="p-3 min-w-[200px]">
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="font-bold text-gray-900 text-sm">
              {vehicle.name || vehicle.license_plate}
            </h3>
            <p className="text-xs text-gray-500">{vehicle.model}</p>
          </div>
          <ModeIndicator mode={vehicle.current_mode} size="sm" />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 mb-2">
          <div className="flex items-center gap-1.5 text-xs text-gray-600">
            <Battery size={12} className="text-green-500" />
            <span>{vehicle.battery_level}%</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-gray-600">
            <MapPin size={12} className="text-blue-500" />
            <span>{vehicle.range_km}km</span>
          </div>
        </div>

        {/* Today's Earnings */}
        <div className="bg-primary-50 rounded-lg p-2 mb-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">本日の収益</span>
            <span className="font-bold text-primary-600 text-sm">
              ¥{vehicle.today_earnings.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-500 mt-0.5">
            <Zap size={10} />
            <span>¥{vehicle.current_hourly_rate.toLocaleString()}/時</span>
          </div>
        </div>

      </div>
    </Popup>
  );
}
