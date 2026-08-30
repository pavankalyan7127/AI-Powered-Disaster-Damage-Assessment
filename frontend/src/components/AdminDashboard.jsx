import React, { useState, useEffect } from 'react';
import { 
  UserCheck, CheckCircle2, XCircle, MessageSquare, Clock, Shield, AlertTriangle, 
  Loader2, Eye, Sparkles, X, ArrowLeft, Building2 
} from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL, getImageUrl } from '../config';

export default function AdminDashboard({ currentUser }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeReview, setActiveReview] = useState(null);
  
  // Detailed Building Data fetched when activeReview is selected
  const [detailedBuilding, setDetailedBuilding] = useState(null);
  const [assessmentMeta, setAssessmentMeta] = useState(null);
  const [fetchingDetails, setFetchingDetails] = useState(false);

  // Gemini AI Visual Explanation State
  const [explanation, setExplanation] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState('');

  // Admin Decision Form State
  const [reviewNote, setReviewNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchPendingReviews = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/admin/reviews`);
      setReviews(res.data || []);
    } catch (err) {
      console.error("Failed to fetch pending admin reviews:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingReviews();
  }, []);

  // When activeReview is selected, fetch full assessment JSON to extract complete building details & probabilities
  const handleOpenBuildingDetail = async (review) => {
    setActiveReview(review);
    setReviewNote('');
    setExplanation(null);
    setExplainError('');
    setDetailedBuilding(null);
    setAssessmentMeta(null);

    if (!review.USER_ID || !review.ASSESSMENT_ID) return;

    setFetchingDetails(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/history/${review.USER_ID}/${review.ASSESSMENT_ID}`);
      const fullAssessment = res.data;
      setAssessmentMeta(fullAssessment);

      // Find specific building
      const buildings = fullAssessment.BUILDINGS || [];
      const found = buildings.find(
        b => String(b.building_id).strip() === String(review.BUILDING_ID).strip() ||
             String(b.folder).strip() === String(review.BUILDING_ID).strip()
      );

      if (found) {
        setDetailedBuilding(found);
      }
    } catch (err) {
      console.error("Failed to load complete assessment data for admin review:", err);
    } finally {
      setFetchingDetails(false);
    }
  };

  const handleExplainAI = async () => {
    if (!activeReview) return;
    setExplainLoading(true);
    setExplainError('');

    try {
      const res = await axios.post(`${API_BASE_URL}/api/explain`, {
        user_id: String(activeReview.USER_ID),
        assessment_id: String(activeReview.ASSESSMENT_ID),
        building_id: String(activeReview.BUILDING_ID)
      });
      setExplanation(res.data);
    } catch (err) {
      setExplainError(
        err.response?.data?.detail || 'Unable to generate AI explanation.'
      );
    } finally {
      setExplainLoading(false);
    }
  };

  const handleDecision = async (approved, decision) => {
    if (!activeReview) return;
    setSubmitting(true);
    try {
      await axios.put(`${API_BASE_URL}/api/admin/reviews/${activeReview.id}`, {
        approved: approved,
        admin_decision: decision,
        review_note: reviewNote
      });

      setActiveReview(null);
      setDetailedBuilding(null);
      setAssessmentMeta(null);
      setReviewNote('');
      fetchPendingReviews();
    } catch (err) {
      console.error("Failed to submit review decision:", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      
      {/* Admin Header */}
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-white">Admin Portal — Human-in-the-Loop Review</h1>
            <p className="text-xs text-slate-400">Inspect full building assessment records, pre/post imagery, and model probabilities before approving or overriding AI predictions</p>
          </div>
        </div>

        <button
          onClick={fetchPendingReviews}
          className="px-4 py-2 bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white rounded-xl transition-colors"
        >
          Refresh Pending Queue
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
          <span>Fetching pending review queue...</span>
        </div>
      ) : reviews.length === 0 ? (
        <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-3xl text-slate-400 text-sm">
          No pending human-review requests found. All clear!
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reviews.map((rev) => (
            <div
              key={rev.id}
              className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4 hover:border-amber-500/40 transition-colors flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-400">User ID: {rev.USER_ID}</span>
                  <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold uppercase text-[10px]">
                    Pending
                  </span>
                </div>

                <div>
                  <span className="block text-xs text-slate-500">Building ID</span>
                  <span className="font-bold text-white text-base font-mono">{rev.BUILDING_ID}</span>
                </div>

                {/* Crop Pair Thumbnails */}
                {(rev.PRE_IMAGE || rev.POST_IMAGE) && (
                  <div className="grid grid-cols-2 gap-2">
                    <div className="aspect-square bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
                      <img src={getImageUrl(rev.PRE_IMAGE)} alt="Pre" className="w-full h-full object-cover" />
                    </div>
                    <div className="aspect-square bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
                      <img src={getImageUrl(rev.POST_IMAGE)} alt="Post" className="w-full h-full object-cover" />
                    </div>
                  </div>
                )}

                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">AI Prediction:</span>
                    <span className="font-bold text-white capitalize">{rev.AI_PREDICTION}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Confidence:</span>
                    <span className="font-bold text-amber-400">{Math.round(rev.CONFIDENCE * 100)}%</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleOpenBuildingDetail(rev)}
                className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-amber-600/20 transition-all flex items-center justify-center gap-2"
              >
                <Eye className="w-4 h-4" />
                <span>Open Complete Assessment View</span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Complete Admin Building Detail View Modal */}
      {activeReview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto space-y-6">
            
            {/* Close Button */}
            <button
              onClick={() => { setActiveReview(null); setDetailedBuilding(null); }}
              className="absolute top-6 right-6 p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Header / Identification */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block mb-1">Admin Building Inspection</span>
                <h2 className="text-2xl font-extrabold text-white font-mono">Building {activeReview.BUILDING_ID}</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Requested by User ID: <strong className="text-slate-200">{activeReview.USER_ID}</strong> • Assessment ID: <strong className="text-cyan-400 font-mono">{activeReview.ASSESSMENT_ID}</strong>
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 font-semibold uppercase">
                  {activeReview.AI_PREDICTION}
                </span>
                <span className="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-400 font-bold">
                  {Math.round(activeReview.CONFIDENCE * 100)}% Conf
                </span>
              </div>
            </div>

            {/* Pre vs Post Image Comparison Grid */}
            <div className="space-y-2">
              <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider">Satellite Crop Imagery</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] text-slate-500 font-semibold block uppercase">Pre-Disaster Image</span>
                  <div className="aspect-square rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
                    <img src={getImageUrl(activeReview.PRE_IMAGE || detailedBuilding?.pre_image)} alt="Pre Disaster" className="w-full h-full object-cover" />
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] text-slate-500 font-semibold block uppercase">Post-Disaster Image</span>
                  <div className="aspect-square rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
                    <img src={getImageUrl(activeReview.POST_IMAGE || detailedBuilding?.post_image)} alt="Post Disaster" className="w-full h-full object-cover" />
                  </div>
                </div>
              </div>
            </div>

            {/* Authoritative Model Prediction & Class Probabilities Section */}
            <div className="p-6 bg-slate-950 border border-slate-800 rounded-2xl space-y-4">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Authoritative Model Metrics & Class Breakdown</h3>
              
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="block text-slate-500">CV Prediction</span>
                  <span className="font-extrabold text-white text-sm capitalize">{activeReview.AI_PREDICTION}</span>
                </div>

                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="block text-slate-500">Model Confidence</span>
                  <span className="font-extrabold text-amber-400 text-sm">{Math.round(activeReview.CONFIDENCE * 100)}%</span>
                </div>

                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="block text-slate-500">Input Mode</span>
                  <span className="font-bold text-slate-200 text-sm uppercase">{assessmentMeta?.INPUT_MODE || 'Satellite'}</span>
                </div>

                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="block text-slate-500">Crop Dimensions</span>
                  <span className="font-bold text-slate-200 text-sm">128 × 128 px</span>
                </div>
              </div>

              {/* Class Probability Breakdown if available */}
              {detailedBuilding?.probabilities && (
                <div className="pt-2 space-y-2">
                  <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Class Probabilities</span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    {Object.entries(detailedBuilding.probabilities).map(([label, val]) => (
                      <div key={label} className="p-2.5 bg-slate-900 rounded-xl border border-slate-800 space-y-1">
                        <div className="flex justify-between text-[11px] font-semibold text-slate-300 capitalize">
                          <span>{label}</span>
                          <span>{Math.round(val * 100)}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                          <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${val * 100}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Optional Gemini AI Visual Explanation Section */}
            <div className="p-6 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">Gemini AI Visual Explanation Assistance</span>
                </div>

                {!explanation && !explainLoading && (
                  <button
                    onClick={handleExplainAI}
                    className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-xl shadow transition-colors flex items-center gap-1"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Explain AI</span>
                  </button>
                )}
              </div>

              {explainLoading && (
                <div className="p-4 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                  <span>Generating visual explanation via Gemini...</span>
                </div>
              )}

              {explainError && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs">
                  {explainError}
                </div>
              )}

              {explanation && (
                <div className="space-y-3 text-xs">
                  {explanation.visual_changes && (
                    <ul className="space-y-1">
                      {explanation.visual_changes.map((vc, i) => (
                        <li key={i} className="text-slate-300 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-1.5" />
                          <span>{vc}</span>
                        </li>
                      ))}
                    </ul>
                  )}

                  <p className="p-3 bg-cyan-950/30 border border-cyan-500/20 rounded-xl text-slate-200 leading-relaxed">
                    {explanation.explanation}
                  </p>
                </div>
              )}
            </div>

            {/* Admin Decision & Justification Form */}
            <div className="p-6 bg-slate-950 border border-amber-500/30 rounded-2xl space-y-4">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block">Admin Review Decision & Justification</span>

              <textarea
                rows={3}
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                placeholder="Enter reviewer note or decision justification (e.g. Satellite crop confirms structural collapse)."
                className="w-full p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500"
              />

              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  disabled={submitting}
                  onClick={() => handleDecision(true, 'approved')}
                  className="py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 text-xs"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve CV Prediction</span>
                </button>

                <button
                  disabled={submitting}
                  onClick={() => handleDecision(true, 'overridden')}
                  className="py-3 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl shadow-lg shadow-rose-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 text-xs"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Override Prediction</span>
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
