import { Popup } from 'react-leaflet';
import { Battery, MapPin, Zap } from 'lucide-react';
import { Vehicle, VehicleMode } from '../../types/vehicle';
import { ModeIndicator } from '../vehicle/ModeIndicator';

interface VehiclePopupProps {
  vehicle: Vehicle;
  onModeChange: (vehicleId: number, mode: VehicleMode) => void;
  onClose: () => void;
}

const availableModes: VehicleMode[] = ['idle', 'accommodation', 'delivery', 'rideshare'];

export function VehiclePopup({ vehicle, onModeChange, onClose }: VehiclePopupProps) {
  const handleModeChange = (mode: VehicleMode) => {
    onModeChange(vehicle.id, mode);
    onClose();
  };

  return (
    <Popup
      position={[vehicle.latitude, vehicle.longitude]}
      closeButton={false}
      className="vehicle-popup"
    >
      <div className="p-4 min-w-[240px]">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-bold text-gray-900">
              {vehicle.name || vehicle.license_plate}
            </h3>
            <p className="text-xs text-gray-500">{vehicle.model}</p>
          </div>
          <ModeIndicator mode={vehicle.current_mode} size="sm" />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="flex items-center gap-1.5 text-sm text-gray-600">
            <Battery size={14} className="text-green-500" />
            <span>{vehicle.battery_level}%</span>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-gray-600">
            <MapPin size={14} className="text-blue-500" />
            <span>{vehicle.range_km}km</span>
          </div>
        </div>

        {/* Today's Earnings */}
        <div className="bg-primary-50 rounded-lg p-2 mb-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">本日の収益</span>
            <span className="font-bold text-primary-600">
              ¥{vehicle.today_earnings.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
            <Zap size={10} />
            <span>¥{vehicle.current_hourly_rate.toLocaleString()}/時</span>
          </div>
        </div>

        {/* Mode Change Buttons */}
        <div className="space-y-2">
          <p className="text-xs text-gray-500 font-medium">モード変更</p>
          <div className="grid grid-cols-2 gap-2">
            {availableModes.map((mode) => (
              <button
                key={mode}
                onClick={() => handleModeChange(mode)}
                disabled={vehicle.current_mode === mode}
                className={`
                  px-3 py-2 text-xs font-medium rounded-lg transition-colors
                  ${vehicle.current_mode === mode
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 active:bg-gray-100'
                  }
                `}
              >
                <ModeIndicator mode={mode} size="sm" showLabel={true} />
              </button>
            ))}
          </div>
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="mt-3 w-full py-2 text-sm text-gray-500 hover:text-gray-700"
        >
          閉じる
        </button>
      </div>
    </Popup>
  );
}
