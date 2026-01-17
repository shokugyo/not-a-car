/// <reference types="react" />

interface ModelViewerElement extends HTMLElement {
  loaded: boolean;
  modelIsVisible: boolean;
  getCameraOrbit: () => { theta: number; phi: number; radius: number };
  setCameraOrbit: (theta: number, phi: number, radius: number) => void;
  resetCameraOrbit: () => void;
  jumpCameraToGoal: () => void;
  cameraTarget: { x: number; y: number; z: number };
  fieldOfView: string;
  minFieldOfView: string;
  maxFieldOfView: string;
  cameraOrbit: string;
  minCameraOrbit: string;
  maxCameraOrbit: string;
  exposure: number;
  shadowIntensity: number;
  shadowSoftness: number;
  environmentImage: string | null;
  src: string | null;
  poster: string | null;
  reveal: 'auto' | 'manual' | 'interaction';
  loading: 'auto' | 'lazy' | 'eager';
  autoRotate: boolean;
  cameraControls: boolean;
  disableZoom: boolean;
  disablePan: boolean;
  disableTap: boolean;
  interactionPrompt: 'auto' | 'when-focused' | 'none';
  interactionPromptStyle: 'basic' | 'wiggle';
  interactionPromptThreshold: number;
}

interface ModelViewerAttributes {
  src?: string;
  alt?: string;
  poster?: string;
  loading?: 'auto' | 'lazy' | 'eager';
  reveal?: 'auto' | 'manual' | 'interaction';
  'auto-rotate'?: boolean | '';
  'camera-controls'?: boolean | '';
  'touch-action'?: 'none' | 'pan-x' | 'pan-y' | 'pinch-zoom';
  'disable-zoom'?: boolean | '';
  'disable-pan'?: boolean | '';
  'disable-tap'?: boolean | '';
  'interaction-prompt'?: 'auto' | 'when-focused' | 'none';
  'interaction-prompt-style'?: 'basic' | 'wiggle';
  'interaction-prompt-threshold'?: number;
  'camera-orbit'?: string;
  'min-camera-orbit'?: string;
  'max-camera-orbit'?: string;
  'field-of-view'?: string;
  'min-field-of-view'?: string;
  'max-field-of-view'?: string;
  'environment-image'?: string;
  exposure?: number;
  'shadow-intensity'?: number;
  'shadow-softness'?: number;
  ar?: boolean | '';
  'ar-modes'?: string;
  'ar-scale'?: 'auto' | 'fixed';
  'ar-placement'?: 'floor' | 'wall';
  'ios-src'?: string;
  skybox?: string;
  style?: React.CSSProperties;
  className?: string;
  onLoad?: () => void;
  onError?: (event: Event) => void;
  onProgress?: (event: CustomEvent<{ totalProgress: number }>) => void;
  ref?: React.Ref<ModelViewerElement>;
  children?: React.ReactNode;
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': ModelViewerAttributes;
    }
  }

  interface Window {
    ModelViewerElement?: typeof HTMLElement;
  }
}

export type { ModelViewerElement, ModelViewerAttributes };
