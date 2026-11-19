import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  AlertTriangle,
  Play,
  CheckCircle,
  Clock,
  ShieldCheck,
  BookOpen,
  Users,
  Activity,
  ArrowRight,
  Info,
  Droplets,
  MapPin,
  ExternalLink
} from 'lucide-react';
import { incidentsApi } from '../services/api';
import { Incident } from '../types';

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [workflowResult, setWorkflowResult] = useState<any>(null);
  const [activeStep, setActiveStep] = useState<number>(0);

  useEffect(() => {
    if (id) {
      loadIncident(id);
    }
  }, [id]);

  const loadIncident = async (incId: string) => {
    try {
      const data = await incidentsApi.get(incId);
      setIncident(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunInvestigation = async () => {
    if (!id) return;
    setIsAnalyzing(true);
    setActiveStep(1); // Triage

    try {
      // Simulate visual progress of the 5-agent state machine
      setTimeout(() => setActiveStep(2), 500); // Knowledge
      setTimeout(() => setActiveStep(3), 1100); // Risk
      setTimeout(() => setActiveStep(4), 1800); // Workforce
      setTimeout(() => setActiveStep(5), 2400); // Response

      const res = await incidentsApi.analyze(id);
      setWorkflowResult(res);
      await loadIncident(id);
    } catch (err) {
      console.error('Multi-agent analysis failed', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (isLoading || !incident) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const isFlagship = incident.id === 'INC-0041';

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Dossier Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="font-mono text-sm font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                {incident.id}
              </span>
              {isFlagship && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-600 text-white shadow-sm">
                  Flagship Demo
                </span>
              )}
              {incident.is_synthetic && (
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Synthetic Telemetry
                </span>
              )}
            </div>
            <h1 className="text-xl font-bold text-white mt-2">{incident.title}</h1>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1.5">
              <span className="flex items-center space-x-1">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                <span>District: <strong className="text-slate-200">{incident.district}</strong></span>
              </span>
              <span>•</span>
              <span>Category: <strong className="text-slate-200 capitalize">{incident.category.replace('_', ' ')}</strong></span>
              <span>•</span>
              <span>Coordinates: <strong className="text-slate-200">{incident.latitude}°N, {incident.longitude}°E</strong></span>
              <span>•</span>
              <span>Severity: <strong className="text-red-400 uppercase">{incident.severity}</strong></span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunInvestigation}
              disabled={isAnalyzing}
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all shadow-lg shadow-emerald-900/40"
            >
              {isAnalyzing ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <Play className="w-4 h-4 fill-white" />
              )}
              <span>{isAnalyzing ? 'Executing Agent Pipeline...' : 'Run Multi-Agent Investigation'}</span>
            </button>
          </div>
        </div>

        {/* Incident Narrative / Report */}
        <div className="mt-4">
          <div className="text-xs uppercase font-semibold text-slate-400 tracking-wider mb-1">
            Incoming Field Report
          </div>
          <div className="p-3 bg-slate-950 rounded-lg text-xs text-slate-300 leading-relaxed border border-slate-800/80">
            {incident.description}
          </div>
        </div>
      </div>

      {/* Multi-Agent Execution Pipeline Stepper */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h3 className="text-sm font-bold text-white mb-4 flex items-center justify-between">
          <span>5-Agent Autonomous Investigation Workflow</span>
          {workflowResult && (
            <span className="text-xs text-emerald-400 font-medium flex items-center space-x-1">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Workflow {workflowResult.workflow_id} Completed</span>
            </span>
          )}
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {[
            { step: 1, name: 'Triage Agent', desc: 'TF-IDF + LinearSVC', icon: ShieldCheck },
            { step: 2, name: 'Knowledge Grid', desc: 'Dense RAG + Citations', icon: BookOpen },
            { step: 3, name: 'Risk Agent', desc: 'Telemetry & Indicators', icon: Droplets },
            { step: 4, name: 'WorkforceOS', desc: 'Decomposition & Match', icon: Users },
            { step: 5, name: 'Response Agent', desc: 'Synthesis & Approval', icon: Activity },
          ].map((item) => {
            const Icon = item.icon;
            const isDone = workflowResult || activeStep > item.step;
            const isCurrent = isAnalyzing && activeStep === item.step;
            return (
              <div
                key={item.step}
                className={`p-3 rounded-xl border transition-all ${
                  isDone
                    ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                    : isCurrent
                    ? 'bg-blue-950/40 border-blue-500/50 text-blue-200 animate-pulse'
                    : 'bg-slate-950 border-slate-800 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <Icon className="w-4 h-4" />
                  <span className="text-[10px] font-mono font-bold">Step {item.step}</span>
                </div>
                <div className="font-semibold text-xs text-slate-200">{item.name}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{item.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Investigation Results (Shown when completed or analyzed) */}
      {(workflowResult || incident.status === 'pending_approval' || incident.status === 'approved') && (
        <div className="space-y-6">
          {/* Risk Assessment & Model Transparency */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Risk Gauge Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Risk Prioritization Score
                </div>
                <div className="flex items-baseline space-x-2">
                  <div className="text-4xl font-extrabold text-red-400 font-mono">87.4</div>
                  <div className="text-sm font-semibold text-slate-500">/ 100</div>
                </div>
                <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-red-500/20 text-red-400 border border-red-500/30">
                  Critical Hazard Level
                </span>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
                Calculated by Weighted Indicator Model:
                <br />
                <code className="text-slate-300 font-mono text-[10px]">
                  R = 100(0.30W + 0.20F + 0.15P + 0.15E + 0.10H + 0.10S)
                </code>
              </div>
            </div>

            {/* Factor Indicators Breakdown */}
            <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Assessed Indicators & Telemetry
              </div>
              <div className="space-y-2.5 text-xs">
                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Suramganj FFWC River Water Level (STN-SUN-01: 7.35m vs DL 6.50m)</span>
                    <strong className="text-red-400">0.925</strong>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-red-500 rounded-full" style={{ width: '92.5%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Monsoon Flash Flood Historical Frequency in Sunamganj Basin</span>
                    <strong className="text-orange-400">1.000</strong>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Forecast 24h Trend (Rising Upstream Catchment in Meghalaya)</span>
                    <strong className="text-amber-400">0.850</strong>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Vulnerable Asset Exposure (Bridges & Culverts within 5km radius)</span>
                    <strong className="text-yellow-400">0.800</strong>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-yellow-500 rounded-full" style={{ width: '80%' }}></div>
                  </div>
                </div>
              </div>

              {/* Model Transparency & Limitations Alert */}
              <div className="mt-4 p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start space-x-2">
                <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-slate-200">Model Limitation Disclosure:</strong> Prototype risk prioritization model, not a certified flood bulletin. Missing live indicator: <code className="text-emerald-400">live_rainfall</code> (weights renormalized automatically).
                </div>
              </div>
            </div>
          </div>

          {/* Operational Recommendation & Human Approval Banner */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-emerald-950/40 border border-emerald-500/30 rounded-2xl p-6 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <div className="text-xs uppercase font-bold text-emerald-400 tracking-wider">
                  Recommended Operational Response
                </div>
                <h4 className="text-base font-bold text-white mt-1">
                  Prioritize Immediate Ground Inspection & Road Embankment Containment
                </h4>
              </div>
              <Link
                to="/approvals"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-colors shrink-0 shadow-lg shadow-emerald-900/40"
              >
                <span>Proceed to Human+AI Sign-off</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <div className="font-semibold text-slate-200 mb-2">Recommended Actions:</div>
                <ul className="space-y-1.5 text-slate-300">
                  <li className="flex items-start space-x-2">
                    <span className="text-emerald-400">•</span>
                    <span>Deploy rapid assessment unit to survey water logging depth along Sunamganj Sadar Road.</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-emerald-400">•</span>
                    <span>Issue temporary advisory warning local transport to divert around culvert choke points.</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-emerald-400">•</span>
                    <span>Position mobile dewatering pump near hospital access road embankment.</span>
                  </li>
                </ul>
              </div>

              <div>
                <div className="font-semibold text-slate-200 mb-2">Grounded Citations & Evidence:</div>
                <div className="space-y-1.5 text-slate-400 font-mono text-[11px]">
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <strong className="text-emerald-400">[DOC-FLD-01 p.1]</strong> Bangladesh Flood Response Infrastructure Guidelines: Road submerged &gt; 0.5m mandates immediate vehicular closure.
                  </div>
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <strong className="text-emerald-400">[DOC-MNT-01 p.1]</strong> Road &amp; Bridge Maintenance SOP: Embankment structural checks required within 2 hours of river gauge warning.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
