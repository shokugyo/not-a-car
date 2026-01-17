import { InteriorMode } from '../types/vehicle';

export interface Vehicle3DConfig {
  modelPath: string;
  posterPath: string;
  cameraOrbit: string;
  scale: number;
}

const BASE_PATH = '/assets';
const MODELS_PATH = `${BASE_PATH}/models/vehicles`;
const INTERIORS_PATH = `${BASE_PATH}/models/interiors`;
const IMAGES_PATH = `${BASE_PATH}/images/vehicles`;

export const DEFAULT_VEHICLE_MODEL: Vehicle3DConfig = {
  modelPath: `${MODELS_PATH}/default.glb`,
  posterPath: `${IMAGES_PATH}/default-placeholder.png`,
  cameraOrbit: '0deg 75deg 105%',
  scale: 1,
};

export const VEHICLE_MODELS: Record<string, Vehicle3DConfig> = {
  'Model S': {
    modelPath: `${MODELS_PATH}/model-s.glb`,
    posterPath: `${IMAGES_PATH}/model-s-placeholder.png`,
    cameraOrbit: '0deg 75deg 105%',
    scale: 1,
  },
  'Model 3': {
    modelPath: `${MODELS_PATH}/model-3.glb`,
    posterPath: `${IMAGES_PATH}/model-3-placeholder.png`,
    cameraOrbit: '0deg 75deg 105%',
    scale: 1,
  },
  'Model X': {
    modelPath: `${MODELS_PATH}/model-x.glb`,
    posterPath: `${IMAGES_PATH}/model-x-placeholder.png`,
    cameraOrbit: '0deg 75deg 110%',
    scale: 1,
  },
  'Model Y': {
    modelPath: `${MODELS_PATH}/model-y.glb`,
    posterPath: `${IMAGES_PATH}/model-y-placeholder.png`,
    cameraOrbit: '0deg 75deg 105%',
    scale: 1,
  },
};

export const INTERIOR_MODELS: Record<InteriorMode, string> = {
  standard: `${INTERIORS_PATH}/standard.glb`,
  bed: `${INTERIORS_PATH}/bed.glb`,
  cargo: `${INTERIORS_PATH}/cargo.glb`,
  office: `${INTERIORS_PATH}/office.glb`,
  passenger: `${INTERIORS_PATH}/passenger.glb`,
};

export function getVehicleModelConfig(modelName: string | null): Vehicle3DConfig {
  if (!modelName) {
    return DEFAULT_VEHICLE_MODEL;
  }
  return VEHICLE_MODELS[modelName] ?? DEFAULT_VEHICLE_MODEL;
}

export function getInteriorModelPath(interiorMode: InteriorMode): string {
  return INTERIOR_MODELS[interiorMode];
}
