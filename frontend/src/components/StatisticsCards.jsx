import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { Building2, ShieldAlert, AlertTriangle, CheckCircle, Flame, Percent } from 'lucide-react';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

export function StatisticsCards({ summary }) {
  const dist = summary.DAMAGE_DISTRIBUTION || {};
  const total = summary.TOTAL_BUILDINGS || 0;
  const avgConf = summary.AVERAGE_CONFIDENCE || 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
      
      {/* Total Buildings */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl">
        <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold mb-2">
          <Building2 className="w-4 h-4 text-cyan-400" />
          <span>Total Buildings</span>
        </div>
        <span className="text-2xl font-extrabold text-white">{total.toLocaleString()}</span>
      </div>

      {/* No Damage */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl">
        <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold mb-2">
          <CheckCircle className="w-4 h-4" />
          <span>No Damage</span>
        </div>
        <span className="text-2xl font-extrabold text-emerald-400">{(dist['no-damage'] || 0).toLocaleString()}</span>
      </div>

      {/* Minor Damage */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl">
        <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold mb-2">
          <AlertTriangle className="w-4 h-4" />
          <span>Minor Damage</span>
        </div>
        <span className="text-2xl font-extrabold text-amber-400">{(dist['minor-damage'] || 0).toLocaleString()}</span>
      </div>

      {/* Major Damage */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl">
        <div className="flex items-center gap-2 text-orange-400 text-xs font-semibold mb-2">
          <ShieldAlert className="w-4 h-4" />
          <span>Major Damage</span>
        </div>
        <span className="text-2xl font-extrabold text-orange-400">{(dist['major-damage'] || 0).toLocaleString()}</span>
      </div>

      {/* Destroyed */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl">
        <div className="flex items-center gap-2 text-rose-500 text-xs font-semibold mb-2">
          <Flame className="w-4 h-4" />
          <span>Destroyed</span>
        </div>
        <span className="text-2xl font-extrabold text-rose-500">{(dist['destroyed'] || 0).toLocaleString()}</span>
      </div>

      {/* Average Confidence */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl col-span-2 lg:col-span-1">
        <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold mb-2">
          <Percent className="w-4 h-4" />
          <span>Avg Confidence</span>
        </div>
        <span className="text-2xl font-extrabold text-sky-400">{avgConf}%</span>
      </div>

    </div>
  );
}

export function DamageChart({ summary }) {
  const dist = summary.DAMAGE_DISTRIBUTION || {};

  const data = {
    labels: ['No Damage', 'Minor Damage', 'Major Damage', 'Destroyed'],
    datasets: [
      {
        data: [
          dist['no-damage'] || 0,
          dist['minor-damage'] || 0,
          dist['major-damage'] || 0,
          dist['destroyed'] || 0
        ],
        backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#ef4444'],
        borderColor: '#0f172a',
        borderWidth: 3,
        hoverOffset: 6
      }
    ]
  };

  const options = {
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#94a3b8', font: { family: 'sans-serif', size: 12 } }
      }
    },
    cutout: '70%',
    responsive: true,
    maintainAspectRatio: false
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 h-80 flex flex-col items-center justify-center">
      <h3 className="text-sm font-bold text-slate-300 mb-4 uppercase tracking-wider text-center">Damage Severity Breakdown</h3>
      <div className="w-full h-56 relative">
        <Doughnut data={data} options={options} />
      </div>
    </div>
  );
}
