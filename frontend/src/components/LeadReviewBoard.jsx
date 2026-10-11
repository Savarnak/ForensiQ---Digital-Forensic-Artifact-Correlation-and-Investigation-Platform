import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, ShieldAlert, Sparkles, FileText, AlertOctagon, UserCheck } from 'lucide-react';
import { approveLead, rejectLead, requestAnalysisLead } from '../services/api';

export default function LeadReviewBoard({ leads, onLeadUpdated }) {
  const [reviewingId, setReviewingId] = useState(null);
  const [reviewerId, setReviewerId] = useState('OFFICER-4099');
  const [reviewNotes, setReviewNotes] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);

  if (!leads || leads.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-xs">
        8. Investigative Leads: No candidate leads generated yet. Run ARGUS Investigation to generate explainable candidate leads.
      </div>
    );
  }

  const handleAction = async (leadId, actionType) => {
    setReviewingId(leadId);
    setErrorMsg(null);
    try {
      let updated;
      if (actionType === 'APPROVE') {
        updated = await approveLead(leadId, reviewerId, reviewNotes || 'Approved by investigator after cross-referencing evidence.');
      } else if (actionType === 'REJECT') {
        updated = await rejectLead(leadId, reviewerId, reviewNotes || 'Rejected by investigator.');
      } else if (actionType === 'REQUEST_ANALYSIS') {
        updated = await requestAnalysisLead(leadId, reviewerId, reviewNotes || 'Requested further deep extraction and IP analysis.');
      }
      if (updated && onLeadUpdated) {
        onLeadUpdated(updated);
      }
      setReviewNotes('');
    } catch (err) {
      setErrorMsg(`Decision update failed: ${err.message}`);
    } finally {
      setReviewingId(null);
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'HIGH':
        return 'bg-rose-950/80 text-rose-300 border-rose-700/80';
      case 'MEDIUM':
        return 'bg-amber-950/80 text-amber-300 border-amber-700/80';
      case 'LOW':
        return 'bg-slate-800 text-slate-300 border-slate-700';
      default:
        return 'bg-cyan-950 text-cyan-300 border-cyan-700';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
      case 'INVESTIGATOR_APPROVED':
        return 'bg-emerald-950 text-emerald-400 border-emerald-700';
      case 'REJECTED':
      case 'INVESTIGATOR_REJECTED':
        return 'bg-rose-950 text-rose-400 border-rose-700';
      case 'NEEDS_MORE_ANALYSIS':
        return 'bg-purple-950 text-purple-300 border-purple-700';
      default:
        return 'bg-amber-950 text-amber-300 border-amber-700 animate-pulse';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-cyan-400" />
            8. Human-in-the-Loop Lead Review Board ({leads.length} Candidate Leads)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            ARGUS outputs explainable candidate leads. Consequential actions require explicit human officer approval.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg font-mono">
          <span className="text-slate-500">REVIEWER ID:</span>
          <input
            type="text"
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            className="bg-transparent text-cyan-400 font-bold w-28 focus:outline-none border-b border-slate-700 focus:border-cyan-400"
          />
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-950/80 border border-rose-800 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertOctagon className="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Lead Cards List */}
      <div className="space-y-6">
        {leads.map((lead) => {
          const leadId = lead.lead_id || lead.id;
          const priority = lead.priority || 'MEDIUM';
          const status = lead.status || 'PENDING_REVIEW';
          const factors = lead.reasoning_factors || lead.reasoning_chain || [];
          const evidenceList = lead.supporting_evidence || lead.supporting_evidence_ids || [];
          const isPending = status === 'PENDING_REVIEW' || status === 'PROPOSED';
          const isCurrentReviewing = reviewingId === leadId;

          return (
            <div
              key={leadId}
              className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4 hover:border-slate-700 transition"
            >
              {/* Header Badges & Title */}
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 border-b border-slate-900 pb-3">
                <div className="flex items-center space-x-3">
                  <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${getPriorityBadge(priority)}`}>
                    PRIORITY: {priority}
                  </span>
                  <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${getStatusBadge(status)}`}>
                    STATUS: {status}
                  </span>
                  <span className="text-xs font-mono text-slate-500">ID: {leadId}</span>
                </div>

                {/* Provenance Badge: AI vs Human */}
                <div className="text-[11px] font-mono">
                  {lead.reviewed_at ? (
                    <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-semibold">
                      HUMAN DECISION BY {lead.reviewed_by || reviewerId}
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800">
                      AI GENERATED RECOMMENDATION
                    </span>
                  )}
                </div>
              </div>

              {/* Title & Summary */}
              <div>
                <h3 className="text-base font-bold text-slate-100">{lead.title}</h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">{lead.summary}</p>
              </div>

              {/* Transparent Reasoning Factors (NO Opaque AI claims) */}
              <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                  Transparent Explainable Reasoning Factors ({factors.length})
                </h4>
                <ul className="list-disc list-inside text-xs text-slate-300 space-y-1 font-mono">
                  {factors.map((factor, fIdx) => (
                    <li key={fIdx} className="leading-tight">
                      {typeof factor === 'string' ? factor : JSON.stringify(factor)}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Supporting Evidence Citations */}
              {evidenceList.length > 0 && (
                <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-cyan-400" />
                  <span>SUPPORTING EVIDENCE ARTIFACTS:</span>
                  <span className="text-emerald-400 font-bold">
                    {evidenceList.map((e) => (typeof e === 'object' ? e.file_name || e.id : e)).join(', ')}
                  </span>
                </div>
              )}

              {/* Legal Non-Guilt Disclaimer */}
              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-900 text-[11px] text-slate-500 font-mono italic">
                {lead.disclaimer || 'Investigative aid provided for officer/analyst review. Does not constitute a determination of guilt or administrative finding.'}
              </div>

              {/* Human Review Decision Buttons */}
              <div className="pt-3 border-t border-slate-900 space-y-3">
                <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
                  <textarea
                    rows={2}
                    placeholder="Enter optional investigator review rationale/notes..."
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono resize-none"
                  />

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleAction(leadId, 'APPROVE')}
                      disabled={isCurrentReviewing}
                      className="flex-1 md:flex-none flex items-center justify-center space-x-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold rounded-lg text-xs transition"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Approve Lead</span>
                    </button>

                    <button
                      onClick={() => handleAction(leadId, 'REQUEST_ANALYSIS')}
                      disabled={isCurrentReviewing}
                      className="flex-1 md:flex-none flex items-center justify-center space-x-1.5 px-3.5 py-1.5 bg-purple-600 hover:bg-purple-500 text-slate-950 font-bold rounded-lg text-xs transition"
                    >
                      <HelpCircle className="w-4 h-4" />
                      <span>Request Analysis</span>
                    </button>

                    <button
                      onClick={() => handleAction(leadId, 'REJECT')}
                      disabled={isCurrentReviewing}
                      className="flex-1 md:flex-none flex items-center justify-center space-x-1.5 px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-slate-950 font-bold rounded-lg text-xs transition"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Reject Lead</span>
                    </button>
                  </div>
                </div>

                {lead.reviewer_notes && (
                  <div className="text-[11px] font-mono text-slate-400 bg-slate-900 p-2 rounded border border-slate-800">
                    <span className="text-cyan-400 font-bold">Investigator Notes ({lead.reviewed_by}):</span> {lead.reviewer_notes}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
