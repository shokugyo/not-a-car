import { CheckCircle, Calendar, Clock, MapPin, Car, Route as RouteIcon } from 'lucide-react';
import { useTripStore } from '../../store';

export function TripComplete() {
  const { currentBooking, selectedRoute, resetTrip } = useTripStore();

  const handleNewTrip = () => {
    resetTrip();
  };

  if (!currentBooking || !selectedRoute) {
    return (
      <div className="flex items-center justify-center h-40">
        <p className="text-gray-500">予約情報が見つかりません</p>
      </div>
    );
  }

  const departureDate = new Date(currentBooking.departureTime);
  const formattedDate = departureDate.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  });
  const formattedTime = departureDate.toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const hours = Math.floor(selectedRoute.totalDuration / 60);
  const minutes = selectedRoute.totalDuration % 60;
  const durationText = hours > 0 ? `${hours}時間${minutes > 0 ? `${minutes}分` : ''}` : `${minutes}分`;

  return (
    <div className="space-y-6">
      {/* Success Icon */}
      <div className="text-center pt-4">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle size={32} className="text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900">予約が完了しました</h2>
        <p className="text-sm text-gray-500 mt-1">
          予約番号: {currentBooking.id}
        </p>
      </div>

      {/* Trip Summary Card */}
      <div className="p-4 bg-gray-50 rounded-xl space-y-4">
        {/* Route Name */}
        <div>
          <h3 className="font-bold text-gray-900">{selectedRoute.name}</h3>
          <p className="text-sm text-gray-600">{selectedRoute.description}</p>
        </div>

        {/* Details */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Calendar size={16} className="text-gray-400" />
            <span className="text-gray-700">{formattedDate}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock size={16} className="text-gray-400" />
            <span className="text-gray-700">{formattedTime} 出発</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <RouteIcon size={16} className="text-gray-400" />
            <span className="text-gray-700">{selectedRoute.totalDistance}km</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock size={16} className="text-gray-400" />
            <span className="text-gray-700">{durationText}</span>
          </div>
        </div>

        {/* Waypoints */}
        <div className="border-t border-gray-200 pt-3">
          <div className="flex items-center gap-2 mb-2">
            <MapPin size={14} className="text-gray-400" />
            <span className="text-xs font-medium text-gray-500">立ち寄りスポット</span>
          </div>
          <div className="space-y-1">
            {selectedRoute.waypoints.map((waypoint, index) => (
              <div key={waypoint.destination.id} className="flex items-center gap-2 text-sm">
                <span className="w-5 h-5 bg-primary-100 rounded-full flex items-center justify-center text-xs font-bold text-primary-600">
                  {index + 1}
                </span>
                <span className="text-gray-700">{waypoint.destination.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Vehicle Info */}
        <div className="border-t border-gray-200 pt-3 flex items-center gap-2">
          <Car size={16} className="text-gray-400" />
          <span className="text-sm text-gray-700">
            車両ID: {currentBooking.vehicleId}
          </span>
        </div>
      </div>

      {/* Estimated Cost */}
      <div className="p-4 bg-primary-50 rounded-xl">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700">概算料金</span>
          <span className="text-xl font-bold text-primary-600">
            ¥{selectedRoute.estimatedCost.toLocaleString()}〜
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <button
          onClick={handleNewTrip}
          className="w-full py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 active:bg-primary-800 transition-colors"
        >
          新しい旅程を計画する
        </button>
        <p className="text-xs text-gray-400 text-center">
          出発時刻になりましたら、車両が指定場所に到着します
        </p>
      </div>
    </div>
  );
}
