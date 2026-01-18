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
  StreamingState,
  StreamingStep,
  StreamEvent,
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
  selectVehiclePreview: (vehicleId: number) => void;
  openVehicleDetail: (vehicleId: number) => void;
  closeVehicleDetail: () => void;
  closePreview: () => void;
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

  selectVehiclePreview: (vehicleId: number) => {
    set({
      selectedVehicleId: vehicleId,
      isDetailMode: false,
      bottomSheetSnap: 1,
    });
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

  closePreview: () => {
    set({
      selectedVehicleId: null,
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

// Default streaming steps
const DEFAULT_STREAMING_STEPS: StreamingStep[] = [
  { name: '目的地抽出', index: 0, status: 'pending', thinkingContent: '' },
  { name: 'ルート候補生成', index: 1, status: 'pending', thinkingContent: '' },
  { name: 'ルート評価', index: 2, status: 'pending', thinkingContent: '' },
];

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
  // Streaming state
  streaming: StreamingState;
  useStreaming: boolean;

  // Actions
  setSearchQuery: (query: string) => void;
  searchDestinations: (query: string) => Promise<void>;
  selectDestination: (destination: Destination | null) => void;
  suggestRoutes: (query: string) => Promise<void>;
  suggestRoutesStreaming: (query: string) => Promise<void>;
  handleStreamEvent: (event: StreamEvent) => void;
  setStreamingRoutes: (routes: Route[]) => void;
  cancelStreaming: () => void;
  setUseStreaming: (useStreaming: boolean) => void;
  selectRoute: (route: Route | null) => void;
  fetchAvailableVehicles: (routeId: string, departureTime: string) => Promise<void>;
  selectTripVehicle: (vehicleId: number | null) => void;
  setDepartureTime: (time: string | null) => void;
  createBooking: () => Promise<void>;
  setStep: (step: TripStep) => void;
  resetTrip: () => void;
  clearError: () => void;
}

// Streaming abort controller reference (stored outside of state)
let streamAbortController: AbortController | null = null;

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
  streaming: {
    isStreaming: false,
    currentStepIndex: null,
    steps: DEFAULT_STREAMING_STEPS.map(s => ({ ...s })),
    error: null,
  },
  useStreaming: true, // Enable streaming

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
        // 最初のルートを自動選択
        selectedRoute: response.routes.length > 0 ? response.routes[0] : null,
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

  suggestRoutesStreaming: async (query: string) => {
    // Cancel any existing stream
    if (streamAbortController) {
      streamAbortController.abort();
    }

    streamAbortController = new AbortController();

    set({
      isFetchingRoute: true,
      error: null,
      routeSuggestion: null,
      streaming: {
        isStreaming: true,
        currentStepIndex: null,
        steps: DEFAULT_STREAMING_STEPS.map(s => ({ ...s })),
        error: null,
      },
    });

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/routing/suggest/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ query }),
        signal: streamAbortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is null');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let eventCount = 0;

      console.log('[SSE] Starting to read stream');

      // Helper function to parse a single SSE event block
      const parseSSEEvent = (eventBlock: string): StreamEvent | null => {
        // Normalize line endings (CRLF to LF)
        const normalizedBlock = eventBlock.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        const lines = normalizedBlock.split('\n');
        let dataLines: string[] = [];

        for (const line of lines) {
          // Skip SSE comments (lines starting with :)
          if (line.startsWith(':')) continue;
          // Skip event type lines (we get type from JSON)
          if (line.startsWith('event:')) continue;
          // Collect data lines
          if (line.startsWith('data:')) {
            dataLines.push(line.slice(5));
          }
        }

        if (dataLines.length === 0) return null;

        // Join multiple data lines (SSE spec allows multi-line data)
        const dataContent = dataLines.join('\n').trim();
        if (!dataContent) return null;

        try {
          return JSON.parse(dataContent) as StreamEvent;
        } catch (e) {
          console.error('[SSE Parse Error]', e, dataContent.substring(0, 100));
          return null;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('[SSE] Stream ended, remaining buffer length:', buffer.length);
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Normalize line endings for consistent splitting
        // SSE spec uses \r\n but we normalize to \n for easier processing
        buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

        // Process complete SSE events (separated by double newline)
        let eventEnd = buffer.indexOf('\n\n');
        while (eventEnd !== -1) {
          const eventBlock = buffer.substring(0, eventEnd);
          buffer = buffer.substring(eventEnd + 2);

          // Skip empty blocks and pure comment blocks
          const trimmedBlock = eventBlock.trim();
          if (trimmedBlock && !trimmedBlock.startsWith(':')) {
            const event = parseSSEEvent(eventBlock);
            if (event) {
              eventCount++;
              console.log('[SSE Event]', eventCount, event.event);
              get().handleStreamEvent(event);
            }
          }

          eventEnd = buffer.indexOf('\n\n');
        }
      }

      // Process any remaining buffer after stream ends
      if (buffer.trim()) {
        console.log('[SSE] Processing final buffer, length:', buffer.length);
        // Normalize and split remaining buffer
        const normalizedBuffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        const remainingParts = normalizedBuffer.split('\n\n');
        for (const eventBlock of remainingParts) {
          const trimmedBlock = eventBlock.trim();
          if (trimmedBlock && !trimmedBlock.startsWith(':')) {
            const event = parseSSEEvent(eventBlock);
            if (event) {
              eventCount++;
              console.log('[SSE Final Event]', eventCount, event.event);
              get().handleStreamEvent(event);
            }
          }
        }
      }

      console.log('[SSE Complete] Total events:', eventCount, 'routeSuggestion:', !!get().routeSuggestion);

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Stream was cancelled
        return;
      }

      console.error('Stream error:', error);
      set(state => ({
        isFetchingRoute: false,
        error: error instanceof Error ? error.message : 'ストリーミングエラー',
        streaming: {
          ...state.streaming,
          isStreaming: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        },
      }));
    }
  },

  handleStreamEvent: (event: StreamEvent) => {
    console.log('[Stream Event]', event.event, event);
    switch (event.event) {
      case 'step_start':
        set(state => ({
          streaming: {
            ...state.streaming,
            currentStepIndex: event.step_index ?? null,
            steps: state.streaming.steps.map(s =>
              s.index === event.step_index
                ? { ...s, status: 'active' as const, name: event.step_name || s.name }
                : s
            ),
          },
        }));
        break;

      case 'thinking':
        console.log('[Thinking]', `step=${event.step_index}`, `content="${event.content}"`);
        set(state => ({
          streaming: {
            ...state.streaming,
            steps: state.streaming.steps.map(s =>
              s.index === event.step_index
                ? { ...s, thinkingContent: s.thinkingContent + (event.content || '') }
                : s
            ),
          },
        }));
        break;

      case 'step_complete':
        set(state => ({
          streaming: {
            ...state.streaming,
            steps: state.streaming.steps.map(s =>
              s.index === event.step_index
                ? { ...s, status: 'completed' as const }
                : s
            ),
          },
        }));
        break;

      case 'routes':
        console.log('[Routes Event] data:', event.data);
        if (event.data && 'routes' in event.data) {
          const routes = event.data.routes as Route[];
          console.log('[Routes Event] Setting routeSuggestion with', routes.length, 'routes');
          set({
            routeSuggestion: {
              routes,
              query: (event.data.query as string) || '',
              generatedAt: (event.data.generatedAt as string) || new Date().toISOString(),
            },
            // 最初のルートを自動選択
            selectedRoute: routes.length > 0 ? routes[0] : null,
          });
        } else {
          console.warn('[Routes Event] Invalid data structure:', event.data);
        }
        break;

      case 'done':
        console.log('[Done Event] routeSuggestion:', get().routeSuggestion);
        // If routeSuggestion is still null after done, show error
        if (!get().routeSuggestion) {
          console.error('[Done Event] routeSuggestion is null after streaming completed');
          set(state => ({
            isFetchingRoute: false,
            currentStep: 'plan',
            error: 'ルート情報の取得に失敗しました。再度お試しください。',
            streaming: {
              ...state.streaming,
              isStreaming: false,
              error: 'Routes event was not received',
            },
          }));
        } else {
          set(state => ({
            isFetchingRoute: false,
            currentStep: 'plan',
            streaming: {
              ...state.streaming,
              isStreaming: false,
            },
          }));
        }
        break;

      case 'error':
        set(state => ({
          isFetchingRoute: false,
          error: event.content || 'Unknown error',
          streaming: {
            ...state.streaming,
            isStreaming: false,
            error: event.content || 'Unknown error',
          },
        }));
        break;
    }
  },

  setStreamingRoutes: (routes: Route[]) => {
    set({
      routeSuggestion: {
        routes,
        query: get().searchQuery,
        generatedAt: new Date().toISOString(),
      },
    });
  },

  cancelStreaming: () => {
    if (streamAbortController) {
      streamAbortController.abort();
      streamAbortController = null;
    }
    set(state => ({
      isFetchingRoute: false,
      streaming: {
        ...state.streaming,
        isStreaming: false,
      },
    }));
  },

  setUseStreaming: (useStreaming: boolean) => {
    set({ useStreaming });
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

    // デモ用: バックエンドAPIを呼ばずにモック予約を作成
    // 少し遅延を入れてリアルな感じを出す
    await new Promise(resolve => setTimeout(resolve, 800));

    const mockBooking: TripBooking = {
      id: `BK-${Date.now().toString(36).toUpperCase()}`,
      route: selectedRoute,
      vehicleId: selectedTripVehicleId,
      departureTime,
      status: 'confirmed',
      createdAt: new Date().toISOString(),
    };

    set({
      currentBooking: mockBooking,
      isBooking: false,
      currentStep: 'complete',
    });
  },

  setStep: (step: TripStep) => {
    set({ currentStep: step });
  },

  resetTrip: () => {
    // Cancel any existing stream
    if (streamAbortController) {
      streamAbortController.abort();
      streamAbortController = null;
    }
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
      streaming: {
        isStreaming: false,
        currentStepIndex: null,
        steps: DEFAULT_STREAMING_STEPS.map(s => ({ ...s })),
        error: null,
      },
    });
  },

  clearError: () => {
    set({ error: null });
  },
}));
