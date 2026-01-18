import { useEffect, useRef } from 'react';
import { Brain, CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';
import { StreamingState } from '../../types/trip';

interface StreamingReasoningPanelProps {
  streaming: StreamingState;
  onCancel?: () => void;
}

export function StreamingReasoningPanel({
  streaming,
  onCancel,
}: StreamingReasoningPanelProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const stepRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const panelRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new content arrives within step
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [streaming.steps]);

  // Auto-scroll to active step when step changes
  useEffect(() => {
    const activeStep = streaming.steps.find(s => s.status === 'active');
    if (activeStep) {
      const stepElement = stepRefs.current.get(activeStep.index);
      if (stepElement) {
        // Scroll the step into view with smooth animation
        stepElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      }
    }
  }, [streaming.currentStepIndex, streaming.steps]);

  // Scroll to panel when streaming starts
  useEffect(() => {
    if (streaming.isStreaming && panelRef.current) {
      panelRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  }, [streaming.isStreaming]);

  const activeStep = streaming.steps.find(s => s.status === 'active');

  // Function to store step refs
  const setStepRef = (index: number, element: HTMLDivElement | null) => {
    if (element) {
      stepRefs.current.set(index, element);
    } else {
      stepRefs.current.delete(index);
    }
  };

  return (
    <div ref={panelRef} className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-primary-50 to-primary-100 border-b border-primary-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <Brain size={18} className="text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-primary-900">AI分析中...</h3>
            <p className="text-xs text-primary-700">
              {activeStep ? activeStep.name : 'ルートを最適化しています'}
            </p>
          </div>
        </div>
        {onCancel && streaming.isStreaming && (
          <button
            onClick={onCancel}
            className="text-xs text-primary-600 hover:text-primary-800 px-2 py-1 rounded hover:bg-primary-200 transition-colors"
          >
            キャンセル
          </button>
        )}
      </div>

      {/* Steps */}
      <div className="p-4 space-y-3">
        {streaming.steps.map((step) => (
          <div
            key={step.index}
            ref={(el) => setStepRef(step.index, el)}
            className="space-y-2"
          >
            {/* Step header */}
            <div className="flex items-center gap-2">
              {step.status === 'completed' ? (
                <CheckCircle2 size={18} className="text-green-500" />
              ) : step.status === 'active' ? (
                <Loader2 size={18} className="text-primary-500 animate-spin" />
              ) : (
                <Circle size={18} className="text-gray-300" />
              )}
              <span
                className={`text-sm font-medium ${
                  step.status === 'active'
                    ? 'text-primary-700'
                    : step.status === 'completed'
                    ? 'text-gray-700'
                    : 'text-gray-400'
                }`}
              >
                {step.name}
              </span>
              {step.status === 'active' && (
                <span className="text-xs text-primary-500 animate-pulse">処理中</span>
              )}
            </div>

            {/* Thinking content */}
            {(step.status === 'active' || (step.status === 'completed' && step.thinkingContent)) && (
              <div
                ref={step.status === 'active' ? contentRef : undefined}
                className="ml-7 p-3 bg-gray-50 rounded-lg border border-gray-200 max-h-32 overflow-y-auto"
              >
                <p className="text-xs text-gray-600 font-mono whitespace-pre-wrap leading-relaxed">
                  {step.thinkingContent || (
                    <span className="text-gray-400 italic">処理を開始しています...</span>
                  )}
                  {step.status === 'active' && (
                    <span className="inline-block w-2 h-4 bg-primary-500 ml-0.5 animate-pulse" />
                  )}
                </p>
              </div>
            )}
          </div>
        ))}

        {/* Error state */}
        {streaming.error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg border border-red-200">
            <AlertCircle size={18} className="text-red-500" />
            <p className="text-sm text-red-700">{streaming.error}</p>
          </div>
        )}
      </div>

      {/* Progress bar */}
      {streaming.isStreaming && (
        <div className="h-1 bg-gray-200">
          <div
            className="h-full bg-primary-500 transition-all duration-300"
            style={{
              width: `${
                (streaming.steps.filter(s => s.status === 'completed').length /
                  streaming.steps.length) *
                100
              }%`,
            }}
          />
        </div>
      )}
    </div>
  );
}
