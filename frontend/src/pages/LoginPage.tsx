import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  AlertCircle,
  ArrowRight,
  KeyRound,
  UserPlus,
  Lock,
  Mail,
  User,
  CheckCircle2,
  Cpu,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'signin' | 'register'>('signin');
  
  // Sign In State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // Register State
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regRole, setRegRole] = useState('analyst');

  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsLoading(true);
    try {
      await login(email.trim(), password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    if (regPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    setIsLoading(true);
    try {
      await register(regEmail.trim(), regPassword, regFullName.trim(), regRole);
      setSuccessMsg('Account registered successfully! Entering Command Center...');
      setTimeout(() => {
        navigate('/');
      }, 700);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. User may already exist.');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to fill credentials WITHOUT auto-submitting
  const handleFillCredentials = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
    setSuccessMsg(`Credentials for ${demoEmail} populated in form. Click "Authenticate & Enter Command Center" to proceed.`);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden text-slate-100">
      {/* Background radial gradient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-lg relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 shadow-xl shadow-emerald-950/60 text-white font-extrabold text-2xl mb-3 ring-1 ring-emerald-400/30">
            <Cpu className="w-7 h-7" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            InfraSphere AI
          </h1>
          <div className="inline-block mt-1 px-3 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold tracking-wide">
            InfraOps BD · National Command Center
          </div>
          <p className="text-xs text-slate-400 mt-2 max-w-sm mx-auto">
            The Intelligent Operating System for Trusted AI · Multi-Agent Crisis Governance & Real-Time Situational Awareness
          </p>
        </div>

        {/* Card Container */}
        <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 sm:p-7 shadow-2xl shadow-black/80">
          
          {/* Tabs: Sign In vs Register */}
          <div className="flex border-b border-slate-800 mb-5">
            <button
              type="button"
              onClick={() => { setActiveTab('signin'); setError(null); setSuccessMsg(null); }}
              className={`flex-1 pb-3 text-xs sm:text-sm font-semibold flex items-center justify-center space-x-2 border-b-2 transition-all ${
                activeTab === 'signin'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <KeyRound className="w-4 h-4" />
              <span>Sign In (Operator)</span>
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('register'); setError(null); setSuccessMsg(null); }}
              className={`flex-1 pb-3 text-xs sm:text-sm font-semibold flex items-center justify-center space-x-2 border-b-2 transition-all ${
                activeTab === 'register'
                  ? 'border-teal-500 text-teal-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <UserPlus className="w-4 h-4" />
              <span>Register New Operator</span>
            </button>
          </div>

          {/* Feedback Alerts */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start space-x-2 text-xs text-red-300 animate-fadeIn">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-start space-x-2 text-xs text-emerald-300 animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* SIGN IN FORM */}
          {activeTab === 'signin' && (
            <div>
              <form onSubmit={handleSignIn} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Operator Email
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="e.g. manager@infrasphere.bd"
                      required
                      autoComplete="username"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter operator password"
                      required
                      autoComplete="current-password"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg text-sm transition-all flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/50 disabled:opacity-50 cursor-pointer"
                >
                  <span>{isLoading ? 'Verifying Credentials...' : 'Authenticate & Enter Command Center'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>

              {/* DEMO CREDENTIAL POPULATOR (FILLS FORM ONLY - NO 1-CLICK BYPASS) */}
              <div className="mt-6 pt-5 border-t border-slate-800">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-2.5">
                  <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-400">
                    Pre-Seeded Demo Profiles (Click to Fill Form)
                  </span>
                  <span className="text-[10px] text-slate-500">Requires Click to Sign In</span>
                </div>
                
                <div className="grid grid-cols-1 gap-2">
                  <button
                    type="button"
                    onClick={() => handleFillCredentials('manager@infrasphere.bd', 'Demo1234!')}
                    className="flex items-center justify-between p-2.5 bg-slate-950/70 hover:bg-slate-800/80 border border-slate-800 hover:border-emerald-500/40 rounded-lg text-left transition-colors cursor-pointer group"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors">
                        Operations Manager (Full Governance)
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">manager@infrasphere.bd · Pass: Demo1234!</div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium border border-emerald-500/20 whitespace-nowrap">
                      Fill Credentials
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleFillCredentials('analyst@infrasphere.bd', 'Demo1234!')}
                    className="flex items-center justify-between p-2.5 bg-slate-950/70 hover:bg-slate-800/80 border border-slate-800 hover:border-blue-500/40 rounded-lg text-left transition-colors cursor-pointer group"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                        Infrastructure Analyst (Investigations)
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">analyst@infrasphere.bd · Pass: Demo1234!</div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-medium border border-blue-500/20 whitespace-nowrap">
                      Fill Credentials
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleFillCredentials('admin@infrasphere.bd', 'Demo1234!')}
                    className="flex items-center justify-between p-2.5 bg-slate-950/70 hover:bg-slate-800/80 border border-slate-800 hover:border-purple-500/40 rounded-lg text-left transition-colors cursor-pointer group"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-200 group-hover:text-purple-400 transition-colors">
                        System Administrator (Security & Policies)
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">admin@infrasphere.bd · Pass: Demo1234!</div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-medium border border-purple-500/20 whitespace-nowrap">
                      Fill Credentials
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* REGISTER NEW OPERATOR FORM */}
          {activeTab === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    value={regFullName}
                    onChange={(e) => setRegFullName(e.target.value)}
                    placeholder="e.g. Dr. Tanvir Ahmed"
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Official Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="e.g. tanvir@pwd.gov.bd"
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Password (min 6 characters)
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="password"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    placeholder="Choose a strong password"
                    required
                    minLength={6}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Operational Duty Role
                </label>
                <select
                  value={regRole}
                  onChange={(e) => setRegRole(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
                >
                  <option value="analyst">Infrastructure Analyst (Assessments & RAG Query)</option>
                  <option value="manager">Operations Manager (Incident Response & Action Approval)</option>
                  <option value="field_coordinator">Field Coordinator (Dispatch & Team Tracking)</option>
                  <option value="ai_auditor">AI Auditor (Model Governance & Safety Audits)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-teal-600 hover:bg-teal-500 active:bg-teal-700 text-white font-semibold py-2.5 rounded-lg text-sm transition-all flex items-center justify-center space-x-2 shadow-lg shadow-teal-950/50 disabled:opacity-50 cursor-pointer"
              >
                <span>{isLoading ? 'Registering Operator...' : 'Create Secure Operator Account'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Security & Compliance Banner */}
          <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
            <div className="flex items-center space-x-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Role-Based Access Control (RBAC)</span>
            </div>
            <span>TLS / JWT Encrypted</span>
          </div>
        </div>

        {/* Footer Credit */}
        <div className="text-center mt-6 text-xs text-slate-500">
          InfraSphere AI · National Infrastructure Resilience · Powered by Google Gemini
        </div>
      </div>
    </div>
  );
};
