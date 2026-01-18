import { useState, useCallback, useRef } from 'react';
import {
  StreamEvent,
  StreamingState,
  StreamingStep,
  Route,
} from '../types/trip';

const API_BASE = '/api/v1';

function parseSSELine(line: string): { event?: string; data?: string } | null {
  if (!line.trim()) return null;

  if (line.startsWith('event:')) {
    return { event: line.slice(6).trim() };
  }
  if (line.startsWith('data:')) {
    return { data: line.slice(5).trim() };
  }
  return null;
}

function parseSSEEvents(chunk: string): StreamEvent[] {
  const events: StreamEvent[] = [];
  const lines = chunk.split('\n');

  for (const line of lines) {
    const parsed = parseSSELine(line);
    if (!parsed) continue;

    if (parsed.data) {
      try {
        const data = JSON.parse(parsed.data);
        events.push(data as StreamEvent);
      } catch {
        // Ignore parse errors
      }
    }
  }

  return events;
}

const DEFAULT_STEPS: StreamingStep[] = [
  { name: '目的地抽出', index: 0, status: 'pending', thinkingContent: '' },
  { name: 'ルート候補生成', index: 1, status: 'pending', thinkingContent: '' },
  { name: 'ルート評価', index: 2, status: 'pending', thinkingContent: '' },
];

export interface UseRouteStreamReturn {
  streaming: StreamingState;
  routes: Route[] | null;
  startStream: (query: string) => Promise<void>;
  cancelStream: () => void;
}

export function useRouteStream(): UseRouteStreamReturn {
  const [streaming, setStreaming] = useState<StreamingState>({
    isStreaming: false,
    currentStepIndex: null,
    steps: DEFAULT_STEPS.map(s => ({ ...s })),
    error: null,
  });

  const [routes, setRoutes] = useState<Route[] | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(prev => ({
      ...prev,
      isStreaming: false,
    }));
  }, []);

  const startStream = useCallback(async (query: string) => {
    // Cancel any existing stream
    cancelStream();

    // Reset state
    setRoutes(null);
    setStreaming({
      isStreaming: true,
      currentStepIndex: null,
      steps: DEFAULT_STEPS.map(s => ({ ...s })),
      error: null,
    });

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/routing/suggest/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ query }),
        signal: abortController.signal,
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

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete events
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const chunk of lines) {
          if (!chunk.trim()) continue;

          const events = parseSSEEvents(chunk);

          for (const event of events) {
            handleStreamEvent(event);
          }
        }
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        const events = parseSSEEvents(buffer);
        for (const event of events) {
          handleStreamEvent(event);
        }
      }

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Stream was cancelled
        return;
      }

      console.error('Stream error:', error);
      setStreaming(prev => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    }

    function handleStreamEvent(event: StreamEvent) {
      switch (event.event) {
        case 'step_start':
          setStreaming(prev => {
            const steps = prev.steps.map(s =>
              s.index === event.step_index
                ? { ...s, status: 'active' as const, name: event.step_name || s.name }
                : s
            );
            return {
              ...prev,
              currentStepIndex: event.step_index ?? null,
              steps,
            };
          });
          break;

        case 'thinking':
          setStreaming(prev => {
            const steps = prev.steps.map(s =>
              s.index === event.step_index
                ? { ...s, thinkingContent: s.thinkingContent + (event.content || '') }
                : s
            );
            return { ...prev, steps };
          });
          break;

        case 'step_complete':
          setStreaming(prev => {
            const steps = prev.steps.map(s =>
              s.index === event.step_index
                ? { ...s, status: 'completed' as const }
                : s
            );
            return { ...prev, steps };
          });
          break;

        case 'routes':
          if (event.data && 'routes' in event.data) {
            setRoutes(event.data.routes as Route[]);
          }
          break;

        case 'done':
          setStreaming(prev => ({
            ...prev,
            isStreaming: false,
          }));
          break;

        case 'error':
          setStreaming(prev => ({
            ...prev,
            isStreaming: false,
            error: event.content || 'Unknown error',
          }));
          break;
      }
    }
  }, [cancelStream]);

  return {
    streaming,
    routes,
    startStream,
    cancelStream,
  };
}
