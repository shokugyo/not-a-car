import { useCallback, useState } from 'react';
import { Vehicle } from '../types/vehicle';

interface MapCenter {
  latitude: number;
  longitude: number;
  zoom: number;
}

interface UseMapCenterReturn {
  center: MapCenter;
  setCenter: (center: Partial<MapCenter>) => void;
  centerOnVehicle: (vehicle: Vehicle) => void;
  centerOnAllVehicles: (vehicles: Vehicle[]) => void;
  resetCenter: () => void;
}

// Default center: Tokyo
const DEFAULT_CENTER: MapCenter = {
  latitude: 35.6762,
  longitude: 139.6503,
  zoom: 12,
};

export function useMapCenter(): UseMapCenterReturn {
  const [center, setCenterState] = useState<MapCenter>(DEFAULT_CENTER);

  const setCenter = useCallback((newCenter: Partial<MapCenter>) => {
    setCenterState(prev => ({ ...prev, ...newCenter }));
  }, []);

  const centerOnVehicle = useCallback((vehicle: Vehicle) => {
    setCenterState({
      latitude: vehicle.latitude,
      longitude: vehicle.longitude,
      zoom: 15,
    });
  }, []);

  const centerOnAllVehicles = useCallback((vehicles: Vehicle[]) => {
    if (vehicles.length === 0) {
      setCenterState(DEFAULT_CENTER);
      return;
    }

    if (vehicles.length === 1) {
      centerOnVehicle(vehicles[0]);
      return;
    }

    // Calculate bounds center
    const lats = vehicles.map(v => v.latitude);
    const lngs = vehicles.map(v => v.longitude);

    const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;

    // Calculate appropriate zoom based on spread
    const latSpread = Math.max(...lats) - Math.min(...lats);
    const lngSpread = Math.max(...lngs) - Math.min(...lngs);
    const maxSpread = Math.max(latSpread, lngSpread);

    let zoom = 12;
    if (maxSpread < 0.01) zoom = 15;
    else if (maxSpread < 0.05) zoom = 14;
    else if (maxSpread < 0.1) zoom = 13;
    else if (maxSpread < 0.5) zoom = 11;
    else zoom = 10;

    setCenterState({
      latitude: centerLat,
      longitude: centerLng,
      zoom,
    });
  }, [centerOnVehicle]);

  const resetCenter = useCallback(() => {
    setCenterState(DEFAULT_CENTER);
  }, []);

  return {
    center,
    setCenter,
    centerOnVehicle,
    centerOnAllVehicles,
    resetCenter,
  };
}
