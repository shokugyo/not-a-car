export type VehicleMode =
  | 'idle'
  | 'accommodation'
  | 'delivery'
  | 'rideshare'
  | 'maintenance'
  | 'charging'
  | 'transit';

export type InteriorMode =
  | 'standard'
  | 'bed'
  | 'cargo'
  | 'office'
  | 'passenger';

export interface Vehicle {
  id: number;
  owner_id: number;
  name: string | null;
  license_plate: string;
  model: string | null;
  year: number | null;
  vin: string | null;
  current_mode: VehicleMode;
  interior_mode: InteriorMode;
  is_active: boolean;
  is_available: boolean;
  latitude: number;
  longitude: number;
  battery_level: number;
  range_km: number;
  allowed_modes: string[];
  auto_mode_switch: boolean;
  current_hourly_rate: number;
  today_earnings: number;
  created_at: string;
  updated_at: string;
}

export interface VehicleStatus {
  id: number;
  name: string | null;
  current_mode: VehicleMode;
  interior_mode: InteriorMode;
  is_available: boolean;
  latitude: number;
  longitude: number;
  battery_level: number;
  range_km: number;
  current_hourly_rate: number;
  today_earnings: number;
  mode_started_at: string | null;
  active_duration_minutes: number | null;
}

export interface VehicleCreate {
  name?: string;
  license_plate: string;
  model?: string;
  year?: number;
  vin?: string;
  allowed_modes?: string[];
  auto_mode_switch?: boolean;
}

export interface ModeChange {
  mode: VehicleMode;
  force?: boolean;
}
