import React from 'react';
import { Bed, Package, Car, Pause, Wrench, Battery, ArrowRight } from 'lucide-react';
import { VehicleMode } from '../../types/vehicle';

interface ModeIndicatorProps {
  mode: VehicleMode;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const modeConfig: Record<VehicleMode, {
  icon: React.ElementType;
  label: string;
  labelJa: string;
  color: string;
  bgColor: string;
}> = {
  idle: {
    icon: Pause,
    label: 'Idle',
    labelJa: '待機中',
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
  },
  accommodation: {
    icon: Bed,
    label: 'Accommodation',
    labelJa: '宿泊',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  delivery: {
    icon: Package,
    label: 'Delivery',
    labelJa: '配送',
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
  },
  rideshare: {
    icon: Car,
    label: 'Rideshare',
    labelJa: 'ライドシェア',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  maintenance: {
    icon: Wrench,
    label: 'Maintenance',
    labelJa: 'メンテナンス',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
  },
  charging: {
    icon: Battery,
    label: 'Charging',
    labelJa: '充電中',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  transit: {
    icon: ArrowRight,
    label: 'In Transit',
    labelJa: '回送中',
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-100',
  },
};

const sizeStyles = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
  lg: 'text-base px-3 py-1.5',
};

const iconSizes = {
  sm: 12,
  md: 16,
  lg: 20,
};

export function ModeIndicator({ mode, size = 'md', showLabel = true }: ModeIndicatorProps) {
  const config = modeConfig[mode] || modeConfig.idle;
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${config.bgColor} ${config.color} ${sizeStyles[size]}`}
    >
      <Icon size={iconSizes[size]} />
      {showLabel && <span>{config.labelJa}</span>}
    </span>
  );
}

export function getModeLabel(mode: VehicleMode): string {
  return modeConfig[mode]?.labelJa || mode;
}
