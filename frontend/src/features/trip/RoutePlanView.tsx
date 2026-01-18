import { ChevronLeft, Clock, MapPin, Sparkles, Route as RouteIcon } from 'lucide-react';
import { useTripStore } from '../../store';
import { Route } from '../../types/trip';
import { ReasoningStepsPanel } from '../../components/reasoning';

interface RouteCardProps {
  route: Route;
  isSelected: boolean;
  onSelect: () => void;
}

function RouteCard({ route, isSelected, onSelect }: RouteCardProps) {
  const hours = Math.floor(route.totalDuration / 60);
  const minutes = route.totalDuration % 60;
  const durationText = hours > 0 ? `${hours}時間${minutes > 0 ? `${minutes}分` : ''}` : `${minutes}分`;

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
        isSelected
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-bold text-gray-900">{route.name}</h3>
        <span className="text-sm font-medium text-primary-600">
          ¥{route.estimatedCost.toLocaleString()}〜
        </span>
      </div>
      <p className="text-sm text-gray-600 mb-3">{route.description}</p>

      {/* Highlights */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {route.highlights.slice(0, 3).map((highlight, index) => (
          <span
            key={index}
            className="px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600"
          >
            {highlight}
          </span>
        ))}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <Clock size={14} />
          <span>{durationText}</span>
        </div>
        <div className="flex items-center gap-1">
          <RouteIcon size={14} />
          <span>{route.totalDistance}km</span>
        </div>
        <div className="flex items-center gap-1">
          <MapPin size={14} />
          <span>{route.waypoints.length}スポット</span>
        </div>
      </div>
    </button>
  );
}

export function RoutePlanView() {
  const { routeSuggestion, selectedRoute, selectRoute, setStep, error } = useTripStore();

  const handleBack = () => {
    setStep('search');
  };

  const handleConfirm = () => {
    if (selectedRoute) {
      setStep('confirm');
    }
  };

  if (!routeSuggestion) {
    return (
      <div className="flex flex-col items-center justify-center h-40 gap-4">
        {error ? (
          <>
            <p className="text-red-500">{error}</p>
            <button
              onClick={handleBack}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              検索に戻る
            </button>
          </>
        ) : (
          <p className="text-gray-500">ルートを読み込み中...</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleBack}
          className="p-2 -ml-2 rounded-lg hover:bg-gray-100 active:bg-gray-200 transition-colors"
        >
          <ChevronLeft size={20} className="text-gray-600" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
            <Sparkles size={18} className="text-primary-600" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">おすすめルート</h2>
            <p className="text-xs text-gray-500">AIが提案する旅程プラン</p>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      {/* AI Reasoning Panel */}
      {routeSuggestion?.processing && (
        <ReasoningStepsPanel processing={routeSuggestion.processing} />
      )}

      {/* Route Options */}
      <div className="space-y-3">
        {routeSuggestion.routes.map((route) => (
          <RouteCard
            key={route.id}
            route={route}
            isSelected={selectedRoute?.id === route.id}
            onSelect={() => selectRoute(route)}
          />
        ))}
      </div>

      {/* Confirm Button */}
      {selectedRoute && (
        <button
          onClick={handleConfirm}
          className="w-full py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 active:bg-primary-800 transition-colors"
        >
          このルートで決定
        </button>
      )}
    </div>
  );
}
