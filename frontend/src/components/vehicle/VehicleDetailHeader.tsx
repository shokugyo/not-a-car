import { ArrowLeft, Settings } from 'lucide-react';
import { Vehicle } from '../../types/vehicle';
import { ModeIndicator } from './ModeIndicator';

interface VehicleDetailHeaderProps {
  vehicle: Vehicle;
  onBack: () => void;
  onSettings?: () => void;
}

export function VehicleDetailHeader({
  vehicle,
  onBack,
  onSettings,
}: VehicleDetailHeaderProps) {
  const displayName = vehicle.name || vehicle.license_plate;

  return (
    <div className="flex items-center justify-between py-3 px-1">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors -ml-2 p-2"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="text-sm font-medium">戻る</span>
      </button>

      <div className="flex-1 text-center">
        <h2 className="text-lg font-semibold text-gray-900 truncate px-4">
          {displayName}
        </h2>
        <div className="flex items-center justify-center gap-2 mt-0.5">
          <ModeIndicator mode={vehicle.current_mode} size="sm" />
          <span className="text-xs text-gray-500">
            {vehicle.model || '車両'}
          </span>
        </div>
      </div>

      {onSettings && (
        <button
          onClick={onSettings}
          className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <Settings className="w-5 h-5" />
        </button>
      )}
      {!onSettings && <div className="w-10" />}
    </div>
  );
}
