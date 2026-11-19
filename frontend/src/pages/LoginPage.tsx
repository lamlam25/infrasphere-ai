import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, AlertCircle, ArrowRight, UserCheck } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async (demoEmail: string) => {
    setError(null);
    setIsLoading(true);
    try {
      await login(demoEmail, 'Demo1234!');
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Quick login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      {/* Background aesthetic grid / glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-600 shadow-xl shadow-emerald-900/40 text-white font-extrabold text-2xl mb-4">
            IS
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">InfraSphere AI</h1>
          <p className="text-sm text-emerald-400 font-medium mt-1">InfraOps BD Command Center</p>
          <p className="text-xs text-slate-400 mt-2">
            The Intelligent Operating System for Trusted AI · Multi-Agent Operations
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center space-x-2 text-xs text-red-400">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@infrasphere.bd"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2.5 rounded-lg text-sm transition-all flex items-center justify-center space-x-2 shadow-lg shadow-emerald-900/30 disabled:opacity-50"
            >
              <span>{isLoading ? 'Signing In...' : 'Sign In to Command Center'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Access Buttons */}
          <div className="mt-6 pt-5 border-t border-slate-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
              <span className="font-semibold uppercase tracking-wider">CloudCamp Demo Quick-Access</span>
              <UserCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('manager@infrasphere.bd')}
                className="w-full flex items-center justify-between p-2.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/50 rounded-lg text-left transition-colors"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-200">Operations Manager (Recommended)</div>
                  <div className="text-[11px] text-slate-500 font-mono">manager@infrasphere.bd</div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium border border-emerald-500/20">
                  Approve / Intervene
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('analyst@infrasphere.bd')}
                className="w-full flex items-center justify-between p-2.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/50 rounded-lg text-left transition-colors"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-200">Infrastructure Analyst</div>
                  <div className="text-[11px] text-slate-500 font-mono">analyst@infrasphere.bd</div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-medium border border-blue-500/20">
                  Analyze / Investigate
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('admin@infrasphere.bd')}
                className="w-full flex items-center justify-between p-2.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-purple-500/50 rounded-lg text-left transition-colors"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-200">System Administrator</div>
                  <div className="text-[11px] text-slate-500 font-mono">admin@infrasphere.bd</div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-medium border border-purple-500/20">
                  Policies & Audit
                </span>
              </button>
            </div>
          </div>
        </div>

        <div className="text-center mt-6 text-xs text-slate-500">
          InfraSphere AI · Built for Bangladesh National Infrastructure Resilience
        </div>
      </div>
    </div>
  );
};
