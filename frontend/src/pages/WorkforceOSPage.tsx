import React, { useState, useEffect } from 'react';
import {
  Users,
  Bot,
  UserCheck,
  CheckCircle2,
  ListTodo,
  Sparkles,
  Calculator,
  ArrowRight,
  Shield,
  MapPin
} from 'lucide-react';
import { workforceApi } from '../services/api';
import { Team, Agent, Task } from '../types';

export const WorkforceOSPage: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState('Sunamganj');
  const [selectedSkill, setSelectedSkill] = useState('flood_response');
  const [simResults, setSimResults] = useState<any[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    loadWorkforce();
  }, []);

  const loadWorkforce = async () => {
    try {
      const [teamsData, agentsData, tasksData] = await Promise.all([
        workforceApi.listTeams(),
        workforceApi.listAgents(),
        workforceApi.listTasks(),
      ]);
      setTeams(teamsData);
      setAgents(agentsData);
      setTasks(tasksData);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const res = await workforceApi.simulateMatch([selectedSkill, 'structural_inspection'], selectedDistrict);
      setSimResults(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Pillar Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-semibold uppercase tracking-wider mb-2">
            <Users className="w-3.5 h-3.5" />
            <span>Pillar 3 · Human-Agent Teaming</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">WorkforceOS Coordination Engine</h1>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Task decomposition with DAG dependency validation, multi-agent operational dispatch, and explainable mathematical candidate scoring.
          </p>
        </div>

        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono text-purple-300">
          Score = 0.40·S + 0.25·Z + 0.20·A + 0.15·L
        </div>
      </div>

      {/* AI Agent Roster */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center space-x-2 mb-4">
          <Bot className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-bold text-white">Autonomous Agent Roster</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {agents.map((ag) => (
            <div key={ag.id} className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">{ag.name}</span>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {ag.status}
                </span>
              </div>
              <div className="text-slate-400 text-[11px] font-mono">{ag.role}</div>
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-1">
                {ag.capabilities?.map((cap, i) => (
                  <span key={i} className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Candidate Team Scoring Simulator */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Calculator className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-bold text-white">Explainable Team Match Scoring Simulator</h2>
          </div>
          <span className="text-xs text-slate-400">Mathematical transparency</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Target District</label>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
            >
              <option value="Sunamganj">Sunamganj (Sylhet Division)</option>
              <option value="Sylhet">Sylhet Sadar</option>
              <option value="Chittagong">Chittagong Port</option>
              <option value="Dhaka">Dhaka Central</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Primary Required Skill</label>
            <select
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
            >
              <option value="flood_response">Flood &amp; Water Response</option>
              <option value="structural_inspection">Structural &amp; Bridge Inspection</option>
              <option value="heavy_equipment">Heavy Dewatering Equipment</option>
              <option value="traffic_control">Traffic &amp; Embankment Barricades</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleSimulate}
              disabled={isSimulating}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-colors shadow-lg shadow-purple-900/30"
            >
              {isSimulating ? (
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>Calculate Explainable Match</span>
            </button>
          </div>
        </div>

        {/* Simulator Results */}
        {simResults.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Ranked Team Candidates (Sub-Score Breakdown):
            </div>
            {simResults.slice(0, 3).map((r, idx) => (
              <div
                key={idx}
                className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs flex flex-col md:flex-row md:items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white text-sm">{r.team_name}</span>
                    <span className="text-[10px] text-slate-400 font-mono">({r.team_id})</span>
                    <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                      {r.district}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-1 font-mono">
                    <span>Skill match: <strong className="text-purple-400">{r.breakdown?.skill_match?.toFixed(2)}</strong></span>
                    <span>•</span>
                    <span>Zone proximity: <strong className="text-purple-400">{r.breakdown?.zone_proximity?.toFixed(2)}</strong></span>
                    <span>•</span>
                    <span>Availability: <strong className="text-purple-400">{r.breakdown?.availability?.toFixed(2)}</strong></span>
                    <span>•</span>
                    <span>Workload factor: <strong className="text-purple-400">{r.breakdown?.workload_factor?.toFixed(2)}</strong></span>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Total Composite Score</div>
                  <div className="text-lg font-bold font-mono text-purple-400">
                    {(r.composite_score * 100).toFixed(1)} / 100
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Human Response Teams List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center space-x-2 mb-4">
          <UserCheck className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-bold text-white">Regional Field Response Teams</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.map((t) => (
            <div key={t.id} className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">{t.name}</span>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {t.status}
                </span>
              </div>
              <div className="flex items-center space-x-1 text-slate-400 text-[11px]">
                <MapPin className="w-3.5 h-3.5" />
                <span>{t.district} ({t.zone})</span>
              </div>
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-1">
                {t.skills?.map((sk, i) => (
                  <span key={i} className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                    {sk.skill} ({(sk.proficiency * 100).toFixed(0)}%)
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
