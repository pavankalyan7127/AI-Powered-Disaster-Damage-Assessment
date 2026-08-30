import React from 'react';
import { Shield, ArrowRight, Activity, Globe, Eye, CheckCircle2 } from 'lucide-react';

export default function LandingPage({ onOpenLogin, onOpenSignup }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-cyan-500 selection:text-white">
      
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-600 text-white shadow-lg shadow-cyan-500/20">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <span className="font-extrabold text-xl text-white tracking-wide">Disaster Damage <span className="text-cyan-400">Assessment</span></span>
              <span className="block text-[10px] text-slate-400 font-mono tracking-widest uppercase">Emergency Satellite Assessment Engine</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={onOpenLogin}
              className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white transition-colors"
            >
              Login
            </button>
            <button
              onClick={onOpenSignup}
              className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-cyan-600/25 transition-all transform hover:-translate-y-0.5"
            >
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center relative overflow-hidden py-20 px-4 sm:px-6 lg:px-8">
        {/* Background Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute bottom-10 left-1/3 w-[400px] h-[200px] bg-blue-600/10 blur-[100px] rounded-full pointer-events-none" />

        <div className="relative z-10 max-w-4xl text-center space-y-8">
          
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold tracking-wide uppercase shadow-sm">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            <span>Siamese ResNet-50 Neural Network Engine</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
            AI-Powered Disaster <br />
            <span className="bg-gradient-to-r from-cyan-400 via-sky-400 to-blue-500 bg-clip-text text-transparent">
              Damage Assessment
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Compare pre- and post-disaster satellite imagery automatically. Instantly extract building footprints, classify damage severity, and mobilize emergency response teams with high precision.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onOpenSignup}
              className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-2xl shadow-xl shadow-cyan-600/25 transition-all transform hover:-translate-y-1 flex items-center justify-center gap-3 text-base"
            >
              <span>Start Damage Assessment</span>
              <ArrowRight className="w-5 h-5" />
            </button>

            <button
              onClick={onOpenLogin}
              className="w-full sm:w-auto px-8 py-4 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 font-semibold rounded-2xl transition-all flex items-center justify-center gap-2 text-base"
            >
              <span>Demo Login</span>
            </button>
          </div>

          {/* Feature Highlights Grid */}
          <div className="pt-16 grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
            <div className="p-6 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-sm">
              <Globe className="w-8 h-8 text-cyan-400 mb-4" />
              <h3 className="font-bold text-lg text-white mb-1">Satellite Windowing</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Direct raster windowing reads high-resolution GeoTIFF files efficiently without blowing up memory.
              </p>
            </div>

            <div className="p-6 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-sm">
              <Eye className="w-8 h-8 text-amber-400 mb-4" />
              <h3 className="font-bold text-lg text-white mb-1">Human-in-the-Loop</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Sub-80% confidence building assessments automatically trigger human review for expert verification.
              </p>
            </div>

            <div className="p-6 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-sm">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-4" />
              <h3 className="font-bold text-lg text-white mb-1">Instant Analytics</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Aggregated damage distributions, building confidence maps, and historical audit trail for rapid decisions.
              </p>
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>© 2026 Disaster Damage Assessment System. Hackathon Demonstration Prototype.</p>
      </footer>
    </div>
  );
}
