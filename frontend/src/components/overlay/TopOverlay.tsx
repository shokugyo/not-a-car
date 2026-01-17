import { Car, RefreshCw } from 'lucide-react';
import { RealtimeEarning } from '../../types/earnings';

interface TopOverlayProps {
  earnings: RealtimeEarning[];
  onRefresh: () => void;
  isRefreshing: boolean;
}

export function TopOverlay({ earnings, onRefresh, isRefreshing }: TopOverlayProps) {
  const totalToday = earnings.reduce((sum, e) => sum + e.today_total, 0);
  const activeVehicles = earnings.filter(e => e.status === 'earning').length;
  const totalVehicles = earnings.length;

  return (
    <div
      className="fixed top-0 left-0 right-0"
      style={{ paddingTop: 'env(safe-area-inset-top)', zIndex: 1000 }}
    >
      <div className="mx-3 mt-3">
        <div className="flex items-center justify-between px-4 py-3 bg-white/95 backdrop-blur-md rounded-2xl shadow-lg">
          {/* Logo and Earnings */}
          <div className="flex items-center gap-3">
            {/* Logo */}
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-sm">M</span>
            </div>

            {/* Earnings */}
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-bold text-gray-900">
                ¥{totalToday.toLocaleString()}
              </span>
              <span className="text-xs text-gray-500">本日</span>
            </div>
          </div>

          {/* Right Side */}
          <div className="flex items-center gap-3">
            {/* Active Vehicles Badge */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 rounded-full">
              <Car size={14} className="text-gray-600" />
              <span className="text-sm font-medium text-gray-700">
                {activeVehicles}/{totalVehicles}
              </span>
              {activeVehicles > 0 && (
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              )}
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200 transition-colors disabled:opacity-50"
            >
              <RefreshCw
                size={18}
                className={`text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
