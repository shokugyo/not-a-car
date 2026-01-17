import { create } from 'zustand';
import { Owner } from '../types/api';
import { Vehicle, VehicleStatus } from '../types/vehicle';
import { RealtimeEarning, EarningsSummary } from '../types/earnings';
import { YieldPrediction } from '../types/yield';
import api from '../api/client';

// UI State Store
type SnapPoint = 0 | 1 | 2;

interface UIState {
  selectedVehicleId: number | null;
  bottomSheetSnap: SnapPoint;
  setSelectedVehicleId: (id: number | null) => void;
  setBottomSheetSnap: (snap: SnapPoint) => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedVehicleId: null,
  bottomSheetSnap: 0,

  setSelectedVehicleId: (id: number | null) => {
    set({ selectedVehicleId: id });
  },

  setBottomSheetSnap: (snap: SnapPoint) => {
    set({ bottomSheetSnap: snap });
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
