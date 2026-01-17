import { create } from 'zustand';
import { Owner } from '../types/api';
import { Vehicle, VehicleStatus } from '../types/vehicle';
import { RealtimeEarning, EarningsSummary } from '../types/earnings';
import { YieldPrediction } from '../types/yield';
import {
  AppMode,
  TripStep,
  Destination,
  Route,
  RouteSuggestionResponse,
  TripVehicle,
  TripBooking,
} from '../types/trip';
import api from '../api/client';

// UI State Store
type SnapPoint = 0 | 1 | 2 | 3;

interface UIState {
  selectedVehicleId: number | null;
  bottomSheetSnap: SnapPoint;
  isDetailMode: boolean;
  appMode: AppMode;
  setSelectedVehicleId: (id: number | null) => void;
  setBottomSheetSnap: (snap: SnapPoint) => void;
  setDetailMode: (isDetail: boolean) => void;
  setAppMode: (mode: AppMode) => void;
  openVehicleDetail: (vehicleId: number) => void;
  closeVehicleDetail: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedVehicleId: null,
  bottomSheetSnap: 0,
  isDetailMode: false,
  appMode: 'owner',

  setSelectedVehicleId: (id: number | null) => {
    set({ selectedVehicleId: id });
  },

  setBottomSheetSnap: (snap: SnapPoint) => {
    set({ bottomSheetSnap: snap });
  },

  setDetailMode: (isDetail: boolean) => {
    set({ isDetailMode: isDetail });
  },

  setAppMode: (mode: AppMode) => {
    set({ appMode: mode, bottomSheetSnap: 1, isDetailMode: false });
  },

  openVehicleDetail: (vehicleId: number) => {
    set({
      selectedVehicleId: vehicleId,
      isDetailMode: true,
      bottomSheetSnap: 3,
    });
  },

  closeVehicleDetail: () => {
    set({
      isDetailMode: false,
      bottomSheetSnap: 1,
    });
  },
}));

interface AuthState {
  owner: Owner | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  owner: null,
  isAuthenticated: api.isAuthenticated(),
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      await api.login(email, password);
      const owner = await api.getMe();
      set({ owner, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    api.logout();
    set({ owner: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    if (!api.isAuthenticated()) {
      set({ isAuthenticated: false, owner: null });
      return;
    }
    try {
      const owner = await api.getMe();
      set({ owner, isAuthenticated: true });
    } catch {
      api.logout();
      set({ isAuthenticated: false, owner: null });
    }
  },
}));

interface VehicleState {
  vehicles: Vehicle[];
  selectedVehicle: Vehicle | null;
  vehicleStatus: VehicleStatus | null;
  isLoading: boolean;
  fetchVehicles: () => Promise<void>;
  fetchVehicleStatus: (id: number) => Promise<void>;
  selectVehicle: (vehicle: Vehicle | null) => void;
  changeMode: (vehicleId: number, mode: string) => Promise<void>;
}

export const useVehicleStore = create<VehicleState>((set, get) => ({
  vehicles: [],
  selectedVehicle: null,
  vehicleStatus: null,
  isLoading: false,

  fetchVehicles: async () => {
    set({ isLoading: true });
    try {
      const vehicles = await api.getVehicles();
      set({ vehicles, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  fetchVehicleStatus: async (id: number) => {
    try {
      const status = await api.getVehicleStatus(id);
      set({ vehicleStatus: status });
    } catch (error) {
      console.error('Failed to fetch vehicle status:', error);
    }
  },

  selectVehicle: (vehicle: Vehicle | null) => {
    set({ selectedVehicle: vehicle });
  },

  changeMode: async (vehicleId: number, mode: string) => {
    try {
      const updated = await api.changeVehicleMode(vehicleId, mode);
      const vehicles = get().vehicles.map((v) =>
        v.id === vehicleId ? updated : v
      );
      set({ vehicles });
      if (get().selectedVehicle?.id === vehicleId) {
        set({ selectedVehicle: updated });
      }
    } catch (error) {
      throw error;
    }
  },
}));

interface EarningsState {
  summary: EarningsSummary | null;
  realtimeEarnings: RealtimeEarning[];
  isLoading: boolean;
  fetchSummary: () => Promise<void>;
  fetchRealtimeEarnings: () => Promise<void>;
}

export const useEarningsStore = create<EarningsState>((set) => ({
  summary: null,
  realtimeEarnings: [],
  isLoading: false,

  fetchSummary: async () => {
    set({ isLoading: true });
    try {
      const summary = await api.getEarningsSummary();
      set({ summary, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  fetchRealtimeEarnings: async () => {
    try {
      const realtimeEarnings = await api.getRealtimeEarnings();
      set({ realtimeEarnings });
    } catch (error) {
      console.error('Failed to fetch realtime earnings:', error);
    }
  },
}));

interface YieldState {
  predictions: Record<number, YieldPrediction>;
  isLoading: boolean;
  fetchPrediction: (vehicleId: number) => Promise<YieldPrediction>;
}

export const useYieldStore = create<YieldState>((set, get) => ({
  predictions: {},
  isLoading: false,

  fetchPrediction: async (vehicleId: number) => {
    set({ isLoading: true });
    try {
      const prediction = await api.getYieldPrediction(vehicleId);
      set({
        predictions: { ...get().predictions, [vehicleId]: prediction },
        isLoading: false,
      });
      return prediction;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
}));

// Trip State Store (User-side)
interface TripState {
  currentStep: TripStep;
  searchQuery: string;
  destinations: Destination[];
  selectedDestination: Destination | null;
  routeSuggestion: RouteSuggestionResponse | null;
  selectedRoute: Route | null;
  availableVehicles: TripVehicle[];
  selectedTripVehicleId: number | null;
  departureTime: string | null;
  currentBooking: TripBooking | null;
  isSearching: boolean;
  isFetchingRoute: boolean;
  isFetchingVehicles: boolean;
  isBooking: boolean;
  error: string | null;

  // Actions
  setSearchQuery: (query: string) => void;
  searchDestinations: (query: string) => Promise<void>;
  selectDestination: (destination: Destination | null) => void;
  suggestRoutes: (query: string) => Promise<void>;
  selectRoute: (route: Route | null) => void;
  fetchAvailableVehicles: (routeId: string, departureTime: string) => Promise<void>;
  selectTripVehicle: (vehicleId: number | null) => void;
  setDepartureTime: (time: string | null) => void;
  createBooking: () => Promise<void>;
  setStep: (step: TripStep) => void;
  resetTrip: () => void;
  clearError: () => void;
}

export const useTripStore = create<TripState>((set, get) => ({
  currentStep: 'search',
  searchQuery: '',
  destinations: [],
  selectedDestination: null,
  routeSuggestion: null,
  selectedRoute: null,
  availableVehicles: [],
  selectedTripVehicleId: null,
  departureTime: null,
  currentBooking: null,
  isSearching: false,
  isFetchingRoute: false,
  isFetchingVehicles: false,
  isBooking: false,
  error: null,

  setSearchQuery: (query: string) => {
    set({ searchQuery: query });
  },

  searchDestinations: async (query: string) => {
    set({ isSearching: true, error: null });
    try {
      const response = await api.searchDestinations({ query });
      set({ destinations: response.destinations, isSearching: false });
    } catch (error) {
      set({
        error: '目的地の検索に失敗しました',
        isSearching: false,
      });
    }
  },

  selectDestination: (destination: Destination | null) => {
    set({ selectedDestination: destination });
  },

  suggestRoutes: async (query: string) => {
    set({ isFetchingRoute: true, error: null });
    try {
      const response = await api.suggestRoutes({ query });
      set({
        routeSuggestion: response,
        isFetchingRoute: false,
        currentStep: 'plan',
      });
    } catch (error) {
      set({
        error: 'ルートの取得に失敗しました',
        isFetchingRoute: false,
      });
    }
  },

  selectRoute: (route: Route | null) => {
    set({ selectedRoute: route });
    if (route) {
      set({ currentStep: 'confirm' });
    }
  },

  fetchAvailableVehicles: async (routeId: string, departureTime: string) => {
    set({ isFetchingVehicles: true, error: null, departureTime });
    try {
      const response = await api.getAvailableVehicles({ routeId, departureTime });
      set({
        availableVehicles: response.vehicles,
        isFetchingVehicles: false,
        currentStep: 'vehicle',
      });
    } catch (error) {
      set({
        error: '利用可能な車両の取得に失敗しました',
        isFetchingVehicles: false,
      });
    }
  },

  selectTripVehicle: (vehicleId: number | null) => {
    set({ selectedTripVehicleId: vehicleId });
  },

  setDepartureTime: (time: string | null) => {
    set({ departureTime: time });
  },

  createBooking: async () => {
    const { selectedRoute, selectedTripVehicleId, departureTime } = get();
    if (!selectedRoute || !selectedTripVehicleId || !departureTime) {
      set({ error: '予約に必要な情報が不足しています' });
      return;
    }

    set({ isBooking: true, error: null });
    try {
      const response = await api.createTripBooking({
        routeId: selectedRoute.id,
        vehicleId: selectedTripVehicleId,
        departureTime,
      });
      set({
        currentBooking: response.booking,
        isBooking: false,
        currentStep: 'complete',
      });
    } catch (error) {
      set({
        error: '予約の作成に失敗しました',
        isBooking: false,
      });
    }
  },

  setStep: (step: TripStep) => {
    set({ currentStep: step });
  },

  resetTrip: () => {
    set({
      currentStep: 'search',
      searchQuery: '',
      destinations: [],
      selectedDestination: null,
      routeSuggestion: null,
      selectedRoute: null,
      availableVehicles: [],
      selectedTripVehicleId: null,
      departureTime: null,
      currentBooking: null,
      error: null,
    });
  },

  clearError: () => {
    set({ error: null });
  },
}));
