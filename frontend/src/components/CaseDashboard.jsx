import React, { useState, useEffect } from 'react';
import {
  FolderPlus,
  Folder,
  CheckCircle,
  Shield,
  ShieldAlert,
  Sparkles,
  Layers,
  FileText,
  Activity,
  GitMerge,
  Clock,
  CheckSquare,
  Lock,
  Search,
  ExternalLink,
  ChevronRight,
  UserCheck,
  AlertTriangle
} from 'lucide-react';
import {
  createCase,
  loadSyntheticCase,
  fetchEvidence,
  fetchLeads,
  fetchOrchestratorResults,
  fetchAuditEvents
} from '../services/api';

export default function CaseDashboard({ cases, activeCase, onSelectCase, onCaseCreated, onRefreshData }) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [caseNumber, setCaseNumber] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isQuickLoading, setIsQuickLoading] = useState(false);

  // Dynamic Case Analytics State
  const [metrics, setMetrics] = useState({
    loading: false,
    evidence: [],
    leads: [],
    orchRes: null,
    auditEvents: []
  });

  useEffect(() => {
    if (!activeCase?.id) return;
    let isMounted = true;
    setMetrics((prev) => ({ ...prev, loading: true }));

    Promise.allSettled([
      fetchEvidence(activeCase.id),
      fetchLeads(activeCase.id),
      fetchOrchestratorResults(activeCase.id),
      fetchAuditEvents(activeCase.id)
    ]).then(([evRes, leadRes, orchRes, auditRes]) => {
      if (!isMounted) return;
      setMetrics({
        loading: false,
        evidence: evRes.status === 'fulfilled' && Array.isArray(evRes.value) ? evRes.value : [],
        leads: leadRes.status === 'fulfilled' && Array.isArray(leadRes.value) ? leadRes.value : [],
        orchRes: orchRes.status === 'fulfilled' ? orchRes.value : null,
        auditEvents: auditRes.status === 'fulfilled' && Array.isArray(auditRes.value) ? auditRes.value : []
      });
    });

    return () => {
      isMounted = false;
    };
  }, [activeCase?.id]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!caseNumber || !title) return;
    setIsCreating(true);
    try {
      const created = await createCase({
        case_number: caseNumber,
        title,
        description: description || 'Digital evidence correlation and investigation case'
      });
      onCaseCreated(created);
      setShowCreateModal(false);
      setCaseNumber('');
      setTitle('');
      setDescription('');
    } catch (err) {
      alert(`Case creation failed: ${err.message}`);
    } finally {
      setIsCreating(false);
    }
  };

  const handleQuickLoadSyntheticCase = async () => {
    setIsQuickLoading(true);
    try {
      const syntheticCase = await loadSyntheticCase();
      onCaseCreated(syntheticCase);
    } catch (err) {
      alert(`Synthetic case loading failed: ${err.message}`);
    } finally {
      setIsQuickLoading(false);
    }
  };

  // Helper values derived dynamically from active case state
  const evidenceCount = metrics.evidence.length;
  const findingsCount = metrics.orchRes?.findings?.count ?? metrics.orchRes?.findings?.raw?.length ?? null;
  const nodesCount = metrics.orchRes?.correlations?.knowledge_graph?.nodes_count ?? metrics.orchRes?.correlations?.knowledge_graph?.nodes?.length ?? null;
  const edgesCount = metrics.orchRes?.correlations?.knowledge_graph?.edges_count ?? metrics.orchRes?.correlations?.knowledge_graph?.edges?.length ?? null;
  const timelineCount = metrics.orchRes?.correlations?.timeline_events?.length ?? null;
  const leadsCount = metrics.leads.length;
  const auditCount = metrics.auditEvents.length;

  // Separate Active Case from Other Cases
  const otherCases = cases.filter((c) => c.id !== activeCase?.id);

  // Categorize Evidence for active case
  const evidenceGrouped = metrics.evidence.reduce((acc, ev) => {
    const type = ev.file_type || 'UNSPECIFIED';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});

  // Pipeline execution status check
  const pipelineSteps = [
    { label: 'Evidence Ingestion', active: evidenceCount > 0, count: evidenceCount > 0 ? `${evidenceCount} Items` : '0 Items' },
    { label: 'Agentic Analysis', active: findingsCount !== null && findingsCount > 0, count: findingsCount !== null ? `${findingsCount} Findings` : 'Pending' },
    { label: 'Intelligence Fusion', active: nodesCount !== null && nodesCount > 0, count: nodesCount !== null ? `${nodesCount} Entities` : 'Pending' },
    { label: 'Knowledge Graph', active: edgesCount !== null && edgesCount > 0, count: edgesCount !== null ? `${edgesCount} Edges` : 'Pending' },
    { label: 'Timeline Reconstruction', active: timelineCount !== null && timelineCount > 0, count: timelineCount !== null ? `${timelineCount} Events` : 'Pending' },
    { label: 'Lead Generation', active: leadsCount > 0, count: leadsCount > 0 ? `${leadsCount} Leads` : 'Pending' },
    { label: 'Human Review', active: metrics.leads.some((l) => l.status === 'APPROVED' || l.status === 'REJECTED'), count: 'Active' },
    { label: 'Audit Trail', active: auditCount > 0, count: auditCount > 0 ? `${auditCount} Events` : 'Recorded' }
  ];

  return (
    <div className="space-y-6 font-sans">
      {/* =========================================================
          1. HEADER / HERO COMMAND CENTER BANNER
      ========================================================= */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <span className="bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-mono text-xs font-bold px-3 py-1 rounded-md tracking-wider flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-cyan-400" />
                ARGUS COMMAND CENTER
              </span>
              <span className="text-xs font-mono text-slate-400">
                Agentic Investigation Backbone
              </span>
            </div>

            <h1 className="text-2xl lg:text-3xl font-extrabold text-slate-100 tracking-tight mt-2">
              From Fragmented Evidence to Explainable Intelligence
            </h1>
            <p className="text-xs lg:text-sm text-slate-400 mt-1 max-w-3xl">
              Cross-source digital correlation, multi-modal entity extraction, LangGraph planner orchestration, and human-in-the-loop auditability.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={handleQuickLoadSyntheticCase}
              disabled={isQuickLoading}
              className="flex items-center space-x-2 text-xs font-mono font-semibold bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/60 px-4 py-2.5 rounded-lg transition shadow-md"
            >
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>{isQuickLoading ? 'Initializing Case 001...' : 'Load Synthetic Case 001'}</span>
            </button>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 text-xs font-mono font-semibold bg-cyan-600 hover:bg-cyan-500 text-slate-950 px-4 py-2.5 rounded-lg transition shadow-cyan-600/20 shadow-md"
            >
              <FolderPlus className="w-4 h-4" />
              <span>New Case</span>
            </button>
          </div>
        </div>
      </div>

      {/* =========================================================
          2. ACTIVE INVESTIGATION BANNER & METRICS
      ========================================================= */}
      {activeCase && (
        <div className="bg-slate-900 border border-cyan-500/40 rounded-xl p-6 shadow-lg space-y-6 relative ring-1 ring-cyan-500/20">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2 font-mono">
                <span className="text-xs text-slate-500 uppercase tracking-widest font-bold">Active Case</span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/80">
                  {activeCase.case_number}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/80">
                  {activeCase.status || 'ACTIVE'}
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-100 mt-1">
                {activeCase.title}
              </h2>
              {activeCase.description && (
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
                  {activeCase.description}
                </p>
              )}
            </div>

            <div className="text-right font-mono text-xs text-slate-400 shrink-0">
              <div>Created: {new Date(activeCase.created_at).toLocaleDateString()}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">ID: {activeCase.id.slice(0, 18)}...</div>
            </div>
          </div>

          {/* 7 Core Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 font-mono">
            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Evidence</span>
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 mt-2">
                {metrics.loading ? '...' : (evidenceCount !== null ? evidenceCount : '--')}
              </div>
              <span className="text-[10px] text-slate-500 mt-1">Ingested Items</span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Findings</span>
                <Activity className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 mt-2">
                {metrics.loading ? '...' : (findingsCount !== null ? findingsCount : '--')}
              </div>
              <span className="text-[10px] text-slate-500 mt-1">Extracted Insights</span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Entities</span>
                <Layers className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 mt-2">
                {metrics.loading ? '...' : (nodesCount !== null ? nodesCount : '--')}
              </div>
              <span className="text-[10px] text-slate-500 mt-1">Canonical Nodes</span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Relationships</span>
                <GitMerge className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 mt-2">
                {metrics.loading ? '...' : (edgesCount !== null ? edgesCount : '--')}
              </div>
              <span className="text-[10px] text-slate-500 mt-1">Correlated Edges</span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Timeline</span>
                <Clock className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 mt-2">
                {metrics.loading ? '...' : (timelineCount !== null ? timelineCount : '--')}
              </div>
              <span className="text-[10px] text-slate-500 mt-1">Chronological Events</span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Leads</span>
                <CheckSquare className="w-3.5 h-3.5 text-indigo-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 mt-2">
                {metrics.loading ? '...' : (leadsCount !== null ? leadsCount : '--')}
              </div>
              <span className="text-[10px] text-slate-500 mt-1">Candidate Actions</span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Audit Log</span>
                <Lock className="w-3.5 h-3.5 text-cyan-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 mt-2">
                {metrics.loading ? '...' : (auditCount !== null ? auditCount : '--')}
              </div>
              <span className="text-[10px] text-slate-500 mt-1">System Records</span>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================
          3. INVESTIGATION PIPELINE VISUAL WORKFLOW
      ========================================================= */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="font-bold text-slate-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            ARGUS Intelligence Fusion Pipeline Workflow
          </h3>
          <span className="text-[11px] text-slate-500">Autonomous LangGraph Orchestration</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
          {pipelineSteps.map((step, idx) => (
            <div
              key={idx}
              className={`p-2.5 rounded-lg border flex flex-col justify-between transition ${
                step.active
                  ? 'bg-slate-950 border-cyan-500/50 text-cyan-300'
                  : 'bg-slate-950/40 border-slate-800 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between text-[10px]">
                <span className="font-bold">{idx + 1}. Step</span>
                {step.active ? (
                  <CheckCircle className="w-3 h-3 text-cyan-400" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-slate-700" />
                )}
              </div>
              <div className="font-bold text-slate-200 text-[11px] mt-2 line-clamp-1">
                {step.label}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                {step.count}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* =========================================================
          4. EVIDENCE INTELLIGENCE & PRIORITY LEADS GRID
      ========================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Evidence & Priority Leads */}
        <div className="lg:col-span-2 space-y-6">
          {/* EVIDENCE SUMMARY PANEL */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 font-mono">
                <FileText className="w-4 h-4 text-cyan-400" />
                Ingested Evidence Artifacts ({evidenceCount})
              </h3>
              <span className="text-xs font-mono text-slate-400">
                {Object.keys(evidenceGrouped).length} Types Identified
              </span>
            </div>

            {metrics.evidence.length === 0 ? (
              <div className="text-center py-6 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs font-mono">
                No evidence items uploaded to active case yet.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 font-mono text-xs">
                {metrics.evidence.map((ev) => (
                  <div key={ev.id} className="bg-slate-950 border border-slate-800 p-3 rounded-lg flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-bold uppercase">
                        {ev.file_type || 'FILE'}
                      </span>
                      <div className="font-semibold text-slate-200 mt-2 truncate text-xs" title={ev.file_name}>
                        {ev.file_name}
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-2 pt-2 border-t border-slate-900">
                      {new Date(ev.created_at || Date.now()).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* PRIORITY CANDIDATE LEADS */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 font-mono">
                <CheckSquare className="w-4 h-4 text-cyan-400" />
                Priority Candidate Leads ({metrics.leads.length})
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                Explainable Priority Scoring
              </span>
            </div>

            {metrics.leads.length === 0 ? (
              <div className="text-center py-6 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs font-mono">
                No candidate leads generated yet. Run Agentic Investigation to populate leads.
              </div>
            ) : (
              <div className="space-y-3 font-mono text-xs">
                {metrics.leads.slice(0, 3).map((lead) => {
                  const leadId = lead.id || lead.lead_id;
                  const isApproved = lead.status === 'APPROVED';
                  const isRejected = lead.status === 'REJECTED';
                  return (
                    <div key={leadId} className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                            lead.priority === 'HIGH'
                              ? 'bg-rose-950 text-rose-400 border border-rose-800'
                              : 'bg-amber-950 text-amber-400 border border-amber-800'
                          }`}>
                            {lead.priority || 'MEDIUM'} PRIORITY
                          </span>
                          <span className="text-slate-300 font-bold">{lead.title}</span>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded border ${
                          isApproved
                            ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                            : isRejected
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-slate-900 text-slate-400 border-slate-700'
                        }`}>
                          {lead.status || 'PENDING_REVIEW'}
                        </span>
                      </div>
                      <p className="text-slate-400 font-sans text-xs line-clamp-2">
                        {lead.summary}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Human Oversight & Case Selection */}
        <div className="space-y-6">
          {/* HUMAN OVERSIGHT PANEL */}
          <div className="bg-slate-900 border border-amber-500/30 rounded-xl p-5 shadow-md space-y-3">
            <div className="flex items-center justify-between text-amber-400 font-mono text-xs font-bold border-b border-slate-800 pb-2">
              <span className="flex items-center gap-1.5">
                <UserCheck className="w-4 h-4" />
                HUMAN OVERSIGHT
              </span>
              <span className="px-2 py-0.5 bg-amber-950 border border-amber-800/80 rounded text-[10px]">
                ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              ARGUS generates findings, correlates cross-evidence relationships, and produces candidate investigative leads with transparent reasoning factors. Final investigative decisions remain with the authorized human investigator.
            </p>
          </div>

          {/* OTHER CASES LIST */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-slate-200 flex items-center gap-2">
                <Folder className="w-4 h-4 text-cyan-400" />
                Other Cases ({otherCases.length})
              </h3>
              <span className="text-[10px] text-slate-500">Repository</span>
            </div>

            {otherCases.length === 0 ? (
              <div className="text-center py-4 text-slate-500 text-[11px]">
                No other cases in repository.
              </div>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {otherCases.map((c) => (
                  <button
                    type="button"
                    key={c.id}
                    onClick={() => onSelectCase && onSelectCase(c)}
                    className="w-full text-left bg-slate-950 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 p-2.5 rounded-lg cursor-pointer transition flex items-center justify-between group focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    <div>
                      <div className="font-bold text-cyan-400 text-xs group-hover:text-cyan-300">{c.case_number}</div>
                      <div className="text-slate-300 font-sans text-xs truncate max-w-[180px]">{c.title}</div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition-colors" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* =========================================================
          5. INITIALIZE NEW CASE MODAL
      ========================================================= */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 font-mono">
              <FolderPlus className="w-5 h-5 text-cyan-400" />
              Initialize Law Enforcement Case
            </h3>
            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-mono">Case Reference Number *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CASE-2026-CYGNUS"
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Case Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Operation Cygnus - Online Safety & Evidence Correlation"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-sans"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Investigation Objective / Description</label>
                <textarea
                  rows={3}
                  placeholder="Describe initial facts, suspect handles, target accounts, or investigation objectives..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-sans"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800 font-mono">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg text-slate-400 hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded-lg transition"
                >
                  {isCreating ? 'Creating...' : 'Initialize Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
