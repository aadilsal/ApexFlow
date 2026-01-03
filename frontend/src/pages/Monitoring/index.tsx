import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, LineChart, Line } from 'recharts';
import { Activity, AlertTriangle, Cpu, Globe } from 'lucide-react';
import { supabase } from '../../lib/supabase';

interface HealthPoint {
  name: string;
  latency: number;
  error: number;
}

interface DriftPoint {
  feature: string;
  score: number;
}

export default function Monitoring() {
  const [healthData, setHealthData] = useState<HealthPoint[]>([]);
  const [driftData, setDriftData] = useState<DriftPoint[]>([]);
  const [stats, setStats] = useState({
    status: 'Unknown',
    drift: 'Unknown',
    cpu: '--',
    throughput: '--'
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMetrics() {
      // In a real app, these might be separate tables or one metrics table
      const { data: health, error: hError } = await supabase
        .from('system_health')
        .select('*')
        .order('name', { ascending: true });

      const { data: drift, error: dError } = await supabase
        .from('drift_metrics')
        .select('*');

      if (!hError && health) setHealthData(health);
      if (!dError && drift) setDriftData(drift);

      // Fetch latest summary stats
      const { data: summary } = await supabase
        .from('system_summary')
        .select('*')
        .single();
      
      if (summary) {
        setStats({
          status: summary.status,
          drift: summary.drift_level,
          cpu: summary.cpu_usage,
          throughput: summary.throughput
        });
      }

      setLoading(false);
    }
    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col">
        <h1 className="text-3xl font-bold tracking-tight text-white uppercase italic">System Health</h1>
        <p className="text-gray-400">Real-time model performance, drift detection, and API health.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <HealthWidget 
          title="API Status" 
          value={stats.status} 
          icon={<Globe className={stats.status === 'Healthy' ? "text-green-500" : "text-gray-500"} />} 
          color={stats.status === 'Healthy' ? "text-green-500" : "text-gray-500"} 
        />
        <HealthWidget 
          title="Model Drift" 
          value={stats.drift} 
          icon={<AlertTriangle className={stats.drift === 'Low' ? "text-green-500" : "text-yellow-500"} />} 
          color={stats.drift === 'Low' ? "text-green-500" : "text-yellow-500"} 
        />
        <HealthWidget title="CPU Usage" value={stats.cpu} icon={<Cpu className="text-primary" />} />
        <HealthWidget title="Throughput" value={stats.throughput} icon={<Activity className="text-primary" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
          <h2 className="text-lg font-bold uppercase italic mb-6">API Latency (ms)</h2>
          <div className="h-64">
            {healthData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={healthData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis dataKey="name" stroke="#ffffff40" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#ffffff40" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#1a1a1b', border: 'none' }} />
                  <Line type="monotone" dataKey="latency" stroke="#E10600" strokeWidth={3} dot={{ r: 4, fill: '#E10600' }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500 italic">No latency metrics available.</div>
            )}
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
          <h2 className="text-lg font-bold uppercase italic mb-6">Feature Drift Scores</h2>
          <div className="h-64">
            {driftData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={driftData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis dataKey="feature" stroke="#ffffff40" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#ffffff40" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#1a1a1b', border: 'none' }} />
                  <Bar dataKey="score">
                    {driftData.map((entry, index) => (
                      <Cell key={index} fill={entry.score > 0.4 ? '#E10600' : '#ffffff20'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500 italic">No drift metrics available.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function HealthWidget({ title, value, icon, color }: { title: string, value: string, icon: React.ReactNode, color?: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-4 hover:border-white/20 transition-all">
      <div className="p-3 rounded-lg bg-white/5 border border-white/10">
        {icon}
      </div>
      <div>
        <p className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">{title}</p>
        <p className={`text-xl font-bold tracking-tight ${color || 'text-white'}`}>{value}</p>
      </div>
    </div>
  );
}
