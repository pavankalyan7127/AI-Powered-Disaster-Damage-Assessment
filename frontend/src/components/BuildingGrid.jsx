import React, { useState } from 'react';
import { Eye, AlertCircle, CheckCircle, Clock, ChevronRight } from 'lucide-react';
import { getImageUrl } from '../config';

export function BuildingCard({ building, reviewStatus, onRequestReview, onOpenDetail }) {
  const preUrl = getImageUrl(building.pre_image);
  const postUrl = getImageUrl(building.post_image);

  const conf = building.confidence || 0;
  const isLowConfidence = conf < 0.8;

  const getDamageBadge = (label) => {
    switch (label?.toLowerCase()) {
      case 'no-damage':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'minor-damage':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'major-damage':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'destroyed':
        return 'bg-rose-500/10 text-rose-500 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 hover:border-slate-700 transition-all flex flex-col justify-between group">
      
      {/* Top Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono font-bold text-slate-300 truncate max-w-[140px]">
          {building.building_id || 'Building'}
        </span>

        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border tracking-wider ${getDamageBadge(building.predicted_label)}`}>
          {building.predicted_label || 'Unknown'}
        </span>
      </div>

      {/* Pre/Post Image Thumbnail Pair */}
      <div 
        onClick={() => onOpenDetail(building)}
        className="grid grid-cols-2 gap-2 mb-4 cursor-pointer"
      >
        <div className="relative aspect-square rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
          <img src={preUrl} alt="Pre" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
          <span className="absolute bottom-1 left-1 px-1.5 py-0.5 bg-slate-950/80 backdrop-blur-sm text-[9px] font-bold text-slate-300 rounded">PRE</span>
        </div>

        <div className="relative aspect-square rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
          <img src={postUrl} alt="Post" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
          <span className="absolute bottom-1 left-1 px-1.5 py-0.5 bg-slate-950/80 backdrop-blur-sm text-[9px] font-bold text-slate-300 rounded">POST</span>
        </div>
      </div>

      {/* Confidence & Review Action */}
      <div className="space-y-3 pt-2 border-t border-slate-800/80">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium">Confidence:</span>
          <span className={`font-bold ${isLowConfidence ? 'text-amber-400' : 'text-cyan-400'}`}>
            {Math.round(conf * 100)}%
          </span>
        </div>

        {/* Review Action State */}
        {reviewStatus ? (
          <div className="p-2 bg-slate-950 rounded-xl border border-slate-800/80 flex items-center justify-between text-[11px]">
            <span className="text-slate-400 font-medium">Review Status:</span>
            <span className="font-bold text-cyan-400 capitalize">
              {reviewStatus.ADMIN_DECISION || 'Pending'}
            </span>
          </div>
        ) : isLowConfidence ? (
          <button
            onClick={() => onRequestReview(building)}
            className="w-full py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-bold rounded-xl transition-colors flex items-center justify-center gap-1.5"
          >
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Request Human Review</span>
          </button>
        ) : (
          <button
            onClick={() => onOpenDetail(building)}
            className="w-full py-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-medium rounded-xl transition-colors flex items-center justify-center gap-1"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Inspect Details</span>
          </button>
        )}
      </div>

    </div>
  );
}

export function BuildingGrid({ buildings, reviews, onRequestReview, onOpenDetail }) {
  const [filter, setFilter] = useState('all');

  const getReviewForBuilding = (buildingId) => {
    return (reviews || []).find(r => str(r.BUILDING_ID) === str(buildingId));
  };

  const str = (val) => String(val || '');

  const filtered = (buildings || []).filter(b => {
    if (filter === 'all') return true;
    if (filter === 'low_conf') return (b.confidence || 0) < 0.8;
    return b.predicted_label === filter;
  });

  return (
    <div className="space-y-6">
      
      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="text-lg font-bold text-white">Building Crop Predictions</h3>

        <div className="flex items-center gap-1 p-1 bg-slate-900 border border-slate-800 rounded-2xl overflow-x-auto">
          {['all', 'low_conf', 'no-damage', 'minor-damage', 'major-damage', 'destroyed'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-all ${
                filter === cat
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {cat === 'low_conf' ? 'Low Conf (<80%)' : cat.replace('-', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-3xl text-slate-500 text-sm">
          No building crops match the selected filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtered.map((b, idx) => (
            <BuildingCard
              key={b.building_id || idx}
              building={b}
              reviewStatus={getReviewForBuilding(b.building_id)}
              onRequestReview={onRequestReview}
              onOpenDetail={onOpenDetail}
            />
          ))}
        </div>
      )}

    </div>
  );
}
