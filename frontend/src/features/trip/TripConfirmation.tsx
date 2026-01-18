import { ChevronLeft, Clock, MapPin, Route as RouteIcon, Loader2 } from 'lucide-react';
import { useTripStore } from '../../store';

export function TripConfirmation() {
  const {
    selectedRoute,
    setStep,
    fetchAvailableVehicles,
    isFetchingVehicles,
    error,
  } = useTripStore();

  const handleBack = () => {
    setStep('plan');
  };

  const handleProceed = async () => {
    if (!selectedRoute) return;
    // デフォルトで1時間後を出発時刻として使用（将来的にLLMで設定予定）
    const departureDateTime = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    await fetchAvailableVehicles(selectedRoute.id, departureDateTime);
  };

  if (!selectedRoute) {
    return (
      <div className="flex items-center justify-center h-40">
        <p className="text-gray-500">ルートが選択されていません</p>
      </div>
    );
  }

  const hours = Math.floor(selectedRoute.totalDuration / 60);
  const minutes = selectedRoute.totalDuration % 60;
  const durationText = hours > 0 ? `${hours}時間${minutes > 0 ? `${minutes}分` : ''}` : `${minutes}分`;

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
          <h2 className="text-lg font-bold text-gray-900">旅程の確認</h2>
          <p className="text-xs text-gray-500">ルート内容を確認してください</p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      {/* Route Summary */}
      <div className="p-4 bg-gray-50 rounded-xl">
        <h3 className="font-bold text-gray-900 mb-2">{selectedRoute.name}</h3>
        <p className="text-sm text-gray-600 mb-3">{selectedRoute.description}</p>

        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Clock size={16} className="text-gray-400" />
            <span>{durationText}</span>
          </div>
          <div className="flex items-center gap-1">
            <RouteIcon size={16} className="text-gray-400" />
            <span>{selectedRoute.totalDistance}km</span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin size={16} className="text-gray-400" />
            <span>{selectedRoute.waypoints.length}スポット</span>
          </div>
        </div>
      </div>

      {/* Waypoints */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">立ち寄りスポット</h4>
        <div className="space-y-2">
          {selectedRoute.waypoints.map((waypoint, index) => (
            <div
              key={waypoint.destination.id}
              className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg"
            >
              <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center text-xs font-bold text-primary-600">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {waypoint.destination.name}
                </p>
                {waypoint.stayDuration && (
                  <p className="text-xs text-gray-500">
                    滞在: {waypoint.stayDuration}分
                  </p>
                )}
              </div>
            </div>
          ))}
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
        <p className="text-xs text-gray-500 mt-1">
          ※車両タイプにより料金が変動します
        </p>
      </div>

      {/* Proceed Button */}
      <button
        onClick={handleProceed}
        disabled={isFetchingVehicles}
        className="w-full py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 active:bg-primary-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isFetchingVehicles ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            車両を検索中...
          </>
        ) : (
          '車両を選択する'
        )}
      </button>
    </div>
  );
}
