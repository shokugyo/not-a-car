import React from 'react';
import { TrendingUp, Clock } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { ModeIndicator } from '../../components/vehicle/ModeIndicator';
import { RealtimeEarning } from '../../types/earnings';

interface EarningsWidgetProps {
  earnings: RealtimeEarning[];
  isLoading?: boolean;
}

export function EarningsWidget({ earnings, isLoading }: EarningsWidgetProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}時間${mins}分`;
    }
    return `${mins}分`;
  };

  const totalToday = earnings.reduce((sum, e) => sum + e.today_total, 0);
  const activeVehicles = earnings.filter((e) => e.status === 'earning').length;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>リアルタイム収益</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="text-green-500" size={20} />
          リアルタイム収益
        </CardTitle>
        <span className="text-sm text-gray-500">
          {activeVehicles}/{earnings.length} 台稼働中
        </span>
      </CardHeader>

      <CardContent>
        {/* Total Today */}
        <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-1">本日の合計収益</p>
          <p className="text-3xl font-bold text-green-600">
            {formatCurrency(totalToday)}
          </p>
        </div>

        {/* Per Vehicle */}
        <div className="space-y-4">
          {earnings.map((earning) => (
            <div
              key={earning.vehicle_id}
              className={`p-4 rounded-lg border ${
                earning.status === 'earning'
                  ? 'border-green-200 bg-green-50'
                  : 'border-gray-200 bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">
                  {earning.vehicle_name || `車両 #${earning.vehicle_id}`}
                </span>
                <ModeIndicator mode={earning.current_mode} size="sm" />
              </div>

              {earning.status === 'earning' ? (
                <>
                  <p className="text-lg font-semibold text-green-600 mb-1">
                    時給 {formatCurrency(earning.hourly_rate)}
                  </p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock size={14} />
                      稼働 {formatDuration(earning.active_minutes)}
                    </span>
                    <span>本日 {formatCurrency(earning.today_total)}</span>
                  </div>
                </>
              ) : (
                <p className="text-sm text-gray-500">
                  {earning.status === 'maintenance' ? 'メンテナンス中' : '待機中'}
                </p>
              )}
            </div>
          ))}

          {earnings.length === 0 && (
            <p className="text-center text-gray-500 py-4">
              車両が登録されていません
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
