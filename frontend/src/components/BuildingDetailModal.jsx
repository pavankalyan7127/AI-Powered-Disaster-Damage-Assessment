import React from 'react';
import { X, ExternalLink, ShieldCheck, AlertCircle, MessageSquare } from 'lucide-react';
import { getImageUrl } from '../config';

export default function BuildingDetailModal({ building, reviewStatus, onRequestReview, onClose }) {
  if (!building) return null;

  const preUrl = getImageUrl(building.pre_image);
  const postUrl = getImageUrl(building.post_image);

  const conf = building.confidence || 0;
  const isLowConfidence = conf < 0.8;
  const probs = building.probabilities || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
        
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <span>Building Identifier</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white">{building.building_id || 'Building Crop'}</h2>
        </div>

        {/* Pre vs Post Comparison Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
          <div className="space-y-2">
            <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider">Pre-Disaster Image</span>
            <div className="aspect-square rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-inner">
              <img src={preUrl} alt="Pre Disaster" className="w-full h-full object-cover" />
            </div>
          </div>

          <div className="space-y-2">
            <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider">Post-Disaster Image</span>
            <div className="aspect-square rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-inner">
              <img src={postUrl} alt="Post Disaster" className="w-full h-full object-cover" />
            </div>
          </div>
        </div>

        {/* Inference & Probabilities Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 p-6 bg-slate-950 border border-slate-800 rounded-2xl">
          <div>
            <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Predicted Class</span>
            <span className="text-xl font-bold text-white capitalize">{building.predicted_label || 'N/A'}</span>
            
            <div className="mt-4">
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">AI Confidence</span>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-extrabold text-cyan-400">{Math.round(conf * 100)}%</span>
                {isLowConfidence ? (
                  <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
                    Low Confidence (&lt;80%)
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                    High Confidence
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Probability Breakdown Bars */}
          <div className="space-y-2">
            <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Class Probabilities</span>
            {Object.entries(probs).map(([label, val]) => (
              <div key={label} className="space-y-1">
                <div className="flex justify-between text-xs font-medium text-slate-300 capitalize">
                  <span>{label}</span>
                  <span>{Math.round(val * 100)}%</span>
                </div>
                <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                    style={{ width: `${val * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Human Review Status / Action Section */}
        <div className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Human-in-the-Loop Review</span>
            {reviewStatus ? (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-cyan-400 capitalize">
                    Status: {reviewStatus.ADMIN_DECISION || (reviewStatus.APPROVED ? 'Approved' : 'Pending Review')}
                  </span>
                </div>
                {reviewStatus.REVIEW_NOTE && (
                  <p className="text-xs text-slate-300 italic flex items-center gap-1.5 mt-1">
                    <MessageSquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    <span>"{reviewStatus.REVIEW_NOTE}"</span>
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                {isLowConfidence 
                  ? 'Model confidence is below 80%. You may submit this building for human expert verification.'
                  : 'High confidence prediction. Human review not required.'}
              </p>
            )}
          </div>

          {isLowConfidence && !reviewStatus && (
            <button
              onClick={() => onRequestReview(building)}
              className="shrink-0 px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-amber-600/20 transition-all flex items-center gap-2"
            >
              <AlertCircle className="w-4 h-4" />
              <span>Request Human Review</span>
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
