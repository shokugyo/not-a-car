import { VehicleMode } from './vehicle';

export interface Earning {
  id: number;
  owner_id: number;
  vehicle_id: number;
  amount: number;
  currency: string;
  mode: VehicleMode;
  description: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  platform_fee: number;
  net_amount: number;
  created_at: string;
}

export interface EarningsSummary {
  total_earnings: number;
  total_net_earnings: number;
  total_platform_fees: number;
  earnings_by_mode: Record<string, number>;
  earnings_by_vehicle: Record<number, number>;
  period_start: string | null;
  period_end: string | null;
}

export interface RealtimeEarning {
  vehicle_id: number;
  vehicle_name: string | null;
  current_mode: VehicleMode;
  hourly_rate: number;
  today_total: number;
  active_minutes: number;
  status: 'earning' | 'idle' | 'maintenance';
}

export interface ModeEarnings {
  mode: VehicleMode;
  total_amount: number;
  total_hours: number;
  average_hourly_rate: number;
  transaction_count: number;
}
