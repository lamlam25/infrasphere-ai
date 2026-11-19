import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckSquare,
  ShieldCheck,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  ArrowRight,
  Lock,
  MessageSquare,
  CheckCircle,
  XCircle,
  RotateCcw
} from 'lucide-react';
import { approvalsApi } from '../services/api';
import { Approval } from '../types';

export const HumanAIPage: React.FC = () => {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [comment, setComment] = useState('Ground inspection prioritized as per FFWC telemetry.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [decisionOutcome, setDecisionOutcome] = useState<any>(null);
  const [feedbackSaved, setFeedbackSaved] = useState(false);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    try {
      const data = await approvalsApi.list();
      setApprovals(data);
      if (data.length > 0) {
        setSelectedApproval(data[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDecision = async (decision: 'approved' | 'rejected' | 'needs_revision') => {
    if (!selectedApproval) return;
    setIsSubmitting(true);
    setDecisionOutcome(null);

    try {
      const res = await approvalsApi.submitDecision(selectedApproval.id, decision, comment);
      setDecisionOutcome(res.data);
      await loadApprovals();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Decision failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFeedback = async (rating: 'helpful' | 'unhelpful') => {
    if (!selectedApproval) return;
    try {
      await approvalsApi.submitFeedback(selectedApproval.id, rating, 'Operator approved model recommendation.');
      setFeedbackSaved(true);
      setTimeout(() => setFeedbackSaved(false), 3000);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Pillar Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold uppercase tracking-wider mb-2">
            <CheckSquare className="w-3.5 h-3.5" />
            <span>Pillar 5 · Human-in-the-Loop Governance</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Human+AI Approval Center</h1>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Accountable operational decision making: AI analyzes, retrieves, and proposes; certified human operators inspect evidence and sign off before dispatch.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800 text-emerald-400">
          <Lock className="w-4 h-4" />
          <span>Every decision logged to SHA-256 Audit Chain</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Approvals Queue */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <h2 className="text-sm font-bold text-white mb-3">Pending Recommendations Queue</h2>
          <div className="space-y-2">
            {approvals.map((appr) => {
              const isSelected = selectedApproval?.id === appr.id;
              return (
                <button
                  key={appr.id}
                  onClick={() => {
                    setSelectedApproval(appr);
                    setDecisionOutcome(null);
                  }}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    isSelected
                      ? 'bg-emerald-950/20 border-emerald-500/40'
                      : 'bg-slate-950 border-slate-800 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="font-bold text-white">{appr.id}</span>
                    <span
                      className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                        appr.status === 'pending'
                          ? 'bg-amber-500/10 text-amber-400'
                          : appr.status === 'approved'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : 'bg-red-500/10 text-red-400'
                      }`}
                    >
                      {appr.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 font-semibold truncate">
                    Incident: {appr.incident_id}
                  </div>
                  <div className="text-[11px] text-slate-500 truncate mt-0.5">
                    {appr.recommendation?.summary || 'Operational plan ready for review'}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Recommendation Dossier & Decision Controls */}
        <div className="lg:col-span-2 space-y-6">
          {selectedApproval ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                  <div className="text-[11px] font-mono text-emerald-400">
                    Reviewing Approval {selectedApproval.id}
                  </div>
                  <h3 className="text-base font-bold text-white mt-0.5">
                    Operational Recommendation for {selectedApproval.incident_id}
                  </h3>
                </div>

                <Link
                  to={`/incidents/${selectedApproval.incident_id}`}
                  className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
                >
                  <span>View Incident</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Recommendation Summary */}
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Proposed Action Summary:
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-200 leading-relaxed">
                  {selectedApproval.recommendation?.summary ||
                    'Prioritize immediate ground inspection and flood hazard containment for Sunamganj Sadar Road.'}
                </div>
              </div>

              {/* Cited Evidence Checklist */}
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Document Grounding &amp; Citations:
                </div>
                <div className="space-y-1.5 text-xs text-slate-300">
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800/80 font-mono text-[11px] text-emerald-300">
                    [DOC-FLD-01 p.1] Road submerged &gt; 0.5m mandates immediate vehicular closure.
                  </div>
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800/80 font-mono text-[11px] text-emerald-300">
                    [DOC-MNT-01 p.1] Embankment structural checks required within 2 hours of river gauge warning.
                  </div>
                </div>
              </div>

              {/* Decision Outcome Alert */}
              {decisionOutcome && (
                <div className="p-4 bg-emerald-950/30 border border-emerald-500/40 rounded-xl text-xs space-y-2">
                  <div className="flex items-center space-x-2 text-emerald-400 font-bold">
                    <CheckCircle className="w-4 h-4" />
                    <span>Decision Recorded: {decisionOutcome.status?.toUpperCase()}</span>
                  </div>
                  <div className="text-slate-300">
                    Audit Hash generated:{' '}
                    <code className="text-emerald-400 font-mono text-[11px]">
                      {decisionOutcome.audit_hash}
                    </code>
                  </div>
                  <div className="pt-2">
                    <Link
                      to="/audit"
                      className="text-emerald-400 underline font-semibold flex items-center space-x-1 text-xs"
                    >
                      <span>View and verify cryptographic chain in Audit Ledger →</span>
                    </Link>
                  </div>
                </div>
              )}

              {/* Human Decision Form */}
              <div className="pt-4 border-t border-slate-800 space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Certified Operator Audit Rationale:
                  </label>
                  <input
                    type="text"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Enter reason for approval or modification..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleDecision('approved')}
                      disabled={isSubmitting || selectedApproval.status === 'approved'}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-lg shadow-emerald-900/30"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Approve &amp; Dispatch</span>
                    </button>

                    <button
                      onClick={() => handleDecision('needs_revision')}
                      disabled={isSubmitting}
                      className="px-3.5 py-2 bg-amber-600/20 hover:bg-amber-600 text-amber-300 hover:text-white border border-amber-500/30 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Request Revision</span>
                    </button>

                    <button
                      onClick={() => handleDecision('rejected')}
                      disabled={isSubmitting}
                      className="px-3.5 py-2 bg-red-600/20 hover:bg-red-600 text-red-300 hover:text-white border border-red-500/30 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>

                  {/* RLHF Operator Feedback Buttons */}
                  <div className="flex items-center space-x-2 text-xs text-slate-400">
                    <span>Feedback:</span>
                    <button
                      onClick={() => handleFeedback('helpful')}
                      title="Mark recommendation helpful"
                      className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-emerald-400 transition-colors"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleFeedback('unhelpful')}
                      title="Mark recommendation unhelpful"
                      className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                    {feedbackSaved && <span className="text-emerald-400 text-[10px]">Saved!</span>}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl text-center text-xs text-slate-500">
              No approval selected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
