import React from 'react';
import { 
  Cpu, Database, Layers, CheckCircle2, AlertTriangle, Flame, ShieldAlert, 
  Percent, ArrowRight, Activity, GitBranch, ShieldCheck
} from 'lucide-react';

export default function ModelDetailsPage({ onBack }) {
  const confusionMatrix = [
    { label: 'no-damage', actual: 'no-damage', pred_no: 591, pred_minor: 220, pred_major: 250, pred_destroyed: 311, total: 1372, accuracy: '43.08%' },
    { label: 'minor-damage', actual: 'minor-damage', pred_no: 74, pred_minor: 1878, pred_major: 809, pred_destroyed: 304, total: 3065, accuracy: '61.27%' },
    { label: 'major-damage', actual: 'major-damage', pred_no: 9, pred_minor: 120, pred_major: 881, pred_destroyed: 155, total: 1165, accuracy: '75.62%' },
    { label: 'destroyed', actual: 'destroyed', pred_no: 7, pred_minor: 24, pred_major: 70, pred_destroyed: 1200, total: 1301, accuracy: '92.24%' }
  ];

  return (
    <div className="space-y-12 animate-fade-in pb-16">
      
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Cpu className="w-3.5 h-3.5" />
            <span>AI Architecture & Evaluation Dashboard</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">Siamese ResNet-50 Damage Classifier</h1>
          <p className="text-xs text-slate-400 mt-1">Technical specifications, xBD dataset statistics, training logs, and test performance matrix for Hackathon judges</p>
        </div>

        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-slate-900 border border-slate-800 text-xs font-bold text-slate-300 hover:text-white rounded-xl transition-colors"
          >
            Back to Assessment
          </button>
        )}
      </div>

      {/* SECTION 1: MODEL OVERVIEW & TOP METRICS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-1">
          <span className="block text-xs text-slate-500 font-semibold uppercase">Architecture</span>
          <span className="text-xl font-extrabold text-white">Siamese ResNet-50</span>
          <span className="block text-[10px] text-cyan-400">Shared Feature Extractor</span>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-1">
          <span className="block text-xs text-slate-500 font-semibold uppercase">Training Accuracy</span>
          <span className="text-xl font-extrabold text-emerald-400">76.42%</span>
          <span className="block text-[10px] text-slate-400">30,413 Training Crops</span>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-1">
          <span className="block text-xs text-slate-500 font-semibold uppercase">Validation Accuracy</span>
          <span className="text-xl font-extrabold text-sky-400">70.35%</span>
          <span className="block text-[10px] text-slate-400">6,583 Validation Crops</span>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-1">
          <span className="block text-xs text-slate-500 font-semibold uppercase">Held-Out Test Accuracy</span>
          <span className="text-xl font-extrabold text-amber-400">65.91%</span>
          <span className="block text-[10px] text-slate-400">6,903 Test Samples Evaluated</span>
        </div>
      </div>

      {/* SECTION 2: DATASET & PREPROCESSING PIPELINE */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          <h2 className="text-xl font-bold text-white">Dataset & Preprocessing (xBD Benchmark)</h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="block text-slate-500">Raw Dataset</span>
            <span className="font-bold text-white text-sm">xBD Satellite Corpus</span>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="block text-slate-500">Image Pairs Discovered</span>
            <span className="font-bold text-cyan-400 text-sm">200 Pairs</span>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="block text-slate-500">Total Crop Pair Samples</span>
            <span className="font-bold text-white text-sm">43,899 Crops</span>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="block text-slate-500">Crop Dimensions & BBox Padding</span>
            <span className="font-bold text-slate-200 text-sm">128×128 px (10px pad)</span>
          </div>
        </div>

        {/* Dataset Split Summary */}
        <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-3">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">70 / 15 / 15 Split Breakdown</span>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="flex items-center justify-between p-2.5 bg-slate-900 rounded-xl border border-slate-800">
              <span className="text-slate-400 font-semibold">Training Set (70%)</span>
              <span className="font-bold text-emerald-400">30,413 crops</span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-slate-900 rounded-xl border border-slate-800">
              <span className="text-slate-400 font-semibold">Validation Set (15%)</span>
              <span className="font-bold text-sky-400">6,583 crops</span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-slate-900 rounded-xl border border-slate-800">
              <span className="text-slate-400 font-semibold">Testing Set (15%)</span>
              <span className="font-bold text-amber-400">6,903 crops</span>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: SIAMESE MODEL ARCHITECTURE */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <h2 className="text-xl font-bold text-white">Siamese ResNet-50 Architecture</h2>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
          The disaster model employs twin ResNet-50 convolutional backbones with shared weights. Pre-disaster and post-disaster 128×128 building crops are passed in parallel, generating high-dimensional feature embeddings. The difference and concatenation vectors pass through dense linear layers to output 4 damage severity class logits.
        </p>

        {/* Architecture Flowchart Diagram */}
        <div className="p-6 bg-slate-950 border border-slate-800 rounded-2xl font-mono text-xs flex flex-col md:flex-row items-center justify-around gap-4 text-center">
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="block font-bold text-cyan-400">PRE Crop (128x128)</span>
            <span className="text-[10px] text-slate-500">Input Image</span>
          </div>

          <ArrowRight className="w-5 h-5 text-slate-600 hidden md:block" />

          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="block font-bold text-white">Shared ResNet-50 Encoder</span>
            <span className="text-[10px] text-slate-500">Weight Sharing</span>
          </div>

          <ArrowRight className="w-5 h-5 text-slate-600 hidden md:block" />

          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="block font-bold text-white">Feature Difference Vector</span>
            <span className="text-[10px] text-slate-500">|F_pre - F_post|</span>
          </div>

          <ArrowRight className="w-5 h-5 text-slate-600 hidden md:block" />

          <div className="p-3 bg-cyan-950 border border-cyan-500/30 rounded-xl">
            <span className="block font-bold text-cyan-300">4-Class Damage Classifier</span>
            <span className="text-[10px] text-cyan-400">Logits → Softmax</span>
          </div>
        </div>
      </div>

      {/* SECTION 4 & 5: TRAINING METRICS & TESTING RESULTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Training Epoch Metrics */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white">Training Metrics Log</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase">
                  <th className="py-2.5 px-3">Epoch</th>
                  <th className="py-2.5 px-3">Train Loss</th>
                  <th className="py-2.5 px-3">Train Acc</th>
                  <th className="py-2.5 px-3">Val Loss</th>
                  <th className="py-2.5 px-3">Val Acc</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                <tr>
                  <td className="py-2.5 px-3 text-cyan-400 font-bold">Epoch 1</td>
                  <td className="py-2.5 px-3">0.8240</td>
                  <td className="py-2.5 px-3 text-emerald-400">68.10%</td>
                  <td className="py-2.5 px-3">0.8749</td>
                  <td className="py-2.5 px-3 text-sky-400">69.48%</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 text-cyan-400 font-bold">Epoch 2</td>
                  <td className="py-2.5 px-3">0.6910</td>
                  <td className="py-2.5 px-3 text-emerald-400">73.65%</td>
                  <td className="py-2.5 px-3">3.3370</td>
                  <td className="py-2.5 px-3 text-sky-400">69.60%</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 text-cyan-400 font-bold">Epoch 3</td>
                  <td className="py-2.5 px-3">0.6226</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">76.42%</td>
                  <td className="py-2.5 px-3">1.0628</td>
                  <td className="py-2.5 px-3 text-sky-400 font-bold">70.35%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Test Evaluation Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white">Held-Out Test Set Evaluation</h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="block text-slate-500">Test Samples</span>
              <span className="text-base font-bold text-white font-mono">6,903</span>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="block text-slate-500">Test Loss</span>
              <span className="text-base font-bold text-slate-200 font-mono">1.0965</span>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="block text-slate-500">Correct Predictions</span>
              <span className="text-base font-bold text-emerald-400 font-mono">4,550</span>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="block text-slate-500">Incorrect Predictions</span>
              <span className="text-base font-bold text-rose-400 font-mono">2,353</span>
            </div>
          </div>
        </div>

      </div>

      {/* SECTION 6 & 7: CONFUSION MATRIX & CLASS PERFORMANCE */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
        <h2 className="text-xl font-bold text-white">Confusion Matrix & Class Accuracy Breakdown</h2>

        <div className="overflow-x-auto">
          <table className="w-full text-center text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-3 px-3 text-left">Actual \ Predicted</th>
                <th className="py-3 px-3 text-emerald-400">no-damage</th>
                <th className="py-3 px-3 text-amber-400">minor-damage</th>
                <th className="py-3 px-3 text-orange-400">major-damage</th>
                <th className="py-3 px-3 text-rose-400">destroyed</th>
                <th className="py-3 px-3 text-right">Class Accuracy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {confusionMatrix.map((row) => (
                <tr key={row.label} className="hover:bg-slate-950/40">
                  <td className="py-3 px-3 text-left font-bold text-slate-200 uppercase">{row.label}</td>
                  <td className={`py-3 px-3 ${row.actual === 'no-damage' ? 'bg-emerald-500/20 text-emerald-300 font-bold' : 'text-slate-400'}`}>{row.pred_no}</td>
                  <td className={`py-3 px-3 ${row.actual === 'minor-damage' ? 'bg-amber-500/20 text-amber-300 font-bold' : 'text-slate-400'}`}>{row.pred_minor}</td>
                  <td className={`py-3 px-3 ${row.actual === 'major-damage' ? 'bg-orange-500/20 text-orange-300 font-bold' : 'text-slate-400'}`}>{row.pred_major}</td>
                  <td className={`py-3 px-3 ${row.actual === 'destroyed' ? 'bg-rose-500/20 text-rose-300 font-bold' : 'text-slate-400'}`}>{row.pred_destroyed}</td>
                  <td className="py-3 px-3 text-right font-bold text-cyan-400">{row.accuracy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Class Performance Progress Bars */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-4">
          <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-2">
            <div className="flex justify-between text-xs font-bold text-emerald-400">
              <span>no-damage</span>
              <span>43.08%</span>
            </div>
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 rounded-full" style={{ width: '43.08%' }} />
            </div>
            <span className="block text-[10px] text-slate-500">591 / 1,372 Correct</span>
          </div>

          <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-2">
            <div className="flex justify-between text-xs font-bold text-amber-400">
              <span>minor-damage</span>
              <span>61.27%</span>
            </div>
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
              <div className="h-full bg-amber-500 rounded-full" style={{ width: '61.27%' }} />
            </div>
            <span className="block text-[10px] text-slate-500">1,878 / 3,065 Correct</span>
          </div>

          <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-2">
            <div className="flex justify-between text-xs font-bold text-orange-400">
              <span>major-damage</span>
              <span>75.62%</span>
            </div>
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
              <div className="h-full bg-orange-500 rounded-full" style={{ width: '75.62%' }} />
            </div>
            <span className="block text-[10px] text-slate-500">881 / 1,165 Correct</span>
          </div>

          <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-2">
            <div className="flex justify-between text-xs font-bold text-rose-500">
              <span>destroyed</span>
              <span>92.24%</span>
            </div>
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
              <div className="h-full bg-rose-500 rounded-full" style={{ width: '92.24%' }} />
            </div>
            <span className="block text-[10px] text-slate-500">1,200 / 1,301 Correct</span>
          </div>
        </div>
      </div>

    </div>
  );
}
