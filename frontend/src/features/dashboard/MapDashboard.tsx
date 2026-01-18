import { useEffect, useState } from 'react';
import { useVehicleStore, useEarningsStore, useYieldStore, useUIStore, useTripStore } from '../../store';
import { MapView } from '../../components/map';
import { TopOverlay } from '../../components/overlay';
import {
  BottomSheet,
  VehicleListCompact,
  EarningsSummaryCompact,
  RecommendationCompact,
} from '../../components/bottomsheet';
import type { SnapPoint } from '../../components/bottomsheet';
import { VehicleDetailSheet, VehiclePreviewCard } from '../../components/vehicle';
import { VehicleMode } from '../../types/vehicle';
import { TripPlannerSheet } from '../trip';

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
    isDetailMode,
    appMode,
    setBottomSheetSnap,
    setAppMode,
    selectVehiclePreview,
    openVehicleDetail,
    closeVehicleDetail,
    closePreview,
  } = useUIStore();

  const { resetTrip, selectedRoute } = useTripStore();

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isChangingMode, setIsChangingMode] = useState(false);

  // Get selected vehicle object
  const selectedVehicle = vehicles.find(v => v.id === selectedVehicleId) || null;

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
    setIsChangingMode(true);
    try {
      await changeMode(vehicleId, mode);
      await fetchRealtimeEarnings();
      await fetchPrediction(vehicleId);
    } catch (error) {
      console.error('Failed to change mode:', error);
    } finally {
      setIsChangingMode(false);
    }
  };

  const handleVehicleSelect = (vehicle: { id: number } | null) => {
    if (vehicle) {
      // Show preview first (2-stage display)
      selectVehiclePreview(vehicle.id);
    } else {
      // Deselect and return to summary view
      closePreview();
    }
  };

  const handleVehicleSelectFromList = (vehicle: { id: number }) => {
    // Show preview (same as marker tap)
    selectVehiclePreview(vehicle.id);
  };

  const handleCloseDetail = () => {
    closeVehicleDetail();
  };

  const handleClosePreview = () => {
    closePreview();
  };

  const handleViewDetail = () => {
    if (selectedVehicleId) {
      openVehicleDetail(selectedVehicleId);
    }
  };

  const handleSnapChange = (snap: SnapPoint) => {
    // If in preview mode (vehicle selected but not in detail mode) and user swipes up to snap 2+
    // transition to full detail mode
    if (selectedVehicleId && !isDetailMode && snap >= 2) {
      openVehicleDetail(selectedVehicleId);
      return;
    }
    setBottomSheetSnap(snap);
  };

  const handleAppModeChange = (mode: 'owner' | 'user') => {
    setAppMode(mode);
    if (mode === 'user') {
      resetTrip();
    }
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
          selectedRoute={appMode === 'user' ? selectedRoute : null}
        />
      </div>

      {/* Top Overlay */}
      <TopOverlay
        earnings={realtimeEarnings}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        appMode={appMode}
        onModeChange={handleAppModeChange}
      />

      {/* Bottom Sheet */}
      <BottomSheet
        snap={bottomSheetSnap}
        onSnapChange={handleSnapChange}
        isDetailMode={isDetailMode && appMode === 'owner'}
        detailContent={
          selectedVehicle && appMode === 'owner' && (
            <VehicleDetailSheet
              vehicle={selectedVehicle}
              prediction={predictions[selectedVehicle.id] || null}
              onBack={handleCloseDetail}
              onModeChange={handleModeChange}
              isChangingMode={isChangingMode}
            />
          )
        }
      >
        {appMode === 'owner' ? (
          selectedVehicleId && !isDetailMode && selectedVehicle ? (
            // Preview mode: show compact vehicle preview card
            <VehiclePreviewCard
              vehicle={selectedVehicle}
              prediction={predictions[selectedVehicleId] || null}
              onViewDetail={handleViewDetail}
              onClose={handleClosePreview}
              onModeChange={handleModeChange}
              isChangingMode={isChangingMode}
            />
          ) : (
            // Default mode: show earnings and vehicle list
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
          )
        ) : (
          <TripPlannerSheet />
        )}
      </BottomSheet>
    </div>
  );
}
