import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertOctagon,
  RotateCcw,
  Clock,
  Zap,
  CheckCircle,
  XCircle,
  Shield,
  Layers,
  Cpu
} from 'lucide-react';
import { agentOpsApi } from '../services/api';
import { AgentRun } from '../types';

export const AgentOpsPage: React.FC = () => {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [circuitBreakers, setCircuitBreakers] = useState<any[]>([]);
  const [spans, setSpans] = useState<any[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    loadAgentOpsData();
  }, []);

  const loadAgentOpsData = async () => {
    try {
      const [runsData, cbData, spansData] = await Promise.all([
        agentOpsApi.listRuns(),
        agentOpsApi.listCircuitBreakers(),
        agentOpsApi.listSpans(),
      ]);
      setRuns(runsData);
      setCircuitBreakers(cbData);
      setSpans(spansData);
      if (runsData.length > 0) {
        setSelectedRunId(runsData[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleTrip = async (agentId: string) => {
    try {
      await agentOpsApi.tripCircuitBreaker(agentId, 'Manual operator test trip');
      await loadAgentOpsData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReset = async (agentId: string) => {
    try {
      await agentOpsApi.resetCircuitBreaker(agentId);
      await loadAgentOpsData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Pillar Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold uppercase tracking-wider mb-2">
            <Activity className="w-3.5 h-3.5" />
            <span>Pillar 4 · Observability &amp; Reliability</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">AgentOps Observability Suite</h1>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Real-time execution telemetry, distributed span tracing, runaway step prevention, and automatic circuit breakers.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800">
          <Cpu className="w-4 h-4 text-amber-400" />
          <span>Active Circuit Breakers: <strong className="text-emerald-400 font-mono">Enforced (10 max steps)</strong></span>
        </div>
      </div>

      {/* Circuit Breaker Control Center */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <AlertOctagon className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-white">Circuit Breaker System Controls</h2>
          </div>
          <span className="text-xs text-slate-400">Protects against infinite loops &amp; runaway agent calls</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { id: 'triage_agent', name: 'Triage Agent' },
            { id: 'knowledge_agent', name: 'Knowledge Grid Agent' },
            { id: 'risk_agent', name: 'Risk Assessment Agent' },
            { id: 'workforce_agent', name: 'WorkforceOS Agent' },
            { id: 'response_agent', name: 'Response Agent' },
            { id: 'supervisor_agent', name: 'Supervisor Agent' },
          ].map((ag) => {
            const cb = circuitBreakers.find((c) => c.agent_id === ag.id);
            const isTripped = cb?.state === 'open' || cb?.state === 'tripped';
            return (
              <div
                key={ag.id}
                className={`p-4 rounded-xl border text-xs flex flex-col justify-between transition-all ${
                  isTripped
                    ? 'bg-red-950/20 border-red-500/40 text-red-300'
                    : 'bg-slate-950 border-slate-800 text-slate-300'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-white">{ag.name}</span>
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                        isTripped
                          ? 'bg-red-500/20 text-red-400 border-red-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      }`}
                    >
                      {isTripped ? 'TRIPPED' : 'NORMAL'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    Limit: 10 steps | 60s max | 3 repeat calls
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex justify-end space-x-2">
                  {isTripped ? (
                    <button
                      onClick={() => handleReset(ag.id)}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center space-x-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Reset</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleTrip(ag.id)}
                      className="px-3 py-1 bg-red-600/20 hover:bg-red-600 text-red-300 hover:text-white border border-red-500/30 rounded text-xs font-semibold flex items-center space-x-1 transition-colors"
                    >
                      <AlertOctagon className="w-3 h-3" />
                      <span>Test Trip</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Agent Execution Runs & Spans */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center space-x-2 mb-4">
          <Layers className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold text-white">Execution Telemetry Runs</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4">Run ID</th>
                <th className="py-2.5 px-4">Incident ID</th>
                <th className="py-2.5 px-4">Agent</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Steps</th>
                <th className="py-2.5 px-4">Completed At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {runs.slice(0, 10).map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40 font-mono">
                  <td className="py-2.5 px-4 font-bold text-slate-200">{r.id}</td>
                  <td className="py-2.5 px-4 text-emerald-400">{r.incident_id}</td>
                  <td className="py-2.5 px-4 text-slate-300 capitalize">{r.agent_id.replace('_', ' ')}</td>
                  <td className="py-2.5 px-4">
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {r.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4">{r.step_count}</td>
                  <td className="py-2.5 px-4 text-slate-400">{r.completed_at ? new Date(r.completed_at).toLocaleTimeString() : 'In progress'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
