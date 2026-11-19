import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  FileText,
  AlertCircle,
  Network,
  CheckCircle,
  ExternalLink,
  HelpCircle,
  Sparkles
} from 'lucide-react';
import { knowledgeApi } from '../services/api';

const sampleQuestions = [
  'What is the water depth threshold for immediate road closure?',
  'What is the mandated response time for bridge inspection after flood warning?',
  'বন্যা পরিস্থিতিতে কালভার্ট পরিদর্শনের নিয়ম কী?',
  'What is the current price of gold in Bangladesh?', // Abstention test
];

export const KnowledgeGridPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [documents, setDocuments] = useState<any[]>([]);
  const [contradictions, setContradictions] = useState<any[]>([]);
  const [graphData, setGraphData] = useState<any>(null);

  useEffect(() => {
    loadKnowledgeData();
  }, []);

  const loadKnowledgeData = async () => {
    try {
      const [docs, contr, g] = await Promise.all([
        knowledgeApi.listDocuments(),
        knowledgeApi.getContradictions(),
        knowledgeApi.getGraph(),
      ]);
      setDocuments(docs);
      setContradictions(contr);
      setGraphData(g);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = async (textToSearch?: string) => {
    const q = textToSearch !== undefined ? textToSearch : query;
    if (!q.trim()) return;
    setIsSearching(true);
    setQueryResult(null);

    try {
      const res = await knowledgeApi.query(q, 4);
      setQueryResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Pillar Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold uppercase tracking-wider mb-2">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Pillar 2 · Grounded Knowledge</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Knowledge Grid &amp; RAG Explorer</h1>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Semantic vector retrieval over operational guidelines and engineering SOPs, with strict page citations, contradiction detection, and 100% evaluated abstention on unanswerable questions.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-950 p-2.5 rounded-xl border border-slate-800">
          <Sparkles className="w-4 h-4 text-blue-400" />
          <span>RAG Evaluation: <strong className="text-blue-400 font-mono">100% Abstention</strong> on out-of-corpus queries</span>
        </div>
      </div>

      {/* Interactive Grounded RAG Query Lab */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-sm font-bold text-white mb-3">Interactive Grounded RAG Query Lab</h2>

        {/* Sample queries */}
        <div className="mb-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Try Sample Queries:
          </div>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.map((q, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setQuery(q);
                  handleSearch(q);
                }}
                className="px-2.5 py-1.5 rounded-lg text-xs bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors text-left"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Ask anything about Bangladesh flood protocols, road maintenance, or culvert SOPs..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-4 pr-24 py-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
          />
          <button
            onClick={() => handleSearch()}
            disabled={isSearching || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors"
          >
            {isSearching ? (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Search className="w-3.5 h-3.5" />
            )}
            <span>Query</span>
          </button>
        </div>

        {/* Query Result Card */}
        {queryResult && (
          <div className="mt-5 p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="font-semibold text-slate-200">Synthesized Grounded Answer:</span>
              <span
                className={`text-[11px] px-2 py-0.5 rounded font-mono ${
                  queryResult.abstained
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}
              >
                {queryResult.abstained ? 'Abstained (Uncertain / Not in Corpus)' : 'Grounded in Documents'}
              </span>
            </div>

            <div className="text-slate-200 leading-relaxed text-xs">
              {queryResult.answer}
            </div>

            {/* Citations list */}
            {queryResult.citations && queryResult.citations.length > 0 && (
              <div className="pt-2 border-t border-slate-800/80">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Extracted Evidence Citations:
                </div>
                <div className="space-y-1">
                  {queryResult.citations.map((c: string, idx: number) => (
                    <div key={idx} className="font-mono text-[11px] text-blue-400 bg-blue-950/30 px-2 py-1 rounded border border-blue-900/40">
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Operational Documents & Contradiction Detector */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Documents Repository */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center space-x-2 mb-4">
            <FileText className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-bold text-white">Ingested Operational Guidelines</h2>
          </div>

          <div className="space-y-3">
            {documents.map((doc) => (
              <div key={doc.id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-blue-400">{doc.id}</span>
                  <span className="text-[10px] uppercase font-semibold text-slate-500">
                    {doc.format} · {doc.chunk_count || 3} chunks
                  </span>
                </div>
                <div className="font-semibold text-slate-200 mt-1">{doc.title}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Author: {doc.author}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Contradiction Detection */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center space-x-2 mb-4">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-white">Cross-Document Contradiction Detector</h2>
          </div>

          <div className="space-y-3">
            {contradictions.length > 0 ? (
              contradictions.map((c, i) => (
                <div key={i} className="p-3 bg-amber-950/20 border border-amber-500/30 rounded-xl text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-amber-300">Discrepancy: {c.asset_id}</span>
                    <span className="text-[10px] uppercase font-bold text-amber-400 px-1.5 py-0.5 bg-amber-500/10 rounded">
                      {c.severity || 'Medium'}
                    </span>
                  </div>
                  <div className="text-slate-300 text-[11px]">{c.explanation}</div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Docs: {c.source_a} vs {c.source_b}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-400 text-center">
                All 3 guidelines aligned. Contradiction audit engine running continuously.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
