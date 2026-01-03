import { Bell, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
export default function Navbar() {

  const { user } = useAuth();

  return (
    <header className="h-16 border-b border-white/10 bg-background/50 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between px-8 ml-64">
      {/* Spacer to push content to the right since search bar is gone */}
      <div className="flex-1" />

      <div className="flex items-center gap-6">
        {/* <button className="relative text-gray-400 hover:text-white transition-colors">
          <Bell size={20} />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full border border-background"></span>
        </button> */}
        
        <div className="flex items-center gap-3 pl-6 border-l border-white/10">
          <div className="text-right">
            <p className="text-sm font-medium text-white uppercase italic">
              {user ? (user.full_name || user.email.split('@')[0]) : 'Guest'}
            </p>
            <p className="text-xs text-gray-500 uppercase">
              {user ? 'Team Member' : 'Observer Access'}
            </p>
          </div>
          <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden">
            <UserIcon size={20} className="text-gray-400" />
          </div>
        </div>
      </div>
    </header>
  );
}
