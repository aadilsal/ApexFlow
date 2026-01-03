import React from 'react';
import PredictionForm from './PredictionForm';
import PredictionChart from './PredictionChart';
import type { PredictionRequest, PredictionResponse } from '../../services/inference';
import { inferenceService } from '../../services/inference';
import { Timer, Zap, ShieldCheck, Activity } from 'lucide-react';
import { supabase } from '../../lib/supabase';

export default function Dashboard() {
  const [isLoading, setIsLoading] = React.useState(false);
  const [latestResult, setLatestResult] = React.useState<PredictionResponse | null>(null);
  const [chartData, setChartData] = React.useState<any[]>([]);
  const [summary, setSummary] = React.useState<any>(null);

  React.useEffect(() => {
    async function fetchSummary() {
      const { data } = await supabase
        .from('system_summary')
        .select('*')
        .single();
      if (data) setSummary(data);
    }
    fetchSummary();
  }, [latestResult]); // Re-fetch when a new prediction happens

  const handlePredict = async (data: PredictionRequest) => {
    setIsLoading(true);
    try {
      const result = await inferenceService.predict(data);
      setLatestResult(result);
      
      // Save prediction to Supabase
      const { error: supabaseError } = await supabase
        .from('predictions')
        .insert([{
          input_data: data,
          predicted_time: result.predicted_lap_time,
          confidence_upper: result.confidence_interval.upper_bound,
          confidence_lower: result.confidence_interval.lower_bound,
          inference_time: result.inference_time_ms,
        }]);

      if (supabaseError) {
        console.error('Failed to save prediction to Supabase:', supabaseError);
      }

      // Simulate a sequence for the chart based on the single prediction
      const sequence = Array.from({ length: 10 }, (_, i) => ({
        lap: i + 1,
        time: result.predicted_lap_time + (Math.random() * 0.4 - 0.2),
        upper: result.confidence_interval.upper_bound + (Math.random() * 0.1),
        lower: result.confidence_interval.lower_bound - (Math.random() * 0.1),
      }));
      setChartData(sequence);
    } catch (error) {
      console.error("Prediction failed", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div className="flex flex-col">
          <h1 className="text-3xl font-bold tracking-tight text-white uppercase italic">Session Control</h1>
          <p className="text-gray-400">Live race telemetry and lap-time prediction engine.</p>
        </div>
        <div className="flex gap-2">
          <span className={`px-3 py-1 rounded-full border text-xs font-bold uppercase tracking-widest flex items-center gap-2 ${summary?.status === 'Healthy' ? 'bg-green-500/10 border-green-500/20 text-green-500' : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-500'}`}>
            <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${summary?.status === 'Healthy' ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
            {summary?.status || 'System Checking'}
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Avg. Lap Time" 
          value={latestResult ? `${latestResult.predicted_lap_time.toFixed(3)}s` : '--'} 
          icon={<Timer className="text-primary" />} 
          trend={summary?.avg_lap_delta}
        />
        <StatCard 
          title="Model Confidence" 
          value={latestResult ? "High" : '--'} 
          icon={<ShieldCheck className="text-primary" />} 
          trend={summary?.confidence_score}
        />
        <StatCard 
          title="Inference Latency" 
          value={latestResult ? `${latestResult.inference_time_ms.toFixed(1)}ms` : '--'} 
          icon={<Zap className="text-primary" />} 
        />
        <StatCard 
          title="Active Session" 
          value={summary?.active_session || '--'} 
          icon={<Activity className="text-primary" />} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 h-[500px]">
          {chartData.length > 0 ? (
            <PredictionChart data={chartData} />
          ) : (
            <div className="h-full w-full bg-white/5 border border-white/10 rounded-2xl flex flex-col items-center justify-center text-gray-500 space-y-4">
              <div className="p-4 rounded-full bg-white/5 border border-white/10">
                <Activity size={32} />
              </div>
              <p className="italic font-medium">Capture simulation inputs to generate visualization...</p>
            </div>
          )}
        </div>
        
        <div className="lg:col-span-4">
          <PredictionForm onSubmit={handlePredict} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, trend }: { title: string, value: string, icon: React.ReactNode, trend?: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-primary/30 transition-all group backdrop-blur-sm">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 rounded-lg bg-white/5 border border-white/10 group-hover:bg-primary/10 group-hover:border-primary/20 transition-all">
          {icon}
        </div>
        {trend && (
          <span className="text-[10px] font-bold text-gray-500 bg-white/5 px-2 py-0.5 rounded border border-white/10">
            {trend}
          </span>
        )}
      </div>
      <p className="text-xs uppercase font-bold text-gray-500 tracking-wider mb-1">{title}</p>
      <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
    </div>
  );
}
