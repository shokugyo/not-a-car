// Trip planning types for user-side mode

export type TripStep = 'search' | 'plan' | 'confirm' | 'vehicle' | 'complete';

export type AppMode = 'owner' | 'user';

// Destination search
export interface Destination {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  category?: string;
  estimatedDuration?: number; // minutes
}

export interface DestinationSearchRequest {
  query: string;
  latitude?: number;
  longitude?: number;
}

export interface DestinationSearchResponse {
  destinations: Destination[];
}

// Route suggestion
export interface RouteWaypoint {
  destination: Destination;
  arrivalTime?: string;
  departureTime?: string;
  stayDuration?: number; // minutes
}

export interface Route {
  id: string;
  name: string;
  description: string;
  waypoints: RouteWaypoint[];
  totalDuration: number; // minutes
  totalDistance: number; // km
  estimatedCost: number; // yen
  highlights: string[];
  vehicleTypes: string[]; // recommended vehicle types
  polyline?: string; // Encoded polyline for map display
}

export interface RoutingRequest {
  query: string;
  origin?: {
    latitude: number;
    longitude: number;
  };
  desired_arrival?: string; // ISO format datetime
  preferences?: string[];
}

export interface LLMStepMetadata {
  step_name: string;
  model_name: string;
  duration_ms: number;
  provider: string;
}

export interface ProcessingMetadata {
  total_duration_ms: number;
  steps: LLMStepMetadata[];
  reasoning_steps: string[];
}

export interface RouteSuggestionResponse {
  routes: Route[];
  query: string;
  generatedAt: string;
  processing?: ProcessingMetadata;
}

// Trip booking
export interface TripBooking {
  id: string;
  route: Route;
  vehicleId: number;
  departureTime: string;
  status: 'pending' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled';
  createdAt: string;
}

export interface TripBookingRequest {
  routeId: string;
  vehicleId: number;
  departureTime: string;
}

export interface TripBookingResponse {
  booking: TripBooking;
}

// Available vehicles for trip
export interface TripVehicle {
  id: number;
  name: string | null;
  model: string | null;
  currentMode: string;
  latitude: number;
  longitude: number;
  batteryLevel: number;
  rangeKm: number;
  hourlyRate: number;
  estimatedPickupTime: number; // minutes
  features: string[];
}

export interface AvailableVehiclesRequest {
  routeId: string;
  departureTime: string;
}

export interface AvailableVehiclesResponse {
  vehicles: TripVehicle[];
}

// Streaming types
export type StreamEventType =
  | 'step_start'
  | 'thinking'
  | 'token'
  | 'step_complete'
  | 'routes'
  | 'done'
  | 'error';

export interface StreamEvent {
  event: StreamEventType;
  step_name?: string;
  step_index?: number;
  content?: string;
  data?: Record<string, unknown>;
}

export interface StreamingStep {
  name: string;
  index: number;
  status: 'pending' | 'active' | 'completed';
  thinkingContent: string;
}

export interface StreamingState {
  isStreaming: boolean;
  currentStepIndex: number | null;
  steps: StreamingStep[];
  error: string | null;
}
