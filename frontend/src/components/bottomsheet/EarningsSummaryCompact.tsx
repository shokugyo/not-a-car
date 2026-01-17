import { TrendingUp, Zap } from 'lucide-react';
import { RealtimeEarning } from '../../types/earnings';

interface EarningsSummaryCompactProps {
  earnings: RealtimeEarning[];
  isLoading?: boolean;
}

export function EarningsSummaryCompact({ earnings, isLoading }: EarningsSummaryCompactProps) {
  const totalToday = earnings.reduce((sum, e) => sum + e.today_total, 0);
  const totalHourlyRate = earnings.reduce((sum, e) => sum + e.hourly_rate, 0);
  const activeVehicles = earnings.filter(e => e.status === 'earning').length;
  const totalVehicles = earnings.length;

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-8 bg-gray-200 rounded w-1/3" />
        <div className="flex gap-4">
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="h-4 bg-gray-200 rounded w-1/4" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Main Earnings Display */}
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-gray-500 mb-0.5">本日の収益</p>
          <p className="text-2xl font-bold text-gray-900">
            ¥{totalToday.toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Zap size={12} className="text-amber-500" />
            <span>¥{Math.round(totalHourlyRate).toLocaleString()}/時</span>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1.5 text-gray-600">
          <div className={`w-2 h-2 rounded-full ${activeVehicles > 0 ? 'bg-green-500' : 'bg-gray-300'}`} />
          <span>
            {activeVehicles}/{totalVehicles} 稼働中
          </span>
        </div>
        {activeVehicles > 0 && (
          <div className="flex items-center gap-1.5 text-green-600">
            <TrendingUp size={14} />
            <span>収益発生中</span>
          </div>
        )}
      </div>
    </div>
  );
}
