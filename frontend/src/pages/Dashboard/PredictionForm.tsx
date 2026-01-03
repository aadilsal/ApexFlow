import React from 'react';
import type { PredictionRequest } from '../../services/inference';
import { Flame, Droplets, User, MapPin, Gauge } from 'lucide-react';

interface PredictionFormProps {
  onSubmit: (data: PredictionRequest) => void;
  isLoading: boolean;
}

const circuits = ["Bahrain", "Saudi Arabia", "Australia", "Azerbaijan", "Miami", "Monaco", "Spain", "Canada", "Austria", "UK", "Hungary", "Belgium", "Netherlands", "Italy", "Singapore", "Japan", "Qatar", "USA", "Mexico", "Brazil", "Las Vegas", "Abu Dhabi"];
const drivers = ["VER", "PER", "LEC", "SAI", "HAM", "RUS", "NOR", "PIA", "ALO", "STR", "GAS", "OCO", "ALB", "SAR", "TSU", "RIC", "MAG", "HUL", "BOT", "ZHO"];
const compounds = ["SOFT", "MEDIUM", "HARD", "INTER", "WET"];
const sessions = ["FP1", "FP2", "FP3", "QUALIFYING", "RACE"];

export default function PredictionForm({ onSubmit, isLoading }: PredictionFormProps) {
  const [formData, setFormData] = React.useState<PredictionRequest>({
    driver_id: "VER",
    circuit_id: "Bahrain",
    fuel_load: 10,
    track_temp: 35,
    tire_compound: "SOFT",
    session_type: "QUALIFYING"
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-6">
        <Gauge className="text-primary" size={20} />
        <h2 className="text-xl font-bold uppercase italic tracking-wider">Simulation Inputs</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs uppercase text-gray-500 font-bold flex items-center gap-2">
              <User size={12} /> Driver
            </label>
            <select 
              value={formData.driver_id}
              onChange={(e) => setFormData({...formData, driver_id: e.target.value})}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-primary/50 transition-colors"
            >
              {drivers.map(d => <option key={d} value={d} className="bg-[#1a1a1a]">{d}</option>)}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase text-gray-500 font-bold flex items-center gap-2">
              <MapPin size={12} /> Circuit
            </label>
            <select 
              value={formData.circuit_id}
              onChange={(e) => setFormData({...formData, circuit_id: e.target.value})}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-primary/50 transition-colors"
            >
              {circuits.map(c => <option key={c} value={c} className="bg-[#1a1a1a]">{c}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs uppercase text-gray-500 font-bold flex items-center gap-2">
              <Flame size={12} /> Track Temp (°C)
            </label>
            <input 
              type="number" 
              value={formData.track_temp}
              onChange={(e) => setFormData({...formData, track_temp: Number(e.target.value)})}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase text-gray-500 font-bold flex items-center gap-2">
              <Droplets size={12} /> Fuel Load (kg)
            </label>
            <input 
              type="number" 
              value={formData.fuel_load}
              onChange={(e) => setFormData({...formData, fuel_load: Number(e.target.value)})}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-primary/50 transition-colors"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs uppercase text-gray-500 font-bold">Compound</label>
            <select 
              value={formData.tire_compound}
              onChange={(e) => setFormData({...formData, tire_compound: e.target.value})}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-primary/50 transition-colors"
            >
              {compounds.map(c => <option key={c} value={c} className="bg-[#1a1a1a]">{c}</option>)}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase text-gray-500 font-bold">Session</label>
            <select 
              value={formData.session_type}
              onChange={(e) => setFormData({...formData, session_type: e.target.value})}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-primary/50 transition-colors"
            >
              {sessions.map(s => <option key={s} value={s} className="bg-[#1a1a1a]">{s}</option>)}
            </select>
          </div>
        </div>

        <button 
          type="submit" 
          disabled={isLoading}
          className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg shadow-lg shadow-primary/20 transition-all uppercase italic flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          ) : 'Run Prediction'}
        </button>
      </form>
    </div>
  );
}
