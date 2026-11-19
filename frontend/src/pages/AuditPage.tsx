import React, { useState, useEffect } from 'react';
import {
  Lock,
  ShieldCheck,
  ShieldAlert,
  CheckCircle,
  Clock,
  Eye,
  RefreshCw,
  X,
  FileCode
} from 'lucide-react';
import { auditApi } from '../services/api';
import { AuditEvent } from '../types';

export const AuditPage: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

  useEffect(() => {
    loadAuditEvents();
  }, []);

  const loadAuditEvents = async () => {
    try {
      const data = await auditApi.listEvents(50);
      setEvents(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    try {
      const res = await auditApi.verifyChain();
      setVerificationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-semibold uppercase tracking-wider mb-2">
            <Lock className="w-3.5 h-3.5" />
            <span>Cryptographic Governance Ledger</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Tamper-Evident SHA-256 Audit Trail</h1>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Every security alert, operational recommendation, and human authorization is permanently recorded in a SHA-256 hash-chained immutable sequence: <code className="text-purple-300 font-mono">H[i] = SHA256(H[i-1] || CanonicalJSON(Event[i]))</code>.
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={isVerifying}
          className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all shadow-lg shadow-purple-900/30 shrink-0"
        >
          {isVerifying ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <ShieldCheck className="w-4 h-4" />
          )}
          <span>Verify Cryptographic Chain</span>
        </button>
      </div>

      {/* Verification Result Banner */}
      {verificationResult && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center justify-between transition-all ${
            verificationResult.verified
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
              : 'bg-red-950/30 border-red-500/40 text-red-200'
          }`}
        >
          <div className="flex items-center space-x-3">
            {verificationResult.verified ? (
              <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0" />
            ) : (
              <ShieldAlert className="w-6 h-6 text-red-400 shrink-0" />
            )}
            <div>
              <div className="font-bold text-sm text-white">
                {verificationResult.verified
                  ? 'Cryptographic Audit Chain Intact & Verified'
                  : 'Audit Chain Tampering Detected!'}
              </div>
              <div className="text-[11px] text-slate-300 mt-0.5">
                Checked <strong>{verificationResult.events_checked}</strong> event(s) from genesis block to current head. Zero tampering detected.
              </div>
            </div>
          </div>

          <div className="text-right font-mono text-[11px]">
            <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300 font-bold uppercase">
              {verificationResult.algorithm}
            </span>
          </div>
        </div>
      )}

      {/* Audit Events Log Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-sm font-bold text-white mb-4">Immutable Event Sequence</h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4 font-sans">Timestamp</th>
                <th className="py-2.5 px-4 font-sans">Actor</th>
                <th className="py-2.5 px-4 font-sans">Event Type</th>
                <th className="py-2.5 px-4 font-sans">Previous Hash (H[i-1])</th>
                <th className="py-2.5 px-4 font-sans">Event Hash (H[i])</th>
                <th className="py-2.5 px-4 text-right font-sans">Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {events.map((e, idx) => (
                <tr key={e.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-4 text-slate-400 whitespace-nowrap">
                    {e.created_at ? new Date(e.created_at).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="py-2.5 px-4 text-slate-200 truncate max-w-[120px]" title={e.actor}>
                    {e.actor.slice(0, 8)}...
                  </td>
                  <td className="py-2.5 px-4 font-sans text-emerald-400 whitespace-nowrap">
                    {e.event_type}
                  </td>
                  <td className="py-2.5 px-4 text-slate-500 truncate max-w-[120px]" title={e.previous_hash}>
                    {e.previous_hash.slice(0, 10)}...
                  </td>
                  <td className="py-2.5 px-4 text-purple-400 font-bold truncate max-w-[120px]" title={e.event_hash}>
                    {e.event_hash.slice(0, 10)}...
                  </td>
                  <td className="py-2.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => setSelectedEvent(e)}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-sans transition-colors inline-flex items-center space-x-1"
                    >
                      <Eye className="w-3 h-3" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payload Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedEvent(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2 mb-2">
              <FileCode className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white">Audited Event Payload</h3>
            </div>
            <div className="text-[11px] text-slate-400 font-mono mb-4">
              ID: {selectedEvent.id} · Type: {selectedEvent.event_type}
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 max-h-72 overflow-y-auto font-mono text-[11px] text-purple-300">
              <pre>{JSON.stringify(selectedEvent.payload, null, 2)}</pre>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
              SHA-256 Hash: {selectedEvent.event_hash}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
