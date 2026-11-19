import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Search,
  Filter,
  Plus,
  ShieldAlert,
  ShieldCheck,
  CheckCircle,
  ExternalLink,
  MapPin,
  X
} from 'lucide-react';
import { incidentsApi, secureAiApi } from '../services/api';
import { Incident } from '../types';

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filteredIncidents, setFilteredIncidents] = useState<Incident[]>([]);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);

  // New incident modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newDistrict, setNewDistrict] = useState('Sylhet');
  const [newCategory, setNewCategory] = useState('flooding');
  const [newSeverity, setNewSeverity] = useState<'low' | 'medium' | 'high' | 'critical'>('high');
  const [newLat, setNewLat] = useState('24.8949');
  const [newLon, setNewLon] = useState('91.8687');
  const [secureAiCheck, setSecureAiCheck] = useState<{ decision?: string; threat?: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadIncidents();
  }, []);

  const loadIncidents = async () => {
    try {
      const data = await incidentsApi.list();
      setIncidents(data);
      setFilteredIncidents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let result = incidents;
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          i.district.toLowerCase().includes(q) ||
          i.id.toLowerCase().includes(q)
      );
    }
    if (categoryFilter !== 'all') {
      result = result.filter((i) => i.category.toLowerCase() === categoryFilter.toLowerCase());
    }
    if (severityFilter !== 'all') {
      result = result.filter((i) => i.severity.toLowerCase() === severityFilter.toLowerCase());
    }
    setFilteredIncidents(result);
  }, [search, categoryFilter, severityFilter, incidents]);

  const handleDescChange = async (text: string) => {
    setNewDesc(text);
    if (text.length > 5) {
      try {
        const check = await secureAiApi.inspectPrompt(text);
        setSecureAiCheck({ decision: check.decision, threat: check.threat_type });
      } catch (err) {
        // ignore
      }
    } else {
      setSecureAiCheck(null);
    }
  };

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (secureAiCheck?.decision === 'block') {
      alert('SecureAI blocked this report: malicious input or prompt injection detected.');
      return;
    }
    setIsSubmitting(true);
    try {
      await incidentsApi.create({
        title: newTitle,
        description: newDesc,
        district: newDistrict,
        category: newCategory,
        severity: newSeverity,
        latitude: parseFloat(newLat) || 24.89,
        longitude: parseFloat(newLon) || 91.86,
        language: /[\u0980-\u09FF]/.test(newDesc) ? 'bn' : 'en',
        source: 'manual_intake',
        is_synthetic: true,
      });
      setIsModalOpen(false);
      setNewTitle('');
      setNewDesc('');
      setSecureAiCheck(null);
      await loadIncidents();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const severityBadge = (sev: string) => {
    const map: Record<string, string> = {
      critical: 'bg-red-500/10 text-red-400 border-red-500/20',
      high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase border ${map[sev] || ''}`}>
        {sev}
      </span>
    );
  };

  const statusBadge = (st: string) => {
    const map: Record<string, string> = {
      reported: 'bg-slate-800 text-slate-300 border-slate-700',
      investigating: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      pending_approval: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      approved: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      resolved: 'bg-emerald-600 text-white border-transparent',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${map[st] || 'bg-slate-800 text-slate-400'}`}>
        {st.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Bangladesh Infrastructure Incidents</h1>
          <p className="text-xs text-slate-400 mt-1">
            Intake, triage, and multi-agent coordination records ({filteredIncidents.length} of {incidents.length} shown)
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-lg shadow-emerald-900/30"
        >
          <Plus className="w-4 h-4" />
          <span>New Incident Intake</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID, district, or title..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Categories</option>
            <option value="flooding">Flooding</option>
            <option value="bridge_damage">Bridge Damage</option>
            <option value="road_washout">Road Washout</option>
            <option value="drainage_block">Drainage Block</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Incident ID</th>
                <th className="py-3 px-4">District / Location</th>
                <th className="py-3 px-4">Title & Context</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Workflow Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {filteredIncidents.map((inc) => {
                const isFlagship = inc.id === 'INC-0041';
                return (
                  <tr
                    key={inc.id}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isFlagship ? 'bg-emerald-950/20 border-l-2 border-emerald-500' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-mono font-bold text-slate-200 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <span>{inc.id}</span>
                        {isFlagship && (
                          <span className="text-[9px] font-semibold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1 py-0.2 rounded">
                            Demo
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-200 whitespace-nowrap">
                      <div className="flex items-center space-x-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span>{inc.district}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 max-w-md truncate">
                      <div className="font-semibold text-slate-200 truncate">{inc.title}</div>
                      <div className="text-[11px] text-slate-500 truncate">{inc.description}</div>
                    </td>
                    <td className="py-3 px-4 capitalize whitespace-nowrap">{inc.category.replace('_', ' ')}</td>
                    <td className="py-3 px-4 whitespace-nowrap">{severityBadge(inc.severity)}</td>
                    <td className="py-3 px-4 whitespace-nowrap">{statusBadge(inc.status)}</td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <Link
                        to={`/incidents/${inc.id}`}
                        className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                          isFlagship
                            ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                        }`}
                      >
                        <span>Investigate</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: New Incident Intake */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-base font-bold text-white mb-1">New Infrastructure Incident Intake</h3>
            <p className="text-xs text-slate-400 mb-4">
              Protected by SecureAI Gateway prompt inspection & input threat defense.
            </p>

            <form onSubmit={handleCreateIncident} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Submerged Culvert at Sunamganj By-pass"
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">District</label>
                  <input
                    type="text"
                    value={newDistrict}
                    onChange={(e) => setNewDistrict(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
                  >
                    <option value="flooding">Flooding</option>
                    <option value="bridge_damage">Bridge Damage</option>
                    <option value="road_washout">Road Washout</option>
                    <option value="drainage_block">Drainage Block</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Report Description (Bangla or English)
                </label>
                <textarea
                  value={newDesc}
                  onChange={(e) => handleDescChange(e.target.value)}
                  rows={3}
                  placeholder="Describe damage, road impassability, or flood depth..."
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                />
                {/* Real-time SecureAI Indicator */}
                {secureAiCheck && (
                  <div
                    className={`mt-1.5 p-2 rounded-lg text-xs flex items-center justify-between border ${
                      secureAiCheck.decision === 'block'
                        ? 'bg-red-500/10 border-red-500/20 text-red-400'
                        : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    <div className="flex items-center space-x-1.5">
                      {secureAiCheck.decision === 'block' ? (
                        <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
                      ) : (
                        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                      )}
                      <span>
                        SecureAI Status: <strong>{secureAiCheck.decision?.toUpperCase()}</strong>
                        {secureAiCheck.threat && ` (${secureAiCheck.threat})`}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || secureAiCheck?.decision === 'block'}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  {isSubmitting ? 'Submitting...' : 'Register Incident'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
