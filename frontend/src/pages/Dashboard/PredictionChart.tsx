import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

interface PredictionPoint {
  lap: number;
  time: number;
  upper: number;
  lower: number;
}

interface PredictionChartProps {
  data: PredictionPoint[];
}

export default function PredictionChart({ data }: PredictionChartProps) {
  return (
    <div className="h-full w-full bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold uppercase italic tracking-wider">Prediction Timeline</h2>
        <div className="flex gap-4 text-xs uppercase font-bold tracking-tighter">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-primary/40 rounded-full"></div>
            <span className="text-gray-400">CI 95%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-primary rounded-full"></div>
            <span className="text-gray-400">Estimated Lap</span>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="colorTime" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#E10600" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#E10600" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
            <XAxis 
              dataKey="lap" 
              stroke="#ffffff40" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false}
              label={{ value: 'Simulation Lap', position: 'insideBottom', offset: -10, fill: '#ffffff40', fontSize: 10 }}
            />
            <YAxis 
              stroke="#ffffff40" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
              domain={['auto', 'auto']}
              tickFormatter={(val) => `${val}s`}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1a1b', border: '1px solid #ffffff10', borderRadius: '8px', color: '#fff' }}
              itemStyle={{ color: '#E10600' }}
            />
            <Area 
              type="monotone" 
              dataKey="upper" 
              stroke="transparent" 
              fill="#E10600" 
              fillOpacity={0.1} 
              connectNulls 
            />
            <Area 
              type="monotone" 
              dataKey="lower" 
              stroke="transparent" 
              fill="#E10600" 
              fillOpacity={0.1} 
              connectNulls 
            />
            <Area 
              type="monotone" 
              dataKey="time" 
              stroke="#E10600" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorTime)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
