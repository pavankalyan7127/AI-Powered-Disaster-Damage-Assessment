import React from 'react';
import { Loader2, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function ProcessingScreen({ steps, currentStepIndex }) {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center animate-fade-in">
      
      <div className="relative mb-8">
        <div className="w-24 h-24 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center animate-pulse">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
        </div>
        <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin" />
      </div>

      <h2 className="text-2xl font-bold text-white mb-2">Processing Disaster Imagery</h2>
      <p className="text-sm text-slate-400 max-w-md mb-8">
        The Siamese ResNet-50 inference engine is analyzing building crops and evaluating structural damage severity.
      </p>

      {/* Progress Steps List */}
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 text-left space-y-4">
        {steps.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;
          const isPending = idx > currentStepIndex;

          return (
            <div key={idx} className="flex items-center gap-3">
              <div className="shrink-0">
                {isDone && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                )}
                {isCurrent && (
                  <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                )}
                {isPending && (
                  <div className="w-5 h-5 rounded-full border border-slate-700 bg-slate-950" />
                )}
              </div>

              <span
                className={`text-sm font-medium transition-colors ${
                  isDone
                    ? 'text-slate-300 line-through text-opacity-60'
                    : isCurrent
                    ? 'text-cyan-400 font-semibold'
                    : 'text-slate-500'
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-8 flex items-center gap-2 text-xs text-slate-500">
        <ShieldCheck className="w-4 h-4 text-emerald-500" />
        <span>Memory-efficient raster windowing active</span>
      </div>
    </div>
  );
}
