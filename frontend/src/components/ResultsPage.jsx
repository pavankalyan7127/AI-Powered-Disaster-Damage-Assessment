import React, { useState } from 'react';
import { ArrowLeft, Clock, ShieldCheck } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { StatisticsCards, DamageChart } from './StatisticsCards';
import { BuildingGrid } from './BuildingGrid';

export default function ResultsPage({ assessment, currentUser, onBack, onOpenBuildingDetail }) {
  const [reviews, setReviews] = useState([]);
  const [notification, setNotification] = useState('');

  const fetchUserReviews = async () => {
    if (!currentUser) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/api/review/user/${currentUser.id}`);
      setReviews(res.data || []);
    } catch (err) {
      console.error("Failed to fetch user reviews:", err);
    }
  };

  React.useEffect(() => {
    fetchUserReviews();
  }, [currentUser]);

  const handleRequestReview = async (building) => {
    if (!currentUser || !assessment) return;

    try {
      await axios.post(`${API_BASE_URL}/api/review`, {
        user_id: String(currentUser.id),
        assessment_id: String(assessment.ASSESSMENT_ID),
        building_id: String(building.building_id),
        ai_prediction: String(building.predicted_label),
        confidence: Number(building.confidence),
        pre_image: building.pre_image,
        post_image: building.post_image
      });

      setNotification(`Human review requested for building ${building.building_id}`);
      setTimeout(() => setNotification(''), 4000);
      fetchUserReviews();
    } catch (err) {
      console.error("Failed to request human review:", err);
    }
  };

  if (!assessment) return null;

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-extrabold text-white">Assessment Results</h1>
              <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs font-semibold">
                {assessment.ASSESSMENT_ID}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5" />
              <span>Processed: {assessment.TIMESTAMP}</span>
            </p>
          </div>
        </div>
      </div>

      {notification && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl text-emerald-400 text-xs font-semibold flex items-center gap-2">
          <ShieldCheck className="w-4 h-4" />
          <span>{notification}</span>
        </div>
      )}

      {/* Aggregate Statistics Header */}
      <StatisticsCards summary={assessment} />

      {/* Charts & Distribution Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <DamageChart summary={assessment} />
        </div>

        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between">
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Assessment Metadata</h3>
            
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="block text-slate-500 font-medium">Input Mode</span>
                <span className="font-bold text-white uppercase">{assessment.INPUT_MODE || 'Satellite'}</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="block text-slate-500 font-medium">Total Crops Evaluated</span>
                <span className="font-bold text-cyan-400">{assessment.TOTAL_BUILDINGS}</span>
              </div>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed pt-2">
              Click any building card below to open its dedicated <span className="text-cyan-400 font-semibold">Building Detail Page</span> with pre/post imagery comparison, class probability breakdown, Gemini AI Visual Explanation, and building-specific AI Assistant Chat.
            </p>
          </div>
        </div>
      </div>

      {/* Building Crop Grid */}
      <BuildingGrid
        buildings={assessment.BUILDINGS || []}
        reviews={reviews}
        onRequestReview={handleRequestReview}
        onOpenDetail={(building) => onOpenBuildingDetail(building)}
      />

    </div>
  );
}
