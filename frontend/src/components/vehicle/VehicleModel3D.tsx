import { useEffect, useRef, useState } from 'react';
import '@google/model-viewer';
import { getVehicleModelConfig } from '../../constants/vehicleModels';
import { Loader2, AlertCircle, RotateCcw, Car } from 'lucide-react';
import type { ModelViewerElement } from '../../types/model-viewer';

interface VehicleModel3DProps {
  modelName: string | null;
  className?: string;
  showControls?: boolean;
}

type LoadState = 'loading' | 'loaded' | 'error' | 'fallback';

export function VehicleModel3D({
  modelName,
  className = '',
  showControls = true,
}: VehicleModel3DProps) {
  const modelRef = useRef<ModelViewerElement>(null);
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [useFallback, setUseFallback] = useState(false);

  const config = getVehicleModelConfig(modelName);

  useEffect(() => {
    setLoadState('loading');
    setUseFallback(false);
  }, [modelName]);

  const handleLoad = () => {
    setLoadState('loaded');
  };

  const handleError = () => {
    if (!useFallback) {
      setUseFallback(true);
      setLoadState('fallback');
    } else {
      setLoadState('error');
    }
  };

  const handleRetry = () => {
    setLoadState('loading');
    setUseFallback(false);
    if (modelRef.current) {
      modelRef.current.src = config.modelPath;
    }
  };

  const handleResetCamera = () => {
    if (modelRef.current) {
      modelRef.current.cameraOrbit = config.cameraOrbit;
    }
  };

  if (loadState === 'error') {
    return (
      <div className={`flex flex-col items-center justify-center bg-gray-100 rounded-2xl ${className}`}>
        <AlertCircle className="w-12 h-12 text-gray-400 mb-3" />
        <p className="text-gray-500 text-sm mb-3">モデルを読み込めませんでした</p>
        <button
          onClick={handleRetry}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          再試行
        </button>
      </div>
    );
  }

  if (loadState === 'fallback') {
    return (
      <div className={`relative flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl overflow-hidden ${className}`}>
        <div className="absolute inset-0 flex items-center justify-center">
          <Car className="w-32 h-32 text-gray-300" strokeWidth={1} />
        </div>
        <div className="absolute bottom-4 left-0 right-0 text-center">
          <p className="text-gray-500 text-xs">3Dモデル準備中</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100 ${className}`}>
      {loadState === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
        </div>
      )}

      <model-viewer
        ref={modelRef}
        src={config.modelPath}
        poster={config.posterPath}
        alt={`${modelName || 'Vehicle'} 3D Model`}
        camera-controls
        auto-rotate
        touch-action="pan-y"
        interaction-prompt="none"
        camera-orbit={config.cameraOrbit}
        shadow-intensity={1}
        exposure={1}
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: 'transparent',
        }}
        onLoad={handleLoad}
        onError={handleError}
      />

      {showControls && loadState === 'loaded' && (
        <button
          onClick={handleResetCamera}
          className="absolute bottom-3 right-3 p-2 bg-white/80 backdrop-blur-sm rounded-full shadow-md hover:bg-white transition-colors"
          title="カメラをリセット"
        >
          <RotateCcw className="w-4 h-4 text-gray-600" />
        </button>
      )}

      <div className="absolute bottom-3 left-3 text-xs text-gray-400">
        タッチして回転・ズーム
      </div>
    </div>
  );
}
