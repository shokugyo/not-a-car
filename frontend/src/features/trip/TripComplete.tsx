import { useState, useEffect } from 'react';
import {
  Car,
  MapPin,
  Clock,
  Calendar,
  Route as RouteIcon,
  Navigation,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { useTripStore } from '../../store';

type WaitingPhase = 'dispatched' | 'approaching' | 'arriving' | 'arrived';

export function TripComplete() {
  const { currentBooking, selectedRoute, availableVehicles, resetTrip } = useTripStore();

  // デモ用: 到着までのカウントダウンと状態遷移（秒単位で管理）
  const [phase, setPhase] = useState<WaitingPhase>('dispatched');
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);
  const [progress, setProgress] = useState(0);

  const selectedVehicle = availableVehicles.find(v => v.id === currentBooking?.vehicleId);
  const initialPickupMinutes = selectedVehicle?.estimatedPickupTime || 5;
  const initialPickupSeconds = initialPickupMinutes * 60;

  // 表示用の分数（切り上げ）
  const remainingMinutes = Math.ceil(remainingSeconds / 60);

  useEffect(() => {
    // 初期設定（秒単位）
    setRemainingSeconds(initialPickupSeconds);
    setProgress(0);

    // デモ用: 1秒ごとに5秒進む（12秒で1分減る）
    const interval = setInterval(() => {
      setRemainingSeconds(prev => {
        const next = Math.max(0, prev - 5);

        // 進捗更新
        const newProgress = Math.min(100, ((initialPickupSeconds - next) / initialPickupSeconds) * 100);
        setProgress(newProgress);

        // フェーズ更新（秒単位で判定）
        if (next <= 0) {
          setPhase('arrived');
          clearInterval(interval);
          return 0;
        } else if (next <= 60) {
          setPhase('arriving');
        } else if (next <= initialPickupSeconds / 2) {
          setPhase('approaching');
        }

        return next;
      });
    }, 1000); // 1秒ごとに5秒分進む

    return () => clearInterval(interval);
  }, [initialPickupSeconds]);

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
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  });
  const formattedTime = departureDate.toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const getPhaseInfo = () => {
    switch (phase) {
      case 'dispatched':
        return {
          title: '車両が出発しました',
          description: 'お迎えに向かっています',
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          pulseColor: 'bg-blue-400',
        };
      case 'approaching':
        return {
          title: '車両が接近中',
          description: 'もうすぐ到着します',
          color: 'text-amber-600',
          bgColor: 'bg-amber-100',
          pulseColor: 'bg-amber-400',
        };
      case 'arriving':
        return {
          title: 'まもなく到着',
          description: '外に出る準備をしてください',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          pulseColor: 'bg-green-400',
        };
      case 'arrived':
        return {
          title: '車両が到着しました',
          description: '乗車してください',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          pulseColor: 'bg-green-400',
        };
    }
  };

  const phaseInfo = getPhaseInfo();

  return (
    <div className="space-y-4">
      {/* Status Header */}
      <div className="text-center pt-2">
        <div className={`relative w-20 h-20 ${phaseInfo.bgColor} rounded-full flex items-center justify-center mx-auto mb-3`}>
          {/* Pulse animation */}
          {phase !== 'arrived' && (
            <div className={`absolute inset-0 ${phaseInfo.pulseColor} rounded-full animate-ping opacity-30`} />
          )}
          {phase === 'arrived' ? (
            <CheckCircle size={40} className={phaseInfo.color} />
          ) : (
            <Car size={40} className={phaseInfo.color} />
          )}
        </div>
        <h2 className={`text-xl font-bold ${phaseInfo.color}`}>
          {phaseInfo.title}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {phaseInfo.description}
        </p>
      </div>

      {/* Arrival Countdown */}
      {phase !== 'arrived' ? (
        <div className="p-4 bg-gray-50 rounded-xl">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Clock size={18} className="text-gray-500" />
              <span className="text-sm text-gray-600">到着まで</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold text-gray-900">{remainingMinutes}</span>
              <span className="text-sm text-gray-500">分</span>
            </div>
          </div>
          {/* Progress bar */}
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-1000 ${
                phase === 'arriving' ? 'bg-green-500' :
                phase === 'approaching' ? 'bg-amber-500' : 'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : (
        <div className="p-4 bg-green-50 rounded-xl border border-green-200">
          <div className="flex items-center gap-3">
            <Navigation size={24} className="text-green-600" />
            <div>
              <p className="font-medium text-green-800">車両が待機中です</p>
              <p className="text-sm text-green-600">
                {selectedVehicle?.name || `車両 #${currentBooking.vehicleId}`} をご確認ください
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Booking Info Card */}
      <div className="p-4 bg-white border border-gray-200 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">予約番号</span>
          <span className="text-sm font-mono font-medium text-gray-700">{currentBooking.id}</span>
        </div>

        <div className="border-t border-gray-100 pt-3">
          <h3 className="font-bold text-gray-900 mb-1">{selectedRoute.name}</h3>
          <p className="text-xs text-gray-500">{selectedRoute.description}</p>
        </div>

        {/* Trip Details */}
        <div className="grid grid-cols-2 gap-2 pt-2">
          <div className="flex items-center gap-2 text-sm">
            <Calendar size={14} className="text-gray-400" />
            <span className="text-gray-700">{formattedDate}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock size={14} className="text-gray-400" />
            <span className="text-gray-700">{formattedTime}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <RouteIcon size={14} className="text-gray-400" />
            <span className="text-gray-700">{selectedRoute.totalDistance}km</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Car size={14} className="text-gray-400" />
            <span className="text-gray-700">{selectedVehicle?.name || `車両 #${currentBooking.vehicleId}`}</span>
          </div>
        </div>

        {/* Waypoints */}
        <div className="border-t border-gray-100 pt-3">
          <div className="flex items-center gap-2 mb-2">
            <MapPin size={14} className="text-gray-400" />
            <span className="text-xs font-medium text-gray-500">目的地</span>
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
      </div>

      {/* Estimated Cost */}
      <div className="p-3 bg-primary-50 rounded-xl">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700">概算料金</span>
          <span className="text-lg font-bold text-primary-600">
            ¥{selectedRoute.estimatedCost.toLocaleString()}〜
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-2 pt-2">
        {phase === 'arrived' && (
          <button
            onClick={handleNewTrip}
            className="w-full py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 active:bg-primary-800 transition-colors flex items-center justify-center gap-2"
          >
            <RefreshCw size={18} />
            新しい旅程を計画する
          </button>
        )}
        <p className="text-xs text-gray-400 text-center">
          {phase !== 'arrived'
            ? '車両の現在地は地図上でも確認できます'
            : 'ご乗車ありがとうございます'}
        </p>
      </div>
    </div>
  );
}
