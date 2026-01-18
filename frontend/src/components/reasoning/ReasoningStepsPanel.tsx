import { Brain, CheckCircle2, Clock } from 'lucide-react';
import { ProcessingMetadata } from '../../types/trip';

interface ReasoningStepsPanelProps {
  processing: ProcessingMetadata;
}

export function ReasoningStepsPanel({ processing }: ReasoningStepsPanelProps) {
  return (
    <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl p-4 border border-primary-200">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 bg-primary-500 rounded-lg flex items-center justify-center">
          <Brain size={16} className="text-white" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-primary-900">AI分析結果</h3>
          <p className="text-xs text-primary-700 flex items-center gap-1">
            <Clock size={12} />
            {(processing.total_duration_ms / 1000).toFixed(1)}秒で分析完了
          </p>
        </div>
      </div>

      {/* Reasoning steps */}
      {processing.reasoning_steps.length > 0 && (
        <div className="space-y-1.5">
          {processing.reasoning_steps.map((step, index) => (
            <div key={index} className="flex items-start gap-2">
              <CheckCircle2 size={14} className="text-green-500 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-gray-700">{step}</p>
            </div>
          ))}
        </div>
      )}

      {/* Processing steps */}
      {processing.steps.length > 0 && (
        <div className="mt-3 pt-3 border-t border-primary-200">
          <div className="flex flex-wrap gap-2">
            {processing.steps.map((step, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-white/60 rounded-full text-xs text-primary-700"
              >
                <span className="font-medium">{step.step_name}</span>
                <span className="text-primary-500">
                  {(step.duration_ms / 1000).toFixed(1)}s
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
