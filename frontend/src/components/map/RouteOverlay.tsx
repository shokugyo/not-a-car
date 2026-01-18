import { useMemo } from 'react';
import { Polyline, Marker } from 'react-leaflet';
import L from 'leaflet';
import { Route } from '../../types/trip';

interface RouteOverlayProps {
  route: Route;
}

// Default origin: Tokyo Station
const DEFAULT_ORIGIN: [number, number] = [35.6812, 139.7671];

/**
 * Decode Google Polyline encoded string to array of coordinates
 * Based on the algorithm: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
 */
function decodePolyline(encoded: string): [number, number][] {
  const coordinates: [number, number][] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    // Decode latitude
    let shift = 0;
    let result = 0;
    let byte: number;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    const deltaLat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += deltaLat;

    // Decode longitude
    shift = 0;
    result = 0;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    const deltaLng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += deltaLng;

    coordinates.push([lat / 1e5, lng / 1e5]);
  }

  return coordinates;
}

// Create a custom divIcon for waypoint markers
function createWaypointIcon(label: string, color: string): L.DivIcon {
  return L.divIcon({
    className: 'route-waypoint-container',
    html: `
      <div class="route-waypoint-marker" style="background-color: ${color};">
        <span class="route-waypoint-label">${label}</span>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

// Route line style
const POLYLINE_OPTIONS = {
  color: '#3b82f6',
  weight: 4,
  opacity: 0.8,
};

// Marker colors
const ORIGIN_COLOR = '#10b981'; // Green
const WAYPOINT_COLOR = '#3b82f6'; // Blue

export function RouteOverlay({ route }: RouteOverlayProps) {
  // Build positions array from polyline or fallback to straight line
  const positions = useMemo(() => {
    // If we have an encoded polyline, decode it
    if (route.polyline) {
      const decoded = decodePolyline(route.polyline);
      if (decoded.length > 0) {
        return decoded;
      }
    }

    // Fallback: straight line from origin to waypoints
    const coords: [number, number][] = [DEFAULT_ORIGIN];
    route.waypoints.forEach((wp) => {
      coords.push([wp.destination.latitude, wp.destination.longitude]);
    });
    return coords;
  }, [route.polyline, route.waypoints]);

  // Origin marker
  const originIcon = useMemo(() => createWaypointIcon('S', ORIGIN_COLOR), []);

  // Waypoint markers
  const waypointMarkers = useMemo(() => {
    return route.waypoints.map((wp, index) => ({
      position: [wp.destination.latitude, wp.destination.longitude] as [number, number],
      icon: createWaypointIcon(String(index + 1), WAYPOINT_COLOR),
      key: wp.destination.id,
      name: wp.destination.name,
    }));
  }, [route.waypoints]);

  return (
    <>
      {/* Polyline connecting all points (road-following if available) */}
      <Polyline positions={positions} pathOptions={POLYLINE_OPTIONS} />

      {/* Origin marker (starting point) */}
      <Marker position={DEFAULT_ORIGIN} icon={originIcon} />

      {/* Waypoint markers */}
      {waypointMarkers.map((marker) => (
        <Marker
          key={marker.key}
          position={marker.position}
          icon={marker.icon}
        />
      ))}
    </>
  );
}
