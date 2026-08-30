import React, { useState } from 'react';
import { Layers, Image as ImageIcon, Zap, Upload, FileUp, Sparkles, AlertCircle } from 'lucide-react';

export default function InputSelector({ onStartSatellite, onStartBuilding, onStartNepalDemo, loading }) {
  const [activeTab, setActiveTab] = useState('satellite');

  // Mode A State
  const [satPre, setSatPre] = useState(null);
  const [satPost, setSatPost] = useState(null);
  const [satGeojson, setSatGeojson] = useState(null);

  // Mode B State
  const [cropPre, setCropPre] = useState(null);
  const [cropPost, setCropPost] = useState(null);

  const [error, setError] = useState('');

  const handleSatelliteSubmit = (e) => {
    e.preventDefault();
    setError('');
    if (!satPre || !satPost || !satGeojson) {
      setError('Please provide all three satellite inputs: Pre TIFF, Post TIFF, and Buildings GeoJSON.');
      return;
    }
    onStartSatellite({ pre_file: satPre, post_file: satPost, geojson_file: satGeojson });
  };

  const handleBuildingSubmit = (e) => {
    e.preventDefault();
    setError('');
    if (!cropPre || !cropPost) {
      setError('Please select both Pre and Post building crop images.');
      return;
    }
    onStartBuilding({ pre_image: cropPre, post_image: cropPost });
  };

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Quick Ready Inputs Header/Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 border border-slate-800 p-6 sm:p-8 shadow-2xl">
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wider uppercase">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Hackathon Demonstration Dataset</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">2026 Nepal Flood & Landslide</h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Pre-configured real-world satellite imagery from the 2026 Nepal disaster event. Automatically loads GeoTIFF rasters and building footprints for instant inference.
            </p>
          </div>

          <button
            onClick={onStartNepalDemo}
            disabled={loading}
            className="shrink-0 px-6 py-3.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-2xl shadow-xl shadow-cyan-600/30 transition-all transform hover:scale-105 flex items-center gap-2.5 disabled:opacity-50"
          >
            <Zap className="w-5 h-5 fill-current text-cyan-200" />
            <span>USE NOW (RUN NEPAL DEMO)</span>
          </button>
        </div>
      </div>

      {/* Input Mode Selector Tabs */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
        
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-6 border-b border-slate-800 mb-6">
          <div>
            <h3 className="text-xl font-bold text-white">Start New Damage Assessment</h3>
            <p className="text-xs text-slate-400">Choose your imagery input pipeline</p>
          </div>

          <div className="flex items-center p-1 bg-slate-950 border border-slate-800 rounded-2xl w-full sm:w-auto">
            <button
              onClick={() => { setActiveTab('satellite'); setError(''); }}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'satellite'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Satellite Imagery Mode</span>
            </button>

            <button
              onClick={() => { setActiveTab('building'); setError(''); }}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'building'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
              <span>Direct Building Crop Mode</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-center gap-3 text-rose-400 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* TAB 1: SATELLITE IMAGERY INPUT MODE */}
        {activeTab === 'satellite' && (
          <form onSubmit={handleSatelliteSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Pre TIFF */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Pre-Disaster Satellite TIFF
                </label>
                <div className="relative border-2 border-dashed border-slate-800 hover:border-cyan-500/50 bg-slate-950/60 rounded-2xl p-4 text-center transition-colors">
                  <Upload className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                  <input
                    type="file"
                    accept=".tif,.tiff"
                    onChange={(e) => setSatPre(e.target.files[0])}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <span className="block text-xs font-semibold text-slate-200 truncate">
                    {satPre ? satPre.name : 'Choose .tif / .tiff'}
                  </span>
                  <span className="block text-[10px] text-slate-500 mt-1">Georeferenced GeoTIFF</span>
                </div>
              </div>

              {/* Post TIFF */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Post-Disaster Satellite TIFF
                </label>
                <div className="relative border-2 border-dashed border-slate-800 hover:border-cyan-500/50 bg-slate-950/60 rounded-2xl p-4 text-center transition-colors">
                  <Upload className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                  <input
                    type="file"
                    accept=".tif,.tiff"
                    onChange={(e) => setSatPost(e.target.files[0])}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <span className="block text-xs font-semibold text-slate-200 truncate">
                    {satPost ? satPost.name : 'Choose .tif / .tiff'}
                  </span>
                  <span className="block text-[10px] text-slate-500 mt-1">Georeferenced GeoTIFF</span>
                </div>
              </div>

              {/* Footprints GeoJSON */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Building Footprints GeoJSON
                </label>
                <div className="relative border-2 border-dashed border-slate-800 hover:border-cyan-500/50 bg-slate-950/60 rounded-2xl p-4 text-center transition-colors">
                  <FileUp className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                  <input
                    type="file"
                    accept=".geojson,.json"
                    onChange={(e) => setSatGeojson(e.target.files[0])}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <span className="block text-xs font-semibold text-slate-200 truncate">
                    {satGeojson ? satGeojson.name : 'Choose .geojson'}
                  </span>
                  <span className="block text-[10px] text-slate-500 mt-1">Vector Polygons</span>
                </div>
              </div>

            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="px-8 py-3.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl shadow-lg shadow-cyan-600/20 transition-all flex items-center gap-2 disabled:opacity-50"
              >
                <Layers className="w-4 h-4" />
                <span>Run Satellite Assessment</span>
              </button>
            </div>
          </form>
        )}

        {/* TAB 2: DIRECT BUILDING CROP MODE */}
        {activeTab === 'building' && (
          <form onSubmit={handleBuildingSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Pre Building Crop */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Pre-Disaster Building Image
                </label>
                <div className="relative border-2 border-dashed border-slate-800 hover:border-cyan-500/50 bg-slate-950/60 rounded-2xl p-6 text-center transition-colors">
                  <ImageIcon className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setCropPre(e.target.files[0])}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <span className="block text-sm font-semibold text-slate-200 truncate">
                    {cropPre ? cropPre.name : 'Select Pre Building Crop'}
                  </span>
                  <span className="block text-xs text-slate-500 mt-1">PNG, JPG, JPEG (Auto-resized to 128x128)</span>
                </div>
              </div>

              {/* Post Building Crop */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Post-Disaster Building Image
                </label>
                <div className="relative border-2 border-dashed border-slate-800 hover:border-cyan-500/50 bg-slate-950/60 rounded-2xl p-6 text-center transition-colors">
                  <ImageIcon className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setCropPost(e.target.files[0])}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <span className="block text-sm font-semibold text-slate-200 truncate">
                    {cropPost ? cropPost.name : 'Select Post Building Crop'}
                  </span>
                  <span className="block text-xs text-slate-500 mt-1">PNG, JPG, JPEG (Auto-resized to 128x128)</span>
                </div>
              </div>

            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="px-8 py-3.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-xl shadow-lg shadow-cyan-600/20 transition-all flex items-center gap-2 disabled:opacity-50"
              >
                <ImageIcon className="w-4 h-4" />
                <span>Run Building Assessment</span>
              </button>
            </div>
          </form>
        )}

      </div>

    </div>
  );
}
