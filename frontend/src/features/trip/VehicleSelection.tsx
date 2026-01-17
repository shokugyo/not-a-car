import { ChevronLeft, Car, Battery, Clock, Loader2 } from 'lucide-react';
import { useTripStore } from '../../store';
import { TripVehicle } from '../../types/trip';

interface VehicleCardProps {
  vehicle: TripVehicle;
  isSelected: boolean;
  onSelect: () => void;
}

function VehicleCard({ vehicle, isSelected, onSelect }: VehicleCardProps) {
  const getBatteryColor = (level: number) => {
    if (level >= 70) return 'text-green-500';
    if (level >= 30) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
        isSelected
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Vehicle Icon */}
        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <Car size={24} className="text-gray-600" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Name and Model */}
          <div className="flex items-start justify-between mb-1">
            <div>
              <h3 className="font-bold text-gray-900">
                {vehicle.name || `車両 #${vehicle.id}`}
              </h3>
              {vehicle.model && (
                <p className="text-xs text-gray-500">{vehicle.model}</p>
              )}
            </div>
            <span className="text-sm font-medium text-primary-600">
              ¥{vehicle.hourlyRate.toLocaleString()}/h
            </span>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
            <div className="flex items-center gap-1">
              <Battery size={14} className={getBatteryColor(vehicle.batteryLevel)} />
              <span>{vehicle.batteryLevel}%</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock size={14} className="text-gray-400" />
              <span>到着まで{vehicle.estimatedPickupTime}分</span>
            </div>
          </div>

          {/* Features */}
          {vehicle.features.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {vehicle.features.slice(0, 3).map((feature, index) => (
                <span
                  key={index}
                  className="px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600"
                >
                  {feature}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </button>
  );
}

export function VehicleSelection() {
  const {
    availableVehicles,
    selectedTripVehicleId,
    selectTripVehicle,
    createBooking,
    isBooking,
    setStep,
    error,
  } = useTripStore();

  const handleBack = () => {
    setStep('confirm');
  };

  const handleBook = async () => {
    if (!selectedTripVehicleId) return;
    await createBooking();
  };

  const selectedVehicle = availableVehicles.find(
    (v) => v.id === selectedTripVehicleId
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleBack}
          className="p-2 -ml-2 rounded-lg hover:bg-gray-100 active:bg-gray-200 transition-colors"
        >
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <h2 className="text-lg font-bold text-gray-900">車両を選択</h2>
          <p className="text-xs text-gray-500">
            {availableVehicles.length}台の車両が利用可能
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      {/* Vehicle List */}
      {availableVehicles.length === 0 ? (
        <div className="p-8 text-center">
          <Car size={48} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">
            現在利用可能な車両がありません
          </p>
          <p className="text-xs text-gray-400 mt-1">
            時間帯を変更してお試しください
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {availableVehicles.map((vehicle) => (
            <VehicleCard
              key={vehicle.id}
              vehicle={vehicle}
              isSelected={selectedTripVehicleId === vehicle.id}
              onSelect={() => selectTripVehicle(vehicle.id)}
            />
          ))}
        </div>
      )}

      {/* Selected Vehicle Summary */}
      {selectedVehicle && (
        <div className="p-4 bg-primary-50 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-700">選択中の車両</span>
            <span className="font-medium text-gray-900">
              {selectedVehicle.name || `車両 #${selectedVehicle.id}`}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">時間料金</span>
            <span className="text-lg font-bold text-primary-600">
              ¥{selectedVehicle.hourlyRate.toLocaleString()}/時間
            </span>
          </div>
        </div>
      )}

      {/* Book Button */}
      {selectedTripVehicleId && (
        <button
          onClick={handleBook}
          disabled={isBooking}
          className="w-full py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 active:bg-primary-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isBooking ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              予約中...
            </>
          ) : (
            'この車両で予約する'
          )}
        </button>
      )}
    </div>
  );
}
