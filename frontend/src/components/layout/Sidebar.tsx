import { useLocation, Link } from 'react-router-dom';
import { LayoutDashboard, Database, Activity, Search, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '../../hooks/useAuth';

export default function Sidebar() {
  const location = useLocation();
  const { user, signOut } = useAuth();

  return (
    <aside className="w-64 h-screen bg-background border-r border-white/10 flex flex-col fixed left-0 top-0">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-primary rounded-sm flex items-center justify-center font-bold text-white shadow-lg shadow-primary/20 rotate-3">AF</div>
        <span className="text-xl font-bold tracking-tighter text-white uppercase italic">ApexFlow</span>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-2">
        <Link to="/portal/dashboard" className={cn("flex items-center gap-3 px-4 py-3 rounded-xl transition-all group", location.pathname === "/portal/dashboard" ? "bg-primary text-white" : "text-gray-400 hover:text-white hover:bg-white/5")}>
          <LayoutDashboard size={20} className="group-hover:text-primary transition-colors" />
          <span className="font-medium">Dashboard</span>
        </Link>
        <Link to="/portal/live" className={cn("flex items-center gap-3 px-4 py-3 rounded-xl transition-all group", location.pathname === "/portal/live" ? "bg-primary text-white" : "text-gray-400 hover:text-white hover:bg-white/5")}>
          <Activity size={20} className="group-hover:text-primary transition-colors" />
          <span className="font-medium">Live Telemetry</span>
        </Link>
        <Link to="/portal/monitoring" className={cn("flex items-center gap-3 px-4 py-3 rounded-xl transition-all group", location.pathname === "/portal/monitoring" ? "bg-primary text-white" : "text-gray-400 hover:text-white hover:bg-white/5")}>
          <Activity size={20} className="group-hover:text-primary transition-colors" />
          <span className="font-medium">System Health</span>
        </Link>
        <Link to="/portal/historical" className={cn("flex items-center gap-3 px-4 py-3 rounded-xl transition-all group", location.pathname === "/portal/historical" ? "bg-primary text-white" : "text-gray-400 hover:text-white hover:bg-white/5")}>
          <Database size={20} className="group-hover:text-primary transition-colors" />
          <span className="font-medium">Historical Data</span>
        </Link>
        <Link to="/portal/explorer" className={cn("flex items-center gap-3 px-4 py-3 rounded-xl transition-all group", location.pathname === "/portal/explorer" ? "bg-primary text-white" : "text-gray-400 hover:text-white hover:bg-white/5")}>
          <Search size={20} className="group-hover:text-primary transition-colors" />
          <span className="font-medium">Data Explorer</span>
        </Link>
      </nav>

      <div className="p-4 border-t border-white/10 space-y-4">
        <div className="px-4 py-2">
          <p className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-1">Authenticated as</p>
          <p className="text-xs text-white truncate font-medium">{user?.email}</p>
        </div>
        <button
          onClick={() => signOut()}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-md text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all duration-300 group"
        >
          <LogOut size={20} className="group-hover:scale-110 transition-transform" />
          <span className="font-medium">Log Out</span>
        </button>
      </div>
    </aside>
  );
}
