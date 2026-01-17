import { useEffect, useState } from 'react';
import { useVehicleStore, useEarningsStore, useYieldStore, useUIStore } from '../../store';
import { MapView } from '../../components/map';
import { TopOverlay } from '../../components/overlay';
import {
  BottomSheet,
  VehicleListCompact,
  EarningsSummaryCompact,
  RecommendationCompact,
} from '../../components/bottomsheet';
import type { SnapPoint } from '../../components/bottomsheet';
import { VehicleMode } from '../../types/vehicle';

export function MapDashboard() {
  const {
    vehicles,
    fetchVehicles,
    changeMode,
    isLoading: vehiclesLoading,
  } = useVehicleStore();

  const {
    realtimeEarnings,
    fetchRealtimeEarnings,
  } = useEarningsStore();

  const { predictions, fetchPrediction } = useYieldStore();

  const {
    selectedVehicleId,
    bottomSheetSnap,
    setSelectedVehicleId,
    setBottomSheetSnap,
  } = useUIStore();

  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initial data fetch
  useEffect(() => {
    fetchVehicles();
    fetchRealtimeEarnings();
  }, [fetchVehicles, fetchRealtimeEarnings]);

  // Fetch predictions for all vehicles
  useEffect(() => {
    vehicles.forEach((v) => {
      if (!predictions[v.id]) {
        fetchPrediction(v.id);
      }
    });
  }, [vehicles, predictions, fetchPrediction]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchRealtimeEarnings();
      vehicles.forEach((v) => fetchPrediction(v.id));
    }, 30000);
    return () => clearInterval(interval);
  }, [vehicles, fetchRealtimeEarnings, fetchPrediction]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetchVehicles();
      await fetchRealtimeEarnings();
      for (const v of vehicles) {
        await fetchPrediction(v.id);
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleModeChange = async (vehicleId: number, mode: VehicleMode) => {
    try {
      await changeMode(vehicleId, mode);
      await fetchRealtimeEarnings();
      await fetchPrediction(vehicleId);
    } catch (error) {
      console.error('Failed to change mode:', error);
    }
  };

  const handleVehicleSelect = (vehicle: { id: number } | null) => {
    setSelectedVehicleId(vehicle?.id ?? null);
    // Expand bottom sheet when vehicle is selected
    if (vehicle && bottomSheetSnap === 0) {
      setBottomSheetSnap(1);
    }
  };

  const handleVehicleSelectFromList = (vehicle: { id: number }) => {
    setSelectedVehicleId(vehicle.id);
    // Keep the current snap position when selecting from list
  };

  const handleSnapChange = (snap: SnapPoint) => {
    setBottomSheetSnap(snap);
  };

  return (
    <div className="h-screen-dvh h-screen w-full overflow-hidden bg-gray-100 relative">
      {/* Full Screen Map */}
      <div className="absolute inset-0 z-0">
        <MapView
          vehicles={vehicles}
          selectedVehicleId={selectedVehicleId}
          onVehicleSelect={handleVehicleSelect}
          onModeChange={handleModeChange}
        />
      </div>

      {/* Top Overlay */}
      <TopOverlay
        earnings={realtimeEarnings}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Bottom Sheet */}
      <BottomSheet
        snap={bottomSheetSnap}
        onSnapChange={handleSnapChange}
      >
        <div className="space-y-4">
          {/* Earnings Summary - Always visible */}
          <EarningsSummaryCompact
            earnings={realtimeEarnings}
            isLoading={vehiclesLoading}
          />

          {/* Vehicle List - Visible at snap 1+ */}
          {bottomSheetSnap >= 1 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">車両</h3>
              <VehicleListCompact
                vehicles={vehicles}
                selectedVehicleId={selectedVehicleId}
                onVehicleSelect={handleVehicleSelectFromList}
              />
            </div>
          )}

          {/* AI Recommendations - Visible at snap 2 */}
          {bottomSheetSnap >= 2 && (
            <RecommendationCompact
              predictions={predictions}
              vehicles={vehicles}
              onModeChange={handleModeChange}
            />
          )}
        </div>
      </BottomSheet>
    </div>
  );
}
