import { useState, useEffect } from 'react';
import { ChevronLeft, Car, Battery, Clock, Loader2, Info, List, ChevronRight } from 'lucide-react';
import { useTripStore, useUIStore } from '../../store';
import { TripVehicle } from '../../types/trip';
import { TripVehicleDetailPanel } from './TripVehicleDetailPanel';

interface VehicleCardProps {
  vehicle: TripVehicle;
  isSelected: boolean;
  onSelect: () => void;
  onViewDetail: () => void;
}

function VehicleCard({ vehicle, isSelected, onSelect, onViewDetail }: VehicleCardProps) {
  const getBatteryColor = (level: number) => {
    if (level >= 70) return 'text-green-500';
    if (level >= 30) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div
      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
        isSelected
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Vehicle Icon - clickable for selection */}
        <button
          onClick={onSelect}
          className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0 hover:bg-gray-200 transition-colors"
        >
          <Car size={24} className="text-gray-600" />
        </button>

        <div className="flex-1 min-w-0">
          {/* Name and Model - clickable for selection */}
          <button
            onClick={onSelect}
            className="w-full text-left"
          >
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
          </button>
        </div>

        {/* Detail button */}
        <button
          onClick={onViewDetail}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors flex-shrink-0"
          aria-label="詳細を見る"
        >
          <ChevronRight size={20} className="text-gray-400" />
        </button>
      </div>
    </div>
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

  const { setSelectedVehicleId } = useUIStore();

  // State for showing detail view
  const [detailVehicleId, setDetailVehicleId] = useState<number | null>(null);

  // Focus map on selected vehicle
  useEffect(() => {
    if (selectedTripVehicleId) {
      setSelectedVehicleId(selectedTripVehicleId);
    }
  }, [selectedTripVehicleId, setSelectedVehicleId]);

  // Clear map selection when leaving this step
  useEffect(() => {
    return () => {
      setSelectedVehicleId(null);
    };
  }, [setSelectedVehicleId]);

  const handleBack = () => {
    if (detailVehicleId !== null) {
      // If in detail view, go back to list
      setDetailVehicleId(null);
    } else {
      // Otherwise, go back to confirm step
      setStep('confirm');
    }
  };

  const handleBook = async () => {
    if (!selectedTripVehicleId) return;
    await createBooking();
  };

  const handleViewDetail = (vehicleId: number) => {
    setDetailVehicleId(vehicleId);
  };

  const handleCloseDetail = () => {
    setDetailVehicleId(null);
  };

  const handleSelectFromDetail = () => {
    if (detailVehicleId !== null) {
      selectTripVehicle(detailVehicleId);
    }
  };

  const selectedVehicle = availableVehicles.find(
    (v) => v.id === selectedTripVehicleId
  );

  const detailVehicle = availableVehicles.find(
    (v) => v.id === detailVehicleId
  );

  // Show detail view
  if (detailVehicle) {
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
          <div className="flex-1">
            <h2 className="text-lg font-bold text-gray-900">車両詳細</h2>
            <p className="text-xs text-gray-500">
              詳細情報を確認して選択
            </p>
          </div>
          <button
            onClick={handleCloseDetail}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-1 text-sm text-gray-600"
          >
            <List size={16} />
            <span>一覧</span>
          </button>
        </div>

        {/* Detail Panel */}
        <TripVehicleDetailPanel
          vehicle={detailVehicle}
          onClose={handleCloseDetail}
          onSelect={handleSelectFromDetail}
          isSelected={selectedTripVehicleId === detailVehicle.id}
        />

        {/* Book Button (when selected) */}
        {selectedTripVehicleId === detailVehicle.id && (
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

  // Show list view
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

      {/* Hint */}
      <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
        <Info size={14} />
        <span>カードをタップで選択、右矢印で詳細表示</span>
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
              onViewDetail={() => handleViewDetail(vehicle.id)}
            />
          ))}
        </div>
      )}

      {/* Selected Vehicle Summary */}
      {selectedVehicle && (
        <div className="p-4 bg-primary-50 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-700">選択中の車両</span>
            <button
              onClick={() => handleViewDetail(selectedVehicle.id)}
              className="text-xs text-primary-600 font-medium hover:underline flex items-center gap-1"
            >
              詳細を見る
              <ChevronRight size={14} />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-900">
              {selectedVehicle.name || `車両 #${selectedVehicle.id}`}
            </span>
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
