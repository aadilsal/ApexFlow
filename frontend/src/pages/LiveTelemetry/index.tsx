import { useEffect, useState } from 'react';
import { Activity, Calendar, Flag, Trophy, Wind, Thermometer } from 'lucide-react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface SessionData {
  session_key: number;
  meeting_name: string;
  session_name: string;
  date_start: string;
  country_name: string;
  circuit_short_name: string;
  year: number;
  is_live: boolean;
}

interface Driver {
  driver_number: number;
  full_name: string;
  team_name: string;
  name_acronym: string;
  headshot_url: string;
}

interface Lap {
  driver_number: number;
  lap_duration: number;
  lap_number: number;
}

interface Weather {
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  wind_speed: number;
  date: string;
}

export default function LiveTelemetry() {
  const [session, setSession] = useState<SessionData | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [, setLaps] = useState<Lap[]>([]);
  const [weather, setWeather] = useState<Weather | null>(null);
  const [loading, setLoading] = useState(true);

  // Derived Stats
  const [fastestLap, setFastestLap] = useState<{time: number, driver: string} | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    fetchLatestSession();
  }, []);

  const fetchLatestSession = async () => {
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    try {
      const res = await fetch(`${API_BASE_URL}/live/latest`);
      if (!res.ok) throw new Error("Failed to fetch session");
      const data = await res.json();
      setSession(data);
      
      if (data.session_key) {
        // Fetch drivers
        const driversRes = await fetch(`${API_BASE_URL}/live/${data.session_key}/drivers`);
        const driversData = await driversRes.json();
        setDrivers(driversData);
        
        // Fetch laps
        const lapsRes = await fetch(`${API_BASE_URL}/live/${data.session_key}/laps`);
        const lapsData: Lap[] = await lapsRes.json();
        setLaps(lapsData);

        // Fetch Weather
        const weatherRes = await fetch(`${API_BASE_URL}/live/${data.session_key}/weather`);
        if (weatherRes.ok) {
           const weatherData = await weatherRes.json();
           // Get latest weather point
           if (weatherData && weatherData.length > 0) {
             setWeather(weatherData[weatherData.length - 1]);
           }
        }
        
        processStats(lapsData, driversData);
      }
    } catch (error) {
      console.error("Failed to fetch live data:", error);
    } finally {
      setLoading(false);
    }
  };

  const processStats = (lapsData: Lap[], driversData: Driver[]) => {
      // 1. Fastest Lap
      let minTime = Infinity;
      let fastestDriverNum = 0;

      lapsData.forEach(lap => {
          if (lap.lap_duration && lap.lap_duration < minTime) {
              minTime = lap.lap_duration;
              fastestDriverNum = lap.driver_number;
          }
      });

      if (minTime !== Infinity) {
          const driver = driversData.find(d => d.driver_number === fastestDriverNum);
          setFastestLap({
              time: minTime,
              driver: driver ? `${driver.name_acronym} (${getShortTeamName(driver.team_name)})` : `#${fastestDriverNum}`
          });
      }

      // 2. Chart Data: Pace Evolution for Top 3 Drivers
      // We'll group laps by lap number
      // Taking top 3 distinct drivers from the laps array (just as an example, ideally leaderboard order)
      const topDrivers = [...new Set(lapsData.map(l => l.driver_number))].slice(0, 3);
      
      const lapsByNumber: Record<string, any> = {};
      
      lapsData.forEach(lap => {
          if (!topDrivers.includes(lap.driver_number)) return;
          if (!lapsByNumber[lap.lap_number]) {
              lapsByNumber[lap.lap_number] = { name: `Lap ${lap.lap_number}` };
          }
          const dName = driversData.find(d => d.driver_number === lap.driver_number)?.name_acronym || lap.driver_number;
          lapsByNumber[lap.lap_number][dName] = lap.lap_duration;
      });

      setChartData(Object.values(lapsByNumber).sort((a: any, b: any) => 
        parseInt(a.name.split(' ')[1]) - parseInt(b.name.split(' ')[1])
      ));
  };

  const getShortTeamName = (name: string) => {
      if (name.includes('Red Bull')) return 'RBR';
      if (name.includes('Ferrari')) return 'FER';
      if (name.includes('Mercedes')) return 'MER';
      if (name.includes('McLaren')) return 'MCL';
      if (name.includes('Aston')) return 'AMR';
      return name.substring(0, 3).toUpperCase();
  };

  const formatTime = (seconds: number) => {
      const mins = Math.floor(seconds / 60);
      const secs = (seconds % 60).toFixed(3);
      return `${mins}:${secs.padStart(6, '0')}`;
  };

  const getTeamColor = (num: number) => {
     const d = drivers.find(d => d.driver_number === num);
     if (!d) return 'bg-gray-500';
     if (d.team_name.toLowerCase().includes('red bull')) return 'bg-[#0600EF]'; // RBR Blue
     if (d.team_name.toLowerCase().includes('ferrari')) return 'bg-[#FF0000]'; // Ferrari Red
     if (d.team_name.toLowerCase().includes('mercedes')) return 'bg-[#00D2BE]'; // Mercedes Teal
     if (d.team_name.toLowerCase().includes('mclaren')) return 'bg-[#FF8700]'; // McLaren Orange
     if (d.team_name.toLowerCase().includes('aston')) return 'bg-[#006F62]'; // AM Green
     if (d.team_name.toLowerCase().includes('alpine')) return 'bg-[#0090FF]'; // Alpine Blue
     if (d.team_name.toLowerCase().includes('williams')) return 'bg-[#005AFF]'; // Williams Blue
     return 'bg-gray-400';
  }
  
  const getTeamColorHex = (acronym: string) => {
      // Helper for chart lines
       if (['VER', 'PER'].includes(acronym)) return '#0600EF';
       if (['LEC', 'SAI'].includes(acronym)) return '#FF0000';
       if (['HAM', 'RUS'].includes(acronym)) return '#00D2BE';
       if (['NOR', 'PIA'].includes(acronym)) return '#FF8700';
       return '#888888';
  }

  if (loading) return <div className="min-h-screen pt-20 flex justify-center items-center text-white">Loading live telemetry...</div>;
  if (!session) return <div className="min-h-screen pt-20 flex justify-center items-center text-white">No active session found.</div>;

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-3 mb-2">
            {session.is_live ? (
              <span className="px-3 py-1 text-xs font-bold text-white bg-red-600 rounded-full animate-pulse flex items-center gap-2">
                <span className="w-2 h-2 bg-white rounded-full"></span> LIVE
              </span>
            ) : (
               <span className="px-3 py-1 text-xs font-bold text-gray-300 bg-gray-700 rounded-full flex items-center gap-2">
                <Calendar size={12} /> REPLAY • {new Date(session.date_start).toLocaleDateString()}
              </span>
            )}
            <span className="text-gray-400 text-sm uppercase tracking-wider">{session.session_name}</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-1">{session.meeting_name}</h1>
          <p className="text-gray-400 flex items-center gap-2">
            <Flag size={16} /> {session.circuit_short_name}, {session.country_name}
          </p>
        </div>
        
        <div className="flex items-center gap-6">
           {weather && (
             <>
                <div className="text-right hidden md:block">
                    <p className="text-xs text-gray-500 uppercase flex items-center justify-end gap-1"><Thermometer size={12}/> Track Temp</p>
                    <p className="text-xl font-mono text-white">{weather.track_temperature.toFixed(1)}°C</p>
                </div>
                <div className="text-right hidden md:block pl-4 border-l border-white/10">
                    <p className="text-xs text-gray-500 uppercase flex items-center justify-end gap-1"><Wind size={12}/> Wind</p>
                    <p className="text-xl font-mono text-white">{weather.wind_speed.toFixed(1)} m/s</p>
                </div>
             </>
           )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: Leaderboard */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Trophy className="text-yellow-400" size={20} /> Field
          </h2>
          <div className="bg-black/40 rounded-xl border border-white/10 overflow-hidden">
             <div className="max-h-[600px] overflow-y-auto">
                {drivers.map((driver, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    key={driver.driver_number} 
                    className="flex items-center p-3 border-b border-white/5 hover:bg-white/5 transition-colors group"
                  >
                    <span className="w-8 text-center font-mono text-gray-400 group-hover:text-white">{driver.driver_number}</span>
                    <div className={`w-1 h-8 mx-3 rounded-full ${getTeamColor(driver.driver_number)}`}></div>
                    <div className="flex-1">
                      <p className="font-bold text-white">{driver.name_acronym}</p>
                      <p className="text-xs text-gray-500 truncate max-w-[120px]">{driver.team_name}</p>
                    </div>
                  </motion.div>
                ))}
             </div>
          </div>
        </div>

        {/* Right Col: Telemetry & Stats */}
        <div className="lg:col-span-2 space-y-6">
           
           {/* Telemetry Chart */}
           <div className="bg-white/5 rounded-2xl border border-white/10 p-6 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Activity className="text-primary" size={20} /> Pace Evolution (Top 3)
              </h3>
              <div className="h-[300px] w-full">
                 <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="name" stroke="#666" fontSize={12} tickMargin={10} />
                        <YAxis stroke="#666" fontSize={12} domain={['auto', 'auto']} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }}
                            itemStyle={{ color: '#fff' }}
                        />
                        <Legend />
                        {chartData.length > 0 && Object.keys(chartData[0]).filter(k => k !== 'name').map((key) => (
                            <Line 
                                key={key}
                                type="monotone" 
                                dataKey={key} 
                                stroke={getTeamColorHex(key)} 
                                strokeWidth={2}
                                dot={false}
                            />
                        ))}
                    </LineChart>
                 </ResponsiveContainer>
              </div>
              <p className="text-center text-gray-500 text-sm mt-4">Lap times (seconds) over session duration</p>
           </div>

           {/* Stats Grid */}
           <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                 <p className="text-gray-400 text-xs uppercase">Fastest Lap</p>
                 {fastestLap ? (
                     <>
                        <p className="text-2xl font-bold text-white mt-1">{formatTime(fastestLap.time)}</p>
                        <p className="text-xs text-primary mt-1">{fastestLap.driver}</p>
                     </>
                 ) : (
                    <p className="text-xl font-bold text-white mt-1">--:--.---</p>
                 )}
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                 <p className="text-gray-400 text-xs uppercase">Humidity</p>
                 {weather ? (
                     <>
                        <p className="text-2xl font-bold text-blue-400 mt-1">{weather.humidity}%</p>
                        <p className="text-xs text-gray-500 mt-1">
                            {weather.humidity > 60 ? 'High Chance of Rain' : 'Dry Conditions'}
                        </p>
                     </>
                 ) : (
                    <p className="text-xl font-bold text-white mt-1">--%</p>
                 )}
              </div>
           </div>

        </div>

      </div>
    </div>
  );
}
