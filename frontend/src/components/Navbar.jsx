import React from 'react';
import { Shield, LogOut, LayoutDashboard, History, UserCheck, Cpu } from 'lucide-react';

export default function Navbar({ currentUser, onNavigate, onLogout, currentView }) {
  if (!currentUser) return null;

  const isAdmin = currentUser.role === 'admin';

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand / Logo */}
        <div 
          onClick={() => onNavigate(isAdmin ? 'admin' : 'home')} 
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="p-2 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-lg text-white tracking-wide">Disaster Damage <span className="text-cyan-400">Assessment</span></span>
            <span className="block text-[10px] text-slate-400 font-mono tracking-wider uppercase">Satellite & AI Evaluation Engine</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex items-center gap-2 sm:gap-4">
          {!isAdmin ? (
            <>
              <button
                onClick={() => onNavigate('home')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentView === 'home' 
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' 
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Assess</span>
              </button>

              <button
                onClick={() => onNavigate('history')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentView === 'history' 
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' 
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <History className="w-4 h-4" />
                <span>History</span>
              </button>

              <button
                onClick={() => onNavigate('model_details')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentView === 'model_details' 
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' 
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Cpu className="w-4 h-4" />
                <span>Model Details</span>
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold">
              <UserCheck className="w-3.5 h-3.5" />
              <span>Admin Portal</span>
            </div>
          )}

          {/* User Profile & Logout */}
          <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
            <div className="hidden md:block text-right">
              <span className="block text-sm font-semibold text-slate-200">{currentUser.name}</span>
              <span className="block text-xs text-slate-400">{currentUser.email}</span>
            </div>

            <button
              onClick={onLogout}
              title="Log Out"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
}
