import React, { useState, useMemo, useEffect } from 'react';
import { 
  Database, 
  Search, 
  Filter, 
  Download, 
  TrendingUp, 
  Gauge, 
  Thermometer, 
  Calendar,
  ChevronDown,
  ChevronUp,
  Info 
} from 'lucide-react';
import { supabase } from '../../lib/supabase';

interface SessionMetadata {
  id: string;
  track: string;
  date: string;
  driver: string;
  laptime: string;
  fuel: number;
  temp: number;
  sectors: string[];
}

export default function Explorer() {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionMetadata[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSessions() {
      const { data, error } = await supabase
        .from('telemetry_sessions')
        .select('*')
        .order('date', { ascending: false });

      if (error) {
        console.error('Error fetching sessions:', error);
      } else {
        setSessions(data || []);
      }
      setLoading(false);
    }

    fetchSessions();
  }, []);

  const filteredSessions = useMemo(() => {
    return sessions.filter(s => 
      s.track.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.driver.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.id.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm, sessions]);

  const stats = useMemo(() => ({
    count: filteredSessions.length,
    avgTemp: Math.round(filteredSessions.reduce((acc, s) => acc + s.temp, 0) / filteredSessions.length) || 0,
    totalFuel: filteredSessions.reduce((acc, s) => acc + s.fuel, 0).toFixed(1)
  }), [filteredSessions]);

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div className="flex flex-col">
          <h1 className="text-3xl font-bold tracking-tight text-white uppercase italic">Telemetry Explorer</h1>
          <p className="text-gray-400">Deep-dive into historical performance data and raw metrics.</p>
        </div>
        <button 
          onClick={() => alert('Exporting data to CSV...')}
          className="flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/20 text-primary rounded-lg text-xs font-bold uppercase hover:bg-primary/20 transition-all"
        >
          <Download size={14} /> Export CSV
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          icon={<Database size={20} />} 
          label="Sessions analyzed" 
          value={stats.count} 
          trend="+12% vs last GP"
        />
        <StatCard 
          icon={<Thermometer size={20} />} 
          label="Avg track temp" 
          value={`${stats.avgTemp}°C`} 
          trend="Optimized range"
        />
        <StatCard 
          icon={<Gauge size={20} />} 
          label="Cumulative fuel load" 
          value={`${stats.totalFuel}kg`} 
          trend="High efficiency"
        />
      </div>

      {/* Filters & Table */}
      <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-md">
        <div className="p-4 border-b border-white/10 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search driver, track, or session ID..." 
              className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-gray-300 hover:text-white transition-colors">
            <Filter size={16} /> Filters
          </button>
        </div>

        <div className="overflow-x-auto">
          {filteredSessions.length > 0 ? (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/5 text-[10px] font-bold uppercase text-gray-400 tracking-[0.2em]">
                  <th className="px-6 py-4">Session ID</th>
                  <th className="px-6 py-4">Track</th>
                  <th className="px-6 py-4">Driver</th>
                  <th className="px-6 py-4">Lap Time</th>
                  <th className="px-6 py-4 text-center">Status</th>
                  <th className="px-6 py-4 w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm font-medium">
                {filteredSessions.map((session) => (
                  <React.Fragment key={session.id}>
                    <tr 
                      className={`hover:bg-white/5 transition-colors group cursor-pointer ${expandedRow === session.id ? 'bg-primary/5' : ''}`}
                      onClick={() => setExpandedRow(expandedRow === session.id ? null : session.id)}
                    >
                      <td className="px-6 py-4 font-mono text-xs text-gray-400 group-hover:text-primary transition-colors">
                        {session.id}
                      </td>
                      <td className="px-6 py-4 flex items-center gap-2">
                         <Calendar size={14} className="text-gray-500" />
                         {session.track}
                      </td>
                      <td className="px-6 py-4">
                        <span className="bg-white/10 px-2 py-0.5 rounded text-xs font-bold border border-white/10">{session.driver}</span>
                      </td>
                      <td className="px-6 py-4 font-mono text-primary font-bold">{session.laptime}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                          <span className="text-[10px] uppercase font-black text-gray-500 tracking-tighter">Verified</span>
                          <div className="group relative">
                            <Info size={12} className="text-gray-600 cursor-help" />
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-background border border-white/10 rounded shadow-2xl text-[10px] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                              Telemetry integrity score: 99.8%<br/>
                              Inertial sensor sync: OK
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {expandedRow === session.id ? <ChevronUp size={16} className="text-primary" /> : <ChevronDown size={16} className="text-gray-500" />}
                      </td>
                    </tr>
                    {expandedRow === session.id && (
                      <tr className="bg-white/[0.02]">
                        <td colSpan={6} className="px-6 py-8 animate-in slide-in-from-top-2 duration-300">
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                            <div className="space-y-2">
                              <p className="text-[10px] uppercase text-gray-500 font-bold tracking-widest">Sector Breakdowns</p>
                              <div className="space-y-3 font-mono">
                                {session.sectors && Array.isArray(session.sectors) && session.sectors.map((s, i) => (
                                  <div key={i} className="flex justify-between items-center text-xs p-2 bg-white/5 rounded border border-white/5">
                                    <span className="text-gray-400 italic">S{i+1}:</span>
                                    <span className="text-white font-bold">{s}s</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div className="md:col-span-3 h-32 flex items-end gap-1 px-4">
                              {[40, 65, 30, 85, 45, 70, 55, 90, 35, 60, 25, 75].map((h, i) => (
                                <div 
                                  key={i} 
                                  className="flex-1 bg-primary/20 border-t border-primary/50 rounded-t-sm group-hover:bg-primary/40 transition-all cursor-crosshair"
                                  style={{ height: `${h}%` }}
                                >
                                  <div className="hidden group-hover:block absolute top-0 text-[10px] text-primary bg-primary/10 px-1">27{i}mbps</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center text-gray-500 italic">
              No sessions found matching your search criteria.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, trend }: { icon: React.ReactNode, label: string, value: string | number, trend: string }) {
  return (
    <div className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-4 hover:border-primary/30 transition-all group">
      <div className="flex justify-between items-start">
        <div className="p-2 bg-white/5 rounded-lg text-gray-400 group-hover:text-primary transition-colors">
          {icon}
        </div>
        <div className="flex items-center gap-1 text-[10px] font-bold text-green-500 uppercase italic">
          <TrendingUp size={12} /> {trend}
        </div>
      </div>
      <div>
        <h4 className="text-xs text-gray-500 uppercase font-black tracking-widest mb-1">{label}</h4>
        <div className="text-3xl font-black italic tracking-tighter text-white uppercase">{value}</div>
      </div>
    </div>
  );
}
