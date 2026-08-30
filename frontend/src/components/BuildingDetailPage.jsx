import React, { useState, useEffect, useRef } from 'react';
import { 
  ArrowLeft, Sparkles, Send, AlertCircle, ShieldCheck, CheckCircle2, 
  Info, Loader2, Bot, User, MessageSquare, Clock, Building2, Eye
} from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL, getImageUrl } from '../config';

export default function BuildingDetailPage({ building, assessment, currentUser, onBack }) {
  const [reviews, setReviews] = useState([]);
  const [reviewSubmitted, setReviewSubmitted] = useState(false);
  const [notification, setNotification] = useState('');

  // Explain AI State
  const [explanation, setExplanation] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainError, setExplainError] = useState('');

  // Chatbox State
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I am your AI Disaster Assessment Assistant. I am analyzing Building ID: ${building?.building_id || 'Crop'}. How can I assist you with this building's damage prediction or inspection?`
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState('');
  const chatBottomRef = useRef(null);

  // Fetch reviews for current user
  useEffect(() => {
    if (!currentUser) return;
    const fetchReviews = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/api/review/user/${currentUser.id}`);
        setReviews(res.data || []);
      } catch (err) {
        console.error("Failed to fetch user reviews:", err);
      }
    };
    fetchReviews();
  }, [currentUser]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatLoading]);

  if (!building || !assessment) return null;

  const preUrl = getImageUrl(building.pre_image);
  const postUrl = getImageUrl(building.post_image);
  const conf = building.confidence || 0;
  const isLowConfidence = conf < 0.8; // Trigger Human Review only for confidence < 80%

  const existingReview = reviews.find(
    r => String(r.BUILDING_ID) === String(building.building_id)
  );

  const handleRequestReview = async () => {
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

      setReviewSubmitted(true);
      setNotification(`Human review request submitted for Building ${building.building_id}`);
      setTimeout(() => setNotification(''), 4000);
    } catch (err) {
      console.error("Failed to request human review:", err);
    }
  };

  const handleExplainAI = async () => {
    if (!currentUser || !assessment) return;
    setExplainLoading(true);
    setExplainError('');

    try {
      const res = await axios.post(`${API_BASE_URL}/api/explain`, {
        user_id: String(currentUser.id),
        assessment_id: String(assessment.ASSESSMENT_ID),
        building_id: String(building.building_id)
      });
      setExplanation(res.data);
    } catch (err) {
      setExplainError(
        err.response?.data?.detail || 'Unable to generate AI explanation. Check backend GEMINI_API_KEY configuration.'
      );
    } finally {
      setExplainLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || chatLoading) return;

    const userMsg = inputMessage.trim();
    setInputMessage('');
    setChatError('');

    const newMessages = [...messages, { role: 'user', content: userMsg }];
    setMessages(newMessages);
    setChatLoading(true);

    try {
      const historyPayload = newMessages.slice(1, -1).map(m => ({
        role: m.role,
        content: m.content
      }));

      const res = await axios.post(`${API_BASE_URL}/api/building-chat`, {
        user_id: String(currentUser.id),
        assessment_id: String(assessment.ASSESSMENT_ID),
        building_id: String(building.building_id),
        message: userMsg,
        history: historyPayload
      });

      setMessages(prev => [...prev, { role: 'assistant', content: res.data.reply }]);
    } catch (err) {
      setChatError(err.response?.data?.detail || 'Failed to send chat message. Please try again.');
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      
      {/* Top Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors flex items-center gap-2 text-xs font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Results</span>
          </button>

          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-extrabold text-white font-mono">Building {building.building_id}</h1>
              <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs font-semibold">
                {assessment.ASSESSMENT_ID}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5" />
              <span>Assessment Date: {assessment.TIMESTAMP}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold uppercase">
            {building.predicted_label}
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-xs text-cyan-400 font-bold">
            {Math.round(conf * 100)}% Conf
          </span>
        </div>
      </div>

      {notification && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl text-emerald-400 text-xs font-semibold flex items-center gap-2">
          <ShieldCheck className="w-4 h-4" />
          <span>{notification}</span>
        </div>
      )}

      {/* Main Grid: Left Column = Imagery & Analysis, Right Column = AI Chatbot */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN (7 cols): Imagery, Details, Review, Visual Explanation */}
        <div className="lg:col-span-7 space-y-8">
          
          {/* Pre vs Post Image Comparison */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Satellite Image Crop Comparison</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
          </div>

          {/* Model Prediction & Metadata Details Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Authoritative AI Prediction & Details</h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="block text-slate-500 font-semibold uppercase">Prediction</span>
                <span className="text-sm font-extrabold text-white capitalize">{building.predicted_label}</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="block text-slate-500 font-semibold uppercase">Confidence</span>
                <span className="text-sm font-extrabold text-cyan-400">{Math.round(conf * 100)}%</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 col-span-2 sm:col-span-1">
                <span className="block text-slate-500 font-semibold uppercase">Crop Dimensions</span>
                <span className="text-sm font-extrabold text-slate-200">128 × 128 px</span>
              </div>
            </div>

            {/* Class Probabilities Bar Breakdown */}
            {building.probabilities && (
              <div className="pt-2 space-y-2">
                <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Class Probabilities</span>
                <div className="space-y-2">
                  {Object.entries(building.probabilities).map(([label, val]) => (
                    <div key={label} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium text-slate-300 capitalize">
                        <span>{label}</span>
                        <span>{Math.round(val * 100)}%</span>
                      </div>
                      <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                          style={{ width: `${val * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Human-in-the-Loop Review Section */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Human-in-the-Loop Protocol</span>
                {existingReview || reviewSubmitted ? (
                  <span className="text-sm font-bold text-cyan-400 capitalize flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>Review Status: {existingReview?.ADMIN_DECISION || 'Pending Human Review'}</span>
                  </span>
                ) : (
                  <p className="text-xs text-slate-400">
                    {isLowConfidence 
                      ? 'Model confidence is below 80%. You may submit this building to the Admin Review queue.'
                      : 'High confidence prediction (≥80%). Human review is restricted to low-confidence predictions (<80%).'}
                  </p>
                )}
              </div>

              {/* STRICT 80% RULE: Allow Request Human Review ONLY when confidence < 80% */}
              {isLowConfidence && !existingReview && !reviewSubmitted && (
                <button
                  onClick={handleRequestReview}
                  className="shrink-0 px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-amber-600/20 transition-all flex items-center gap-2"
                >
                  <AlertCircle className="w-4 h-4" />
                  <span>Request Human Review</span>
                </button>
              )}
            </div>

            {/* Display Admin Reviewer Note if available */}
            {existingReview?.REVIEW_NOTE && existingReview.REVIEW_NOTE.trim() !== '' && (
              <div className="p-4 bg-slate-950 border border-amber-500/30 rounded-2xl space-y-1.5 animate-fade-in">
                <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
                  <MessageSquare className="w-4 h-4" />
                  <span>Admin Reviewer Note</span>
                  {existingReview.REVIEWED_AT && (
                    <span className="text-[10px] text-slate-500 font-normal">({existingReview.REVIEWED_AT})</span>
                  )}
                </div>
                <p className="text-xs text-slate-200 italic leading-relaxed pl-6 border-l-2 border-amber-500/50">
                  "{existingReview.REVIEW_NOTE}"
                </p>
              </div>
            )}
          </div>

          {/* Gemini AI Visual Explanation Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Gemini AI Visual Explanation</h3>
              </div>

              {!explanation && !explainLoading && (
                <button
                  onClick={handleExplainAI}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-xl shadow-md transition-colors flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Explain with AI</span>
                </button>
              )}
            </div>

            {explainLoading && (
              <div className="p-8 text-center bg-slate-950 rounded-2xl space-y-2">
                <Loader2 className="w-6 h-6 text-cyan-400 animate-spin mx-auto" />
                <span className="text-xs text-slate-300 font-semibold block">Analyzing visual changes with Gemini AI...</span>
              </div>
            )}

            {explainError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs">
                {explainError}
              </div>
            )}

            {explanation && (
              <div className="space-y-4 text-xs">
                {explanation.visual_changes && (
                  <div className="space-y-1.5">
                    <span className="font-bold text-slate-300 block uppercase">Observed Changes:</span>
                    <ul className="space-y-1 pl-2">
                      {explanation.visual_changes.map((vc, i) => (
                        <li key={i} className="text-slate-300 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-1.5" />
                          <span>{vc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="p-3 bg-cyan-950/30 border border-cyan-500/20 rounded-xl">
                  <span className="font-bold text-cyan-400 block mb-1">Visual Reasoning Summary:</span>
                  <p className="text-slate-200 leading-relaxed">{explanation.explanation}</p>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                  <span>Evidence Level: <strong className="text-cyan-400 capitalize">{explanation.evidence_level || 'Medium'}</strong></span>
                  <span>Limitations: <strong className="text-slate-400">{explanation.limitations || 'None'}</strong></span>
                </div>
              </div>
            )}
          </div>

        </div>

        {/* RIGHT COLUMN (5 cols): Building-Specific AI Chatbot Panel */}
        <div className="lg:col-span-5">
          <div className="sticky top-24 bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col h-[700px] shadow-2xl">
            
            {/* Chat Header */}
            <div className="pb-4 border-b border-slate-800 mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-cyan-600/20 border border-cyan-500/30 text-cyan-400">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">AI Assistant</h3>
                  <span className="block text-[11px] font-mono text-cyan-400">Context: Building {building.building_id}</span>
                </div>
              </div>

              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold">
                Active
              </span>
            </div>

            {/* Chat Messages Scroll Container */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 text-xs ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-cyan-600 text-white font-medium rounded-tr-none'
                        : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none space-y-1'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-7 h-7 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              {chatLoading && (
                <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                  <span>AI assistant is analyzing building details...</span>
                </div>
              )}

              {chatError && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs">
                  {chatError}
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Chat Input Form */}
            <form onSubmit={handleSendMessage} className="pt-4 border-t border-slate-800 mt-4 space-y-2">
              <div className="relative flex items-center">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={`Ask about Building ${building.building_id}...`}
                  className="w-full pl-4 pr-12 py-3 bg-slate-950 border border-slate-800 rounded-2xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
                />
                <button
                  type="submit"
                  disabled={chatLoading || !inputMessage.trim()}
                  className="absolute right-2 p-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl transition-all disabled:opacity-40"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
                <Info className="w-3 h-3 text-slate-400 shrink-0" />
                <span>AI tools do not replace on-site certified engineering inspections.</span>
              </div>
            </form>

          </div>
        </div>

      </div>

    </div>
  );
}
