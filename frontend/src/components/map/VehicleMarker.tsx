import React, { useMemo } from 'react';
import { Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Bed, Package, Car, Pause, Wrench, Battery, ArrowRight } from 'lucide-react';
import { renderToString } from 'react-dom/server';
import { Vehicle, VehicleMode } from '../../types/vehicle';

interface VehicleMarkerProps {
  vehicle: Vehicle;
  isSelected: boolean;
  onClick: (vehicle: Vehicle) => void;
}

const modeConfig: Record<VehicleMode, {
  icon: React.ElementType;
  color: string;
  markerClass: string;
}> = {
  idle: {
    icon: Pause,
    color: '#6b7280',
    markerClass: 'vehicle-marker-idle',
  },
  accommodation: {
    icon: Bed,
    color: '#9333ea',
    markerClass: 'vehicle-marker-accommodation',
  },
  delivery: {
    icon: Package,
    color: '#d97706',
    markerClass: 'vehicle-marker-delivery',
  },
  rideshare: {
    icon: Car,
    color: '#2563eb',
    markerClass: 'vehicle-marker-rideshare',
  },
  maintenance: {
    icon: Wrench,
    color: '#ea580c',
    markerClass: 'vehicle-marker-maintenance',
  },
  charging: {
    icon: Battery,
    color: '#16a34a',
    markerClass: 'vehicle-marker-charging',
  },
  transit: {
    icon: ArrowRight,
    color: '#0891b2',
    markerClass: 'vehicle-marker-transit',
  },
};

export function VehicleMarker({ vehicle, isSelected, onClick }: VehicleMarkerProps) {
  const map = useMap();
  const config = modeConfig[vehicle.current_mode] || modeConfig.idle;
  const Icon = config.icon;

  const icon = useMemo(() => {
    const iconHtml = renderToString(
      <Icon size={22} color="white" strokeWidth={2.5} />
    );

    const html = `
      <div class="vehicle-marker ${config.markerClass} ${isSelected ? 'selected' : ''}" style="color: ${config.color}; background-color: ${config.color};">
        ${iconHtml}
        ${isSelected ? '<div class="vehicle-marker-ring"></div>' : ''}
      </div>
    `;

    return L.divIcon({
      html,
      className: 'vehicle-marker-container',
      iconSize: [48, 48],
      iconAnchor: [24, 24],
    });
  }, [vehicle.current_mode, isSelected, config]);

  const handleClick = () => {
    onClick(vehicle);
    map.flyTo([vehicle.latitude, vehicle.longitude], 15, {
      duration: 0.5,
    });
  };

  return (
    <Marker
      position={[vehicle.latitude, vehicle.longitude]}
      icon={icon}
      eventHandlers={{
        click: handleClick,
      }}
    />
  );
}

export { modeConfig };
