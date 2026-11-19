import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertTriangle,
  ShieldCheck,
  BookOpen,
  Users,
  Activity,
  CheckSquare,
  Lock,
  Radio,
  UserCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { path: '/', label: 'Overview & Map', icon: LayoutDashboard },
  { path: '/incidents', label: 'Incidents Directory', icon: AlertTriangle },
  { path: '/secureai', label: 'SecureAI Protection', icon: ShieldCheck, badge: 'Pillar 1' },
  { path: '/knowledge', label: 'Knowledge Grid', icon: BookOpen, badge: 'Pillar 2' },
  { path: '/workforce', label: 'WorkforceOS', icon: Users, badge: 'Pillar 3' },
  { path: '/agentops', label: 'AgentOps Tracing', icon: Activity, badge: 'Pillar 4' },
  { path: '/approvals', label: 'Human+AI Approvals', icon: CheckSquare, badge: 'Pillar 5' },
  { path: '/audit', label: 'Tamper-Evident Audit', icon: Lock },
];

export const Sidebar: React.FC = () => {
  const { user, switchUser } = useAuth();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-900/30">
            IS
          </div>
          <div>
            <div className="font-bold text-slate-100 text-sm tracking-wide">InfraSphere AI</div>
            <div className="text-xs text-emerald-400 font-medium flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>InfraOps BD</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-600/15 text-emerald-400 border border-emerald-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Role Switcher Demo Control */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
          <span>Demo Role Switcher</span>
          <UserCheck className="w-3.5 h-3.5 text-slate-500" />
        </div>
        <div className="grid grid-cols-3 gap-1">
          <button
            onClick={() => switchUser('manager')}
            className={`text-xs py-1 px-1.5 rounded text-center transition-colors font-medium ${
              user?.role === 'manager'
                ? 'bg-emerald-600 text-white font-semibold'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Manager
          </button>
          <button
            onClick={() => switchUser('analyst')}
            className={`text-xs py-1 px-1.5 rounded text-center transition-colors font-medium ${
              user?.role === 'analyst'
                ? 'bg-blue-600 text-white font-semibold'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Analyst
          </button>
          <button
            onClick={() => switchUser('admin')}
            className={`text-xs py-1 px-1.5 rounded text-center transition-colors font-medium ${
              user?.role === 'admin'
                ? 'bg-purple-600 text-white font-semibold'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Admin
          </button>
        </div>
      </div>
    </aside>
  );
};
