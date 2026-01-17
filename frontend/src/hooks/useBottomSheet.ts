import { useState, useCallback, useRef } from 'react';

export type SnapPoint = 0 | 1 | 2 | 3;

interface UseBottomSheetOptions {
  initialSnap?: SnapPoint;
  onSnapChange?: (snap: SnapPoint) => void;
  maxSnap?: SnapPoint;
}

interface UseBottomSheetReturn {
  snap: SnapPoint;
  setSnap: (snap: SnapPoint) => void;
  translateY: number;
  isDragging: boolean;
  handlers: {
    onTouchStart: (e: React.TouchEvent) => void;
    onTouchMove: (e: React.TouchEvent) => void;
    onTouchEnd: (e: React.TouchEvent) => void;
  };
}

// Snap point heights as percentages of viewport height
const SNAP_HEIGHTS: Record<SnapPoint, number> = {
  0: 15,   // Collapsed - 15vh
  1: 45,   // Half - 45vh
  2: 85,   // Expanded - 85vh
  3: 100,  // Fullscreen - 100vh (Vehicle Detail Mode)
};

export function useBottomSheet({
  initialSnap = 0,
  onSnapChange,
  maxSnap = 3,
}: UseBottomSheetOptions = {}): UseBottomSheetReturn {
  const [snap, setSnapState] = useState<SnapPoint>(initialSnap);
  const [isDragging, setIsDragging] = useState(false);
  const [translateY, setTranslateY] = useState(0);

  const dragStartY = useRef(0);
  const dragStartTranslate = useRef(0);
  const velocityRef = useRef(0);
  const lastTouchY = useRef(0);
  const lastTouchTime = useRef(0);

  const getHeightFromSnap = (s: SnapPoint): number => {
    return (SNAP_HEIGHTS[s] / 100) * window.innerHeight;
  };

  const setSnap = useCallback((newSnap: SnapPoint) => {
    setSnapState(newSnap);
    setTranslateY(0);
    onSnapChange?.(newSnap);
  }, [onSnapChange]);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    dragStartY.current = touch.clientY;
    dragStartTranslate.current = translateY;
    lastTouchY.current = touch.clientY;
    lastTouchTime.current = Date.now();
    velocityRef.current = 0;
    setIsDragging(true);
  }, [translateY]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isDragging) return;

    const touch = e.touches[0];
    const deltaY = touch.clientY - dragStartY.current;

    // Calculate velocity
    const now = Date.now();
    const timeDelta = now - lastTouchTime.current;
    if (timeDelta > 0) {
      velocityRef.current = (touch.clientY - lastTouchY.current) / timeDelta;
    }
    lastTouchY.current = touch.clientY;
    lastTouchTime.current = now;

    // Apply resistance at boundaries
    const currentHeight = getHeightFromSnap(snap);
    const newTranslate = dragStartTranslate.current + deltaY;

    // Limit drag range based on maxSnap
    const maxHeight = getHeightFromSnap(maxSnap);
    const minHeight = getHeightFromSnap(0);

    const effectiveHeight = currentHeight - newTranslate;

    if (effectiveHeight > maxHeight) {
      // Apply resistance when pulling up beyond max
      const overflow = effectiveHeight - maxHeight;
      setTranslateY(-overflow * 0.3);
    } else if (effectiveHeight < minHeight) {
      // Apply resistance when pulling down beyond min
      const overflow = minHeight - effectiveHeight;
      setTranslateY(overflow * 0.3);
    } else {
      setTranslateY(newTranslate);
    }
  }, [isDragging, snap, maxSnap]);

  const handleTouchEnd = useCallback(() => {
    if (!isDragging) return;
    setIsDragging(false);

    const currentHeight = getHeightFromSnap(snap) - translateY;
    const velocity = velocityRef.current;

    // Determine target snap based on position and velocity
    let targetSnap: SnapPoint = snap;

    // Velocity-based snap (if moving fast enough)
    if (Math.abs(velocity) > 0.5) {
      if (velocity < 0) {
        // Moving up (increasing height)
        targetSnap = Math.min(maxSnap, snap + 1) as SnapPoint;
      } else {
        // Moving down (decreasing height)
        targetSnap = Math.max(0, snap - 1) as SnapPoint;
      }
    } else {
      // Position-based snap - build heights array based on maxSnap
      const snapHeights: number[] = [];
      for (let i = 0; i <= maxSnap; i++) {
        snapHeights.push(getHeightFromSnap(i as SnapPoint));
      }

      // Find closest snap point
      let closestSnap: SnapPoint = 0;
      let minDistance = Infinity;

      snapHeights.forEach((height, index) => {
        const distance = Math.abs(currentHeight - height);
        if (distance < minDistance) {
          minDistance = distance;
          closestSnap = index as SnapPoint;
        }
      });

      targetSnap = closestSnap;
    }

    setSnap(targetSnap);
  }, [isDragging, snap, translateY, setSnap, maxSnap]);

  return {
    snap,
    setSnap,
    translateY: isDragging ? translateY : 0,
    isDragging,
    handlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    },
  };
}

export { SNAP_HEIGHTS };
