import { useState, useEffect } from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { supabase } from '../../lib/supabase';

interface ModelVersion {
  name: string;
  mae: number;
  rmse: number;
  accuracy: number;
  is_production: boolean;
}

export default function Historical() {
  const [perfData, setPerfData] = useState<ModelVersion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPerformance() {
      const { data, error } = await supabase
        .from('model_versions')
        .select('*')
        .order('accuracy', { ascending: true });

      if (error) {
        console.error('Error fetching model performance:', error);
      } else {
        setPerfData(data || []);
      }
      setLoading(false);
    }
    fetchPerformance();
  }, []);

  const champion = perfData.find(m => m.is_production) || perfData[perfData.length - 1];

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
        <h1 className="text-3xl font-bold tracking-tight text-white uppercase italic">Model Performance</h1>
        <p className="text-gray-400">Comparative analysis across model versions and training cycles.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
          <h2 className="text-lg font-bold uppercase italic mb-6">Error Progression (MAE/RMSE)</h2>
          <div className="h-80">
            {perfData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="mae" name="MAE" unit="s" stroke="#ffffff40" fontSize={12} tickLine={false} />
                  <YAxis dataKey="rmse" name="RMSE" unit="s" stroke="#ffffff40" fontSize={12} tickLine={false} />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1a1a1b', border: 'none' }} />
                  <Legend verticalAlign="top" height={36}/>
                  <Scatter name="Legacy Models" data={perfData.filter(m => !m.is_production)} fill="#ffffff20" shape="circle" />
                  <Scatter name="Production Model" data={perfData.filter(m => m.is_production)} fill="#E10600" shape="star" />
                </ScatterChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500 italic">No performance data available.</div>
            )}
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm flex flex-col justify-center gap-8">
           <div className="space-y-2">
              <p className="text-xs uppercase font-bold text-gray-500 tracking-widest">Champion Model</p>
              <p className="text-4xl font-bold text-white tracking-tighter uppercase italic">{champion?.name || '---'}</p>
           </div>
           
           <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                <p className="text-[10px] uppercase font-bold text-primary/80">Mean Absolute Error</p>
                <p className="text-xl font-bold text-primary italic">{champion?.mae ? `${champion.mae}s` : '--'}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-[10px] uppercase font-bold text-gray-500">RMSE</p>
                <p className="text-xl font-bold text-white italic">{champion?.rmse ? `${champion.rmse}s` : '--'}</p>
              </div>
           </div>

           <div className="pt-4 border-t border-white/10">
              <p className="text-xs text-gray-400 italic">"Accuracy score for the active model: {champion?.accuracy || 0}%"</p>
           </div>
        </div>
      </div>
    </div>
  );
}
