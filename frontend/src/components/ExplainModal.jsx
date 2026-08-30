import React from 'react';
import { X, Sparkles, AlertCircle, ShieldAlert, CheckCircle2, Info, Loader2 } from 'lucide-react';
import { getImageUrl } from '../config';

export default function ExplainModal({ building, explanation, loading, error, onClose }) {
  if (!building) return null;

  const preUrl = getImageUrl(building.pre_image);
  const postUrl = getImageUrl(building.post_image);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto space-y-6">
        
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Visual Explanation</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white">
            Building {building.building_id || 'Crop'}
          </h2>
        </div>

        {/* Pre vs Post Thumbnail Pair */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider">Pre-Disaster Image</span>
            <div className="aspect-square rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
              <img src={preUrl} alt="Pre Disaster" className="w-full h-full object-cover" />
            </div>
          </div>

          <div className="space-y-1.5">
            <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider">Post-Disaster Image</span>
            <div className="aspect-square rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
              <img src={postUrl} alt="Post Disaster" className="w-full h-full object-cover" />
            </div>
          </div>
        </div>

        {/* AI Prediction & Confidence Banner */}
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
          <div>
            <span className="block text-slate-500 font-semibold uppercase tracking-wider mb-0.5">Authoritative CV Prediction</span>
            <span className="text-base font-extrabold text-white capitalize">{building.predicted_label}</span>
          </div>

          <div className="text-right">
            <span className="block text-slate-500 font-semibold uppercase tracking-wider mb-0.5">Model Confidence</span>
            <span className="text-base font-extrabold text-cyan-400">{Math.round((building.confidence || 0) * 100)}%</span>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="p-12 text-center bg-slate-950 border border-slate-800/80 rounded-2xl space-y-3">
            <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
            <p className="text-sm font-semibold text-slate-200">Analyzing visual changes with Gemini AI...</p>
            <p className="text-xs text-slate-500">Comparing structural contours, roof integrity, and debris accumulation.</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-center gap-3 text-rose-400 text-xs">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Gemini Explanation Response Body */}
        {explanation && !loading && (
          <div className="space-y-6">
            
            {/* Visual Changes Bullet Points */}
            {explanation.visual_changes && explanation.visual_changes.length > 0 && (
              <div className="space-y-2">
                <span className="block text-xs font-bold text-slate-300 uppercase tracking-wider">Observed Visual Changes</span>
                <ul className="space-y-2">
                  {explanation.visual_changes.map((item, idx) => (
                    <li key={idx} className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl text-xs text-slate-300 flex items-start gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-1.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* AI Explanation Narrative */}
            <div className="p-4 bg-cyan-950/20 border border-cyan-500/20 rounded-2xl space-y-2">
              <span className="block text-xs font-bold text-cyan-400 uppercase tracking-wider">AI Visual Narrative</span>
              <p className="text-xs text-slate-200 leading-relaxed">{explanation.explanation}</p>
            </div>

            {/* Evidence Level & Limitations Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="block text-slate-500 font-bold uppercase tracking-wider mb-1">Evidence Level</span>
                <span className="font-extrabold text-cyan-400 uppercase">{explanation.evidence_level || 'Medium'}</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="block text-slate-500 font-bold uppercase tracking-wider mb-1">Imagery Limitations</span>
                <span className="text-slate-300">{explanation.limitations || 'None reported.'}</span>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/60 flex items-center gap-2 text-[11px] text-slate-500">
              <Info className="w-4 h-4 shrink-0 text-slate-400" />
              <span>AI visual explanation is based on visible image differences and does not replace expert structural assessment.</span>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
