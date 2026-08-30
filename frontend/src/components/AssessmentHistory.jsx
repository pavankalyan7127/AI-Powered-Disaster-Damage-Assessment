import React, { useState, useEffect } from 'react';
import { History as HistoryIcon, Clock, ArrowRight, Building2, ChevronRight, Loader2 } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export default function AssessmentHistory({ currentUser, onSelectAssessment }) {
  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentUser) return;
    const loadHistory = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/history/${currentUser.id}`);
        setHistoryList(res.data || []);
      } catch (err) {
        console.error("Failed to load history:", err);
      } finally {
        setLoading(false);
      }
    };
    loadHistory();
  }, [currentUser]);

  const handleCardClick = async (item) => {
    // Fetch full assessment JSON if buildings array is omitted in metadata
    if (!item.BUILDINGS || item.BUILDINGS.length === 0) {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/history/${currentUser.id}/${item.ASSESSMENT_ID}`);
        onSelectAssessment(res.data);
        return;
      } catch (err) {
        console.error("Failed to fetch complete assessment details:", err);
      }
    }
    onSelectAssessment(item);
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400 flex flex-col items-center gap-3">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        <span>Loading assessment history...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <HistoryIcon className="w-6 h-6 text-cyan-400" />
        <div>
          <h2 className="text-xl font-bold text-white">Assessment History</h2>
          <p className="text-xs text-slate-400">Past disaster assessment runs and saved building crop predictions</p>
        </div>
      </div>

      {historyList.length === 0 ? (
        <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-3xl text-slate-500 text-sm">
          No previous assessment history found for your account.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {historyList.map((item) => {
            const dist = item.DAMAGE_DISTRIBUTION || {};
            return (
              <div
                key={item.id || item.ASSESSMENT_ID}
                onClick={() => handleCardClick(item)}
                className="p-6 bg-slate-900 border border-slate-800 hover:border-cyan-500/50 rounded-2xl cursor-pointer transition-all hover:scale-[1.01] space-y-4 group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2.5 py-1 rounded-lg">
                    {item.ASSESSMENT_ID}
                  </span>
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{item.TIMESTAMP}</span>
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="block text-slate-500">Buildings Evaluated</span>
                    <span className="font-bold text-white text-base">{item.TOTAL_BUILDINGS}</span>
                  </div>

                  <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="block text-slate-500">Avg Confidence</span>
                    <span className="font-bold text-sky-400 text-base">{item.AVERAGE_CONFIDENCE}%</span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs">
                  <div className="flex items-center gap-2 text-[11px] font-semibold">
                    <span className="text-emerald-400">{dist['no-damage'] || 0} Undamaged</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-rose-400">{dist['destroyed'] || 0} Destroyed</span>
                  </div>

                  <div className="flex items-center gap-1 text-cyan-400 font-semibold group-hover:translate-x-1 transition-transform">
                    <span>View Results</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
