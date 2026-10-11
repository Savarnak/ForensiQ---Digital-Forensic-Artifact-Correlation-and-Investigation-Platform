import React from 'react';
import { ShieldCheck, User, Cpu, Clock, Lock } from 'lucide-react';

export default function AuditTrailView({ auditEvents: propEvents, orchestratorResults }) {
  const auditEvents = (propEvents && Array.isArray(propEvents) && propEvents.length > 0)
    ? propEvents
    : (orchestratorResults?.audit_events || []);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Lock className="w-5 h-5 text-cyan-400" />
            10. Immutable Audit Trail ({auditEvents.length} Events)
          </h2>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Tamper-evident audit log recording every system action, LangGraph node execution, and human officer review decision.
          </p>
        </div>
      </div>

      {auditEvents.length === 0 ? (
        <div className="text-center py-8 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
          No audit events recorded yet. Run ARGUS Investigation or approve/reject leads to record audit log entries.
        </div>
      ) : (
        <div className="space-y-2">
          {auditEvents.map((evt, idx) => (
            <div key={idx} className="bg-slate-950 border border-slate-800 p-3 rounded-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  {evt.actor?.includes('OFFICER') ? (
                    <User className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Cpu className="w-4 h-4 text-cyan-400" />
                  )}
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-cyan-300">{evt.event_type}</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-slate-400">Actor: {evt.actor}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans mt-0.5 max-w-xl">
                    {evt.details?.summary || evt.details?.reason || JSON.stringify(evt.details)}
                  </p>
                </div>
              </div>

              <div className="text-right text-[10px] text-slate-500 shrink-0">
                <span className="bg-slate-900 border border-slate-800 px-2 py-1 rounded">
                  Immutable Record #AUDIT-{idx + 101}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
