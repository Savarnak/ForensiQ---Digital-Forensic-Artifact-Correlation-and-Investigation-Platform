import React, { useState, useEffect } from 'react';
import { AlertCircle, AlertTriangle, HelpCircle, FileSearch, RefreshCw } from 'lucide-react';
import { fetchGapsAndContradictions } from '../services/api';

export default function GapContradictionPanel({ activeCase, orchestratorResults }) {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeCase) {
      loadAnalysis();
    }
  }, [activeCase, orchestratorResults]);

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const data = await fetchGapsAndContradictions(activeCase.id);
      setAnalysisData(data);
    } catch (err) {
      console.error('Error loading gaps & contradictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const gaps = analysisData?.evidence_gaps || [];
  const contradictions = analysisData?.contradictions || [];
  const chainIssues = analysisData?.investigation_chain_issues || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-amber-400" />
            9. Evidence Gap & Contradiction Analysis Panel
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Detects referenced but missing evidence, timestamp/attribute contradictions, and unverified relationship chains.
          </p>
        </div>

        <button
          onClick={loadAnalysis}
          disabled={loading}
          className="text-xs font-mono bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Analysis Engine</span>
        </button>
      </div>

      {/* Summary Badges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        <div className="bg-slate-950 p-4 rounded-xl border border-amber-800/60">
          <span className="text-amber-400 font-bold block mb-1">Referenced Missing Evidence ({gaps.length})</span>
          <p className="text-[11px] text-slate-400">Devices or files cited in chats/OCR lacking supporting evidence.</p>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-rose-800/60">
          <span className="text-rose-400 font-bold block mb-1">Evidence Contradictions ({contradictions.length})</span>
          <p className="text-[11px] text-slate-400">Timestamp or metadata attribute mismatches across evidence artifacts.</p>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-purple-800/60">
          <span className="text-purple-400 font-bold block mb-1">Incomplete Chains ({chainIssues.length})</span>
          <p className="text-[11px] text-slate-400">Single-source handle or secondary device links requiring verification.</p>
        </div>
      </div>

      {/* Section 1: Evidence Gaps */}
      {gaps.length > 0 && (
        <div className="space-y-3 font-mono text-xs">
          <h3 className="font-bold text-amber-300 uppercase tracking-wider text-xs">
            1. Referenced But Missing Digital Evidence ({gaps.length})
          </h3>

          <div className="space-y-2">
            {gaps.map((g, idx) => (
              <div key={idx} className="bg-slate-950 border border-amber-900/50 p-4 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-300">Entity: {g.referenced_entity} ({g.entity_type})</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                    Source: {g.source_evidence}
                  </span>
                </div>
                <p className="text-slate-300 font-sans text-xs">{g.reason}</p>
                <div className="text-[11px] text-cyan-400 bg-slate-900 p-2 rounded border border-slate-800">
                  <strong>Recommended Action:</strong> {g.recommended_action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 2: Contradictions */}
      {contradictions.length > 0 && (
        <div className="space-y-3 font-mono text-xs">
          <h3 className="font-bold text-rose-300 uppercase tracking-wider text-xs">
            2. Evidence Contradictions & Timestamp Mismatches ({contradictions.length})
          </h3>

          <div className="space-y-2">
            {contradictions.map((c, idx) => (
              <div key={idx} className="bg-slate-950 border border-rose-900/50 p-4 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-rose-300">{c.title}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800">
                    {c.contradiction_type}
                  </span>
                </div>
                <p className="text-slate-300 font-sans text-xs">{c.description}</p>
                <div className="text-[11px] text-emerald-400 bg-slate-900 p-2 rounded border border-slate-800">
                  <strong>Recommended Action:</strong> {c.recommended_investigator_action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
