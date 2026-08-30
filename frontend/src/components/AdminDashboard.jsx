import React, { useState, useEffect } from 'react';
import { UserCheck, CheckCircle2, XCircle, MessageSquare, Clock, Shield, AlertTriangle, Loader2 } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL, getImageUrl } from '../config';

export default function AdminDashboard({ currentUser }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeReview, setActiveReview] = useState(null);
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
            <p className="text-xs text-slate-400">Review low-confidence AI predictions flagged by disaster response teams</p>
          </div>
        </div>

        <button
          onClick={fetchPendingReviews}
          className="px-4 py-2 bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white rounded-xl transition-colors"
        >
          Refresh Pending
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
                onClick={() => { setActiveReview(rev); setReviewNote(''); }}
                className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-amber-600/20 transition-all flex items-center justify-center gap-2"
              >
                <span>Review Request</span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Admin Decision Modal */}
      {activeReview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
            
            <div>
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block mb-1">Building Review</span>
              <h3 className="text-xl font-extrabold text-white font-mono">{activeReview.BUILDING_ID}</h3>
            </div>

            <div className="space-y-3">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                Reviewer Note / Decision Justification
              </label>
              <textarea
                rows={3}
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                placeholder="e.g. Satellite comparison confirms significant structural collapse."
                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                disabled={submitting}
                onClick={() => handleDecision(true, 'approved')}
                className="py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 text-xs"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Approve Prediction</span>
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

            <button
              onClick={() => setActiveReview(null)}
              className="w-full py-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>

          </div>
        </div>
      )}

    </div>
  );
}
