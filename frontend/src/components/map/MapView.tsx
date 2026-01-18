import { useEffect } from 'react';
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Vehicle, VehicleMode } from '../../types/vehicle';
import { Route } from '../../types/trip';
import { VehicleMarker } from './VehicleMarker';
import { VehiclePopup } from './VehiclePopup';
import { RouteOverlay } from './RouteOverlay';

interface MapViewProps {
  vehicles: Vehicle[];
  selectedVehicleId: number | null;
  onVehicleSelect: (vehicle: Vehicle | null) => void;
  onModeChange: (vehicleId: number, mode: VehicleMode) => void;
  selectedRoute?: Route | null;
}

// Default center: Tokyo Station
const DEFAULT_CENTER: [number, number] = [35.6812, 139.7671];
const DEFAULT_ZOOM = 14;

// Fix for default marker icons in Leaflet with webpack/vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function MapController({
  vehicles,
  selectedVehicleId,
  selectedRoute,
  onMapClick,
}: {
  vehicles: Vehicle[];
  selectedVehicleId: number | null;
  selectedRoute: Route | null;
  onMapClick: () => void;
}) {
  const map = useMap();

  // Handle map click to deselect vehicle
  useMapEvents({
    click: () => {
      onMapClick();
    },
  });

  // Helper: fly to a point with vertical offset (to account for bottom UI)
  // Offset the target southward so the actual point appears in upper portion of visible map
  const flyToWithOffset = (lat: number, lng: number, zoom: number) => {
    // Calculate offset based on zoom level (higher zoom = smaller offset in degrees)
    // At zoom 16, roughly 0.002 degrees ≈ 200m offset
    const offsetFactor = 0.003 / Math.pow(2, zoom - 14);
    const offsetLat = lat - offsetFactor;
    map.flyTo([offsetLat, lng], zoom, { duration: 0.5 });
  };

  useEffect(() => {
    // When route is displayed
    if (selectedRoute) {
      if (selectedVehicleId) {
        // Vehicle selected: zoom to that vehicle (offset for bottom UI)
        const vehicle = vehicles.find(v => v.id === selectedVehicleId);
        if (vehicle) {
          flyToWithOffset(vehicle.latitude, vehicle.longitude, 16);
        }
      } else {
        // No vehicle selected: fit to entire route with more bottom padding
        const routePositions: [number, number][] = [[35.6812, 139.7671]]; // Default origin
        selectedRoute.waypoints.forEach((wp) => {
          routePositions.push([wp.destination.latitude, wp.destination.longitude]);
        });
        if (routePositions.length >= 2) {
          const bounds = L.latLngBounds(routePositions);
          // Asymmetric padding: more on bottom to account for bottom sheet
          map.fitBounds(bounds, {
            paddingTopLeft: [40, 40],
            paddingBottomRight: [40, 200], // Extra padding at bottom
            maxZoom: 14,
            animate: true,
            duration: 0.5,
          });
        }
      }
      return;
    }

    // Normal mode (no route)
    if (vehicles.length === 0) return;

    if (selectedVehicleId) {
      // Vehicle selected: zoom with offset
      const vehicle = vehicles.find(v => v.id === selectedVehicleId);
      if (vehicle) {
        flyToWithOffset(vehicle.latitude, vehicle.longitude, 15);
      }
    } else {
      // Fit bounds to all vehicles with bottom padding
      const bounds = L.latLngBounds(
        vehicles.map(v => [v.latitude, v.longitude] as [number, number])
      );
      map.fitBounds(bounds, {
        paddingTopLeft: [40, 40],
        paddingBottomRight: [40, 150],
        maxZoom: 14,
      });
    }
  }, [vehicles.length, selectedVehicleId, selectedRoute, map]);

  return null;
}

export function MapView({
  vehicles,
  selectedVehicleId,
  onVehicleSelect,
  onModeChange: _onModeChange,
  selectedRoute,
}: MapViewProps) {
  // onModeChange is passed for interface compatibility but mode changes are handled in bottom sheet
  void _onModeChange;

  const selectedVehicle = vehicles.find(v => v.id === selectedVehicleId);

  const handleVehicleClick = (vehicle: Vehicle) => {
    onVehicleSelect(vehicle.id === selectedVehicleId ? null : vehicle);
  };

  const handleMapClick = () => {
    // Deselect vehicle when clicking on empty map area
    if (selectedVehicleId) {
      onVehicleSelect(null);
    }
  };

  // Calculate initial center
  const initialCenter: [number, number] = vehicles.length > 0
    ? [
        vehicles.reduce((sum, v) => sum + v.latitude, 0) / vehicles.length,
        vehicles.reduce((sum, v) => sum + v.longitude, 0) / vehicles.length,
      ]
    : DEFAULT_CENTER;

  return (
    <MapContainer
      center={initialCenter}
      zoom={DEFAULT_ZOOM}
      className="w-full h-full"
      zoomControl={false}
      attributionControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapController vehicles={vehicles} selectedVehicleId={selectedVehicleId} selectedRoute={selectedRoute || null} onMapClick={handleMapClick} />

      {vehicles.map((vehicle) => (
        <VehicleMarker
          key={vehicle.id}
          vehicle={vehicle}
          isSelected={vehicle.id === selectedVehicleId}
          onClick={handleVehicleClick}
        />
      ))}

      {selectedVehicle && (
        <VehiclePopup vehicle={selectedVehicle} />
      )}

      {selectedRoute && <RouteOverlay route={selectedRoute} />}
    </MapContainer>
  );
}
