import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

export default function Layout() {
  return (
    <div className="min-h-screen bg-background text-white selection:bg-primary/30 selection:text-white">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <Navbar />
        <main className="ml-64 p-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
