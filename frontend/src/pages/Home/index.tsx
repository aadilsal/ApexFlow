import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Gauge, Zap, Database, Activity, ChevronRight, Globe, Shield, Cpu } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative flex flex-col items-center overflow-hidden bg-background text-white selection:bg-primary/30">
      {/* Background Image with Overlay */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-40 grayscale-[50%]"
        style={{ backgroundImage: 'url("https://wallpapercave.com/wp/wp9768653.jpg")' }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background/80 to-background" />
      
      {/* Hero Section */}
      <main className="relative z-10 w-full max-w-7xl px-8 flex flex-col items-center pt-32 pb-24 text-center">
        <div className="animate-in fade-in slide-in-from-top-10 duration-1000">
          <div className="inline-flex w-20 h-20 bg-primary rounded-2xl items-center justify-center font-black text-4xl text-white italic shadow-2xl shadow-primary/20 rotate-3 mb-8">AF</div>
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter uppercase italic leading-[0.9] mb-6 drop-shadow-2xl">
            Precision <br />
            <span className="text-primary">ApexFlow</span>
          </h1>
          <p className="max-w-2xl mx-auto text-xl text-gray-400 font-medium mb-12">
            The world's most advanced F1 lap-time prediction engine. 
            Harnessing XGBoost and real-time telemetry to predict the future of the race.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button 
              onClick={() => navigate('/portal/dashboard')}
              className="group relative px-8 py-4 bg-primary text-white font-bold rounded-xl transition-all uppercase italic tracking-tighter flex items-center gap-2 overflow-hidden shadow-2xl shadow-primary/30 active:scale-95"
            >
              <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
              <span className="relative z-10 flex items-center gap-2">
                Initialize Command Center <ChevronRight size={18} />
              </span>
            </button>
            <a 
              href="#features"
              className="px-8 py-4 bg-white/5 border border-white/10 text-white font-bold rounded-xl hover:bg-white/10 transition-all uppercase italic tracking-tighter"
            >
              Explore Capabilities
            </a>
          </div>
        </div>
      </main>

      {/* Feature Grid */}
      <section id="features" className="relative z-10 w-full max-w-7xl px-8 py-24 border-t border-white/5 bg-background/50 backdrop-blur-sm">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          <FeatureCard 
            icon={<Cpu className="text-primary" size={32} />}
            title="XGBoost Core"
            description="Highly optimized gradient boosted trees trained on 20+ seasons of historical F1 telemetry data."
          />
          <FeatureCard 
            icon={<Activity className="text-primary" size={32} />}
            title="Real-time Drift"
            description="Continuous monitoring of model performance against live track conditions to ensure millisecond accuracy."
          />
          <FeatureCard 
            icon={<Database className="text-primary" size={32} />}
            title="Deep Telemetry"
            description="Ingests speed trap data, sector times, and tire life variables direct from FIA technical feeds."
          />
        </div>
      </section>

      {/* Tech Specs */}
      <section className="relative z-10 w-full max-w-7xl px-8 py-24 flex flex-col md:flex-row items-center gap-16">
        <div className="flex-1 space-y-6 text-left">
          <span className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest">
            Technical Specification 4.2
          </span>
          <h2 className="text-4xl font-extrabold tracking-tight uppercase italic">Built for the <span className="text-primary">Limit</span></h2>
          <p className="text-gray-400 text-lg leading-relaxed">
            ApexFlow isn't just a dashboard; it's a mission-critical tool for data analysts. 
            From monitoring drift in high-speed sectors to analyzing historical pace at Monaco, 
            every feature is designed for speed and clarity.
          </p>
          <ul className="space-y-4">
            <li className="flex items-center gap-3 text-sm font-medium text-gray-300">
              <Shield size={16} className="text-primary" /> End-to-end encrypted telemetry feeds
            </li>
            <li className="flex items-center gap-3 text-sm font-medium text-gray-300">
              <Globe size={16} className="text-primary" /> Instant access to global GP metadata
            </li>
            <li className="flex items-center gap-3 text-sm font-medium text-gray-300">
              <Zap size={16} className="text-primary" /> Sub-10ms inference latency
            </li>
          </ul>
        </div>
        <div className="flex-1 w-full max-w-md aspect-video bg-white/5 border border-white/10 rounded-3xl flex items-center justify-center p-8 group relative overflow-hidden">
          <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <Gauge size={80} className="text-primary/40 group-hover:text-primary transition-colors duration-500 animate-pulse" />
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-7xl px-8 py-12 text-center border-t border-white/5">
        <p className="text-[10px] text-gray-600 uppercase font-medium tracking-[0.2em]">
          ApexFlow Predictor
        </p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="space-y-4 group">
      <div className="w-16 h-16 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center group-hover:bg-primary/10 group-hover:border-primary/20 transition-all duration-500">
        {icon}
      </div>
      <h3 className="text-xl font-bold uppercase italic tracking-tight text-white">{title}</h3>
      <p className="text-gray-500 leading-relaxed text-sm">{description}</p>
    </div>
  );
}
