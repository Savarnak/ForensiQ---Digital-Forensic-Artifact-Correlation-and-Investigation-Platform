import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import CaseDashboard from './components/CaseDashboard';
import EvidenceWorkspace from './components/EvidenceWorkspace';
import InvestigationGoal from './components/InvestigationGoal';
import AgentActivity from './components/AgentActivity';
import FindingsViewer from './components/FindingsViewer';
import KnowledgeGraphView from './components/KnowledgeGraphView';
import TimelineView from './components/TimelineView';
import LeadReviewBoard from './components/LeadReviewBoard';
import GapContradictionPanel from './components/GapContradictionPanel';
import AuditTrailView from './components/AuditTrailView';
import ExecutionLogsModal from './components/ExecutionLogsModal';

import {
  fetchHealth,
  fetchCases,
  fetchEvidence,
  runOrchestrator,
  fetchOrchestratorResults,
  fetchAuditEvents,
  fetchLeads
} from './services/api';

const VALID_TABS = [
  'dashboard',
  'evidence',
  'goal',
  'agent',
  'findings',
  'graph',
  'timeline',
  'leads',
  'gaps',
  'audit'
];

export default function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [cases, setCases] = useState([]);
  const [activeCase, setActiveCase] = useState(null);
  const [evidenceList, setEvidenceList] = useState([]);
  const [orchestratorResults, setOrchestratorResults] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [leads, setLeads] = useState([]);
  const [isOrchestrating, setIsOrchestrating] = useState(false);

  // Remember the last opened tab after refresh if valid
  const [activeTab, setActiveTab] = useState(() => {
    const savedTab = localStorage.getItem('activeTab');
    return savedTab && VALID_TABS.includes(savedTab) ? savedTab : 'dashboard';
  });

  const [showLogsModal, setShowLogsModal] = useState(false);

  /*
   * ---------------------------------------------------------
   * INITIAL APPLICATION LOAD
   * ---------------------------------------------------------
   */
  useEffect(() => {
    loadInitialData();
  }, []);

  /*
   * ---------------------------------------------------------
   * LOAD CASE DATA WHEN ACTIVE CASE CHANGES
   * ---------------------------------------------------------
   */
  useEffect(() => {
    if (activeCase) {
      loadCaseData(activeCase.id);
    }
  }, [activeCase]);

  /*
   * ---------------------------------------------------------
   * SAVE ACTIVE TAB
   * ---------------------------------------------------------
   */
  useEffect(() => {
    if (activeTab && VALID_TABS.includes(activeTab)) {
      localStorage.setItem('activeTab', activeTab);
    }
  }, [activeTab]);

  /*
   * ---------------------------------------------------------
   * INITIAL DATA
   *
   * IMPORTANT:
   * We first check localStorage for the previously selected
   * case instead of blindly selecting caseList[0].
   * ---------------------------------------------------------
   */
  const loadInitialData = async () => {
    try {
      const health = await fetchHealth();
      setSystemStatus(health);

      const caseList = await fetchCases();
      setCases(caseList);

      if (caseList.length > 0) {
        const savedCaseId = localStorage.getItem('activeCaseId');

        const savedCase = savedCaseId
          ? caseList.find((c) => c.id === savedCaseId)
          : null;

        if (savedCase) {
          // Restore previously selected case
          setActiveCase(savedCase);
        } else {
          // If saved case doesn't exist, use first available case
          setActiveCase(caseList[0]);
          localStorage.setItem('activeCaseId', caseList[0].id);
        }
      }
    } catch (err) {
      console.error('Error fetching initial data:', err);
    }
  };

  /*
   * ---------------------------------------------------------
   * LOAD ALL DATA FOR ACTIVE CASE
   * ---------------------------------------------------------
   */
  const loadCaseData = async (caseId) => {
    // Clear old case data immediately to prevent stale data
    // from appearing while the new case is loading.
    setOrchestratorResults(null);
    setAuditEvents([]);
    setEvidenceList([]);
    setLeads([]);

    try {
      // Evidence
      const evs = await fetchEvidence(caseId);
      setEvidenceList(evs);

      // Leads
      const lds = await fetchLeads(caseId);
      setLeads(lds);

      // Orchestrator results
      const orchRes = await fetchOrchestratorResults(caseId);
      setOrchestratorResults(orchRes);

      // Audit events
      const audits = await fetchAuditEvents(caseId);
      setAuditEvents(audits);
    } catch (err) {
      console.error('Error loading case data:', err);
    }
  };

  /*
   * ---------------------------------------------------------
   * CASE SELECTION
   *
   * Save selected case ID in localStorage so refresh doesn't
   * send the user back to caseList[0].
   * ---------------------------------------------------------
   */
  const handleCaseSelect = (selectedCase) => {
    if (!selectedCase) return;

    let targetCase = selectedCase;
    if (typeof selectedCase === 'string') {
      targetCase = cases.find((c) => c.id === selectedCase || c.case_number === selectedCase) || { id: selectedCase };
    }

    setActiveCase(targetCase);
    localStorage.setItem('activeCaseId', targetCase.id);
    if (targetCase.id) {
      loadCaseData(targetCase.id);
    }
  };

  /*
   * ---------------------------------------------------------
   * NEW CASE CREATED
   * ---------------------------------------------------------
   */
  const handleCaseCreated = (newCase) => {
    if (!newCase) return;

    setCases((prevCases) => {
      const exists = prevCases.some((c) => c.id === newCase.id);

      if (exists) {
        return prevCases.map((c) =>
          c.id === newCase.id ? newCase : c
        );
      }

      return [newCase, ...prevCases];
    });

    // Make new case active
    setActiveCase(newCase);

    // Remember it
    localStorage.setItem('activeCaseId', newCase.id);
  };

  /*
   * ---------------------------------------------------------
   * EVIDENCE UPLOADED
   * ---------------------------------------------------------
   */
  const handleEvidenceUploaded = (newEv) => {
    if (!newEv) return;

    setEvidenceList((prevEvidence) => [
      newEv,
      ...prevEvidence
    ]);
  };

  /*
   * ---------------------------------------------------------
   * RUN ORCHESTRATOR
   * ---------------------------------------------------------
   */
  const handleRunOrchestrator = async () => {
    if (!activeCase) return;

    setIsOrchestrating(true);

    try {
      const result = await runOrchestrator(activeCase.id);

      setOrchestratorResults(result);

      if (result.leads) {
        setLeads(result.leads);
      }

      // Refresh audit events after investigation run
      const audits = await fetchAuditEvents(activeCase.id);
      setAuditEvents(audits);

      // Go to leads after investigation
      setActiveTab('leads');
    } catch (err) {
      console.error('Orchestrator failed:', err);
      alert(`Orchestrator failed: ${err.message}`);
    } finally {
      setIsOrchestrating(false);
    }
  };

  /*
   * ---------------------------------------------------------
   * LEAD UPDATED
   *
   * Used after approve / reject / request-analysis.
   * ---------------------------------------------------------
   */
  const handleLeadUpdated = async (updatedLead) => {
    if (!updatedLead) return;

    const leadId = updatedLead.id || updatedLead.lead_id;

    setLeads((prevLeads) =>
      prevLeads.map((l) =>
        (l.id || l.lead_id) === leadId
          ? updatedLead
          : l
      )
    );

    if (activeCase) {
      try {
        // Refresh audit trail after human review decision
        const audits = await fetchAuditEvents(activeCase.id);
        setAuditEvents(audits);

        // Also refresh leads from backend
        const updatedLeads = await fetchLeads(activeCase.id);
        setLeads(updatedLeads);
      } catch (err) {
        console.error(
          'Error refreshing audit events after lead update:',
          err
        );
      }
    }
  };

  /*
   * ---------------------------------------------------------
   * RENDER
   * ---------------------------------------------------------
   */
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-cyan-500 selection:text-slate-950">

      <Header
        systemStatus={systemStatus}
        activeCase={activeCase}
      />

      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6 space-y-6">

        {/* =====================================================
            NAVIGATION TABS
        ====================================================== */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-2 flex overflow-x-auto gap-2 text-xs font-mono font-semibold scrollbar-none shadow-md">

          {/* 1. CASE DASHBOARD */}
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap ${activeTab === 'dashboard'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            1. Case Dashboard
          </button>

          {/* 2. EVIDENCE */}
          <button
            onClick={() => setActiveTab('evidence')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap flex items-center gap-1.5 ${activeTab === 'evidence'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            <span>2. Evidence</span>

            {evidenceList.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-950 text-cyan-300">
                {evidenceList.length}
              </span>
            )}
          </button>

          {/* 3. GOAL GUIDANCE */}
          <button
            onClick={() => setActiveTab('goal')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap ${activeTab === 'goal'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            3. Goal Guidance
          </button>

          {/* 4. AGENT RUN */}
          <button
            onClick={() => setActiveTab('agent')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap flex items-center gap-1.5 ${activeTab === 'agent'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            <span>4. Agent Run</span>

            {isOrchestrating && (
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            )}
          </button>

          {/* 5. FINDINGS */}
          <button
            onClick={() => setActiveTab('findings')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap ${activeTab === 'findings'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            5. Findings
          </button>

          {/* 6. GRAPH */}
          <button
            onClick={() => setActiveTab('graph')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap ${activeTab === 'graph'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            6. Graph
          </button>

          {/* 7. TIMELINE */}
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap ${activeTab === 'timeline'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            7. Timeline
          </button>

          {/* 8. LEADS */}
          <button
            onClick={() => setActiveTab('leads')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap flex items-center gap-1.5 ${activeTab === 'leads'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            <span>8. Leads</span>

            {leads.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-950 text-cyan-300">
                {leads.length}
              </span>
            )}
          </button>

          {/* 9. GAPS & CONFLICTS */}
          <button
            onClick={() => setActiveTab('gaps')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap ${activeTab === 'gaps'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            9. Gaps & Conflicts
          </button>

          {/* 10. AUDIT TRAIL */}
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-4 py-2.5 rounded-lg transition whitespace-nowrap ${activeTab === 'audit'
                ? 'bg-cyan-600 text-slate-950 shadow-cyan-600/20 shadow-sm font-extrabold'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
          >
            10. Audit Trail
          </button>

        </div>

        {/* =====================================================
            TAB VIEWS
        ====================================================== */}

        {/* 1. CASE DASHBOARD */}
        {activeTab === 'dashboard' && (
          <CaseDashboard
            cases={cases}
            activeCase={activeCase}
            onSelectCase={handleCaseSelect}
            onCaseCreated={handleCaseCreated}
          />
        )}

        {/* 2. EVIDENCE */}
        {activeTab === 'evidence' && (
          <EvidenceWorkspace
            activeCase={activeCase}
            evidenceList={evidenceList}
            onEvidenceUploaded={handleEvidenceUploaded}
          />
        )}

        {/* 3. GOAL GUIDANCE */}
        {activeTab === 'goal' && (
          <InvestigationGoal
            activeCase={activeCase}
            onRunOrchestrator={handleRunOrchestrator}
            isOrchestrating={isOrchestrating}
          />
        )}

        {/* 4. AGENT RUN */}
        {activeTab === 'agent' && (
          <AgentActivity
            isOrchestrating={isOrchestrating}
            orchestratorResults={orchestratorResults}
            onOpenLogsModal={() => setShowLogsModal(true)}
          />
        )}

        {/* 5. FINDINGS */}
        {activeTab === 'findings' && (
          <FindingsViewer
            orchestratorResults={orchestratorResults}
          />
        )}

        {/* 6. GRAPH */}
        {activeTab === 'graph' && (
          <KnowledgeGraphView
            orchestratorResults={orchestratorResults}
          />
        )}

        {/* 7. TIMELINE */}
        {activeTab === 'timeline' && (
          <TimelineView
            activeCase={activeCase}
            orchestratorResults={orchestratorResults}
          />
        )}

        {/* 8. LEADS */}
        {activeTab === 'leads' && (
          <LeadReviewBoard
            leads={leads}
            onLeadUpdated={handleLeadUpdated}
          />
        )}

        {/* 9. GAPS & CONFLICTS */}
        {activeTab === 'gaps' && (
          <GapContradictionPanel
            activeCase={activeCase}
            orchestratorResults={orchestratorResults}
          />
        )}

        {/* 10. AUDIT TRAIL */}
        {activeTab === 'audit' && (
          <AuditTrailView
            auditEvents={auditEvents}
            orchestratorResults={orchestratorResults}
          />
        )}

      </main>

      {/* =====================================================
          BRAIN EXECUTION LOGS MODAL
      ====================================================== */}
      {showLogsModal && orchestratorResults && (
        <ExecutionLogsModal
          logs={orchestratorResults.execution_logs}
          onClose={() => setShowLogsModal(false)}
        />
      )}

    </div>
  );
}