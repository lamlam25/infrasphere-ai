import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Shield, Database, Radio } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();

  const roleColors: Record<string, string> = {
    manager: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    analyst: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    admin: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  };

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full text-xs text-amber-300">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
          <span className="font-medium">Synthetic Telemetry Active</span>
          <span className="text-amber-400/60 font-mono">(FFWC / OSM Demo Sandbox)</span>
        </div>
        <div className="hidden md:flex items-center space-x-2 text-xs text-slate-400 border-l border-slate-800 pl-4">
          <Radio className="w-3.5 h-3.5 text-emerald-400" />
          <span>Sunamganj STN-SUN-01: <strong className="text-red-400">7.35m</strong> (Danger: 6.50m)</span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {user && (
          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-slate-200">{user.full_name}</div>
              <div className="text-[11px] text-slate-400">{user.email}</div>
            </div>
            <span
              className={`px-2.5 py-1 text-xs uppercase font-semibold rounded-md border ${
                roleColors[user.role] || 'bg-slate-800 text-slate-300 border-slate-700'
              }`}
            >
              {user.role}
            </span>
          </div>
        )}

        <button
          onClick={logout}
          title="Sign Out"
          className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
