import { Battery } from 'lucide-react';
import { Vehicle } from '../../types/vehicle';
import { ModeIndicator } from '../vehicle/ModeIndicator';

interface VehicleListCompactProps {
  vehicles: Vehicle[];
  selectedVehicleId: number | null;
  onVehicleSelect: (vehicle: Vehicle) => void;
}

export function VehicleListCompact({
  vehicles,
  selectedVehicleId,
  onVehicleSelect,
}: VehicleListCompactProps) {
  if (vehicles.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 text-sm">
        車両が登録されていません
      </div>
    );
  }

  return (
    <div className="overflow-x-auto pb-2 -mx-4 px-4">
      <div className="flex gap-3" style={{ minWidth: 'max-content' }}>
        {vehicles.map((vehicle) => (
          <button
            key={vehicle.id}
            onClick={() => onVehicleSelect(vehicle)}
            className={`
              flex-shrink-0 w-32 p-3 rounded-xl text-left transition-all
              ${selectedVehicleId === vehicle.id
                ? 'bg-primary-50 border-2 border-primary-500 shadow-sm'
                : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
              }
            `}
          >
            {/* Vehicle Name */}
            <p className="font-medium text-gray-900 text-sm truncate">
              {vehicle.name || vehicle.license_plate}
            </p>

            {/* Mode Badge */}
            <div className="mt-1">
              <ModeIndicator mode={vehicle.current_mode} size="sm" />
            </div>

            {/* Stats Row */}
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Battery size={12} className={vehicle.battery_level > 20 ? 'text-green-500' : 'text-red-500'} />
                <span>{vehicle.battery_level}%</span>
              </div>
              <span className="text-xs font-medium text-primary-600">
                ¥{vehicle.today_earnings.toLocaleString()}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
