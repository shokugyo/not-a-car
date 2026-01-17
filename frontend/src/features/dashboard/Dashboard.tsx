import React, { useEffect, useState } from 'react';
import { Car, Plus, RefreshCw } from 'lucide-react';
import { useVehicleStore, useEarningsStore, useYieldStore } from '../../store';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { VehicleCard } from '../../components/vehicle/VehicleCard';
import { EarningsWidget } from './EarningsWidget';
import { RecommendationWidget } from './RecommendationWidget';
import { VehicleMode } from '../../types/vehicle';
import api from '../../api/client';

export function Dashboard() {
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

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showAddVehicle, setShowAddVehicle] = useState(false);
  const [newVehicle, setNewVehicle] = useState({
    license_plate: '',
    name: '',
    model: '',
  });

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

  const handleAddVehicle = async () => {
    if (!newVehicle.license_plate) return;
    try {
      await api.createVehicle(newVehicle);
      await fetchVehicles();
      setNewVehicle({ license_plate: '', name: '', model: '' });
      setShowAddVehicle(false);
    } catch (error) {
      console.error('Failed to add vehicle:', error);
    }
  };

  const vehicleNames = vehicles.reduce(
    (acc, v) => ({ ...acc, [v.id]: v.name || v.license_plate }),
    {} as Record<number, string>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <Car className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">NOT A CAR</h1>
                <p className="text-sm text-gray-500">Your car works while you sleep</p>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw
                size={16}
                className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`}
              />
              更新
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Earnings & Recommendations */}
          <div className="lg:col-span-2 space-y-6">
            <EarningsWidget
              earnings={realtimeEarnings}
              isLoading={vehiclesLoading}
            />

            <RecommendationWidget
              predictions={predictions}
              vehicleNames={vehicleNames}
              onModeChange={handleModeChange}
            />
          </div>

          {/* Right Column - Vehicles */}
          <div className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>車両一覧</CardTitle>
                <Button size="sm" onClick={() => setShowAddVehicle(true)}>
                  <Plus size={16} className="mr-1" />
                  追加
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Add Vehicle Form */}
                {showAddVehicle && (
                  <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                    <input
                      type="text"
                      placeholder="ナンバープレート *"
                      className="input"
                      value={newVehicle.license_plate}
                      onChange={(e) =>
                        setNewVehicle({ ...newVehicle, license_plate: e.target.value })
                      }
                    />
                    <input
                      type="text"
                      placeholder="車両名"
                      className="input"
                      value={newVehicle.name}
                      onChange={(e) =>
                        setNewVehicle({ ...newVehicle, name: e.target.value })
                      }
                    />
                    <input
                      type="text"
                      placeholder="車種"
                      className="input"
                      value={newVehicle.model}
                      onChange={(e) =>
                        setNewVehicle({ ...newVehicle, model: e.target.value })
                      }
                    />
                    <div className="flex gap-2">
                      <Button onClick={handleAddVehicle}>登録</Button>
                      <Button
                        variant="secondary"
                        onClick={() => setShowAddVehicle(false)}
                      >
                        キャンセル
                      </Button>
                    </div>
                  </div>
                )}

                {/* Vehicle List */}
                {vehicles.map((vehicle) => (
                  <VehicleCard key={vehicle.id} vehicle={vehicle} />
                ))}

                {vehicles.length === 0 && !showAddVehicle && (
                  <div className="text-center py-8 text-gray-500">
                    <Car size={48} className="mx-auto mb-3 text-gray-300" />
                    <p>車両が登録されていません</p>
                    <p className="text-sm mt-1">
                      「追加」ボタンから車両を登録してください
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
