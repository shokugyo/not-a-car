import { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Vehicle, VehicleMode } from '../../types/vehicle';
import { VehicleMarker } from './VehicleMarker';
import { VehiclePopup } from './VehiclePopup';

interface MapViewProps {
  vehicles: Vehicle[];
  selectedVehicleId: number | null;
  onVehicleSelect: (vehicle: Vehicle | null) => void;
  onModeChange: (vehicleId: number, mode: VehicleMode) => void;
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

function MapController({ vehicles, selectedVehicleId }: { vehicles: Vehicle[]; selectedVehicleId: number | null }) {
  const map = useMap();

  useEffect(() => {
    if (vehicles.length === 0) return;

    if (selectedVehicleId) {
      const vehicle = vehicles.find(v => v.id === selectedVehicleId);
      if (vehicle) {
        map.flyTo([vehicle.latitude, vehicle.longitude], 15, { duration: 0.5 });
      }
    } else {
      // Fit bounds to all vehicles
      const bounds = L.latLngBounds(
        vehicles.map(v => [v.latitude, v.longitude] as [number, number])
      );
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [vehicles.length, selectedVehicleId]);

  return null;
}

export function MapView({
  vehicles,
  selectedVehicleId,
  onVehicleSelect,
  onModeChange,
}: MapViewProps) {
  const selectedVehicle = vehicles.find(v => v.id === selectedVehicleId);

  const handleVehicleClick = (vehicle: Vehicle) => {
    onVehicleSelect(vehicle.id === selectedVehicleId ? null : vehicle);
  };

  const handlePopupClose = () => {
    onVehicleSelect(null);
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

      <MapController vehicles={vehicles} selectedVehicleId={selectedVehicleId} />

      {vehicles.map((vehicle) => (
        <VehicleMarker
          key={vehicle.id}
          vehicle={vehicle}
          isSelected={vehicle.id === selectedVehicleId}
          onClick={handleVehicleClick}
        />
      ))}

      {selectedVehicle && (
        <VehiclePopup
          vehicle={selectedVehicle}
          onModeChange={onModeChange}
          onClose={handlePopupClose}
        />
      )}
    </MapContainer>
  );
}
