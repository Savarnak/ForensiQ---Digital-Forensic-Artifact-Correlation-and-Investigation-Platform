import React from 'react';
import { Cpu, CheckCircle2, Clock, Terminal, ShieldAlert, ArrowRight } from 'lucide-react';

export default function AgentActivity({ isOrchestrating, orchestratorResults, onOpenLogsModal }) {
  if (!isOrchestrating && !orchestratorResults) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md text-center text-slate-500 text-xs">
        4. Agent Activity & Investigation Run: Ready. Click 'RUN ARGUS INVESTIGATION' above to trigger the LangGraph orchestration brain.
      </div>
    );
  }

  const tasks = orchestratorResults?.tasks || [];
  const logs = orchestratorResults?.execution_logs || [];
  const runInfo = orchestratorResults?.investigation_run || {};

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Cpu className={`w-5 h-5 ${isOrchestrating ? 'text-cyan-400 animate-spin' : 'text-emerald-400'}`} />
            4. Agent Activity / Live Investigation Run Progress
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time execution of LangGraph state machine nodes and registered tool capability execution.
          </p>
        </div>

        {logs.length > 0 && (
          <button
            onClick={onOpenLogsModal}
            className="flex items-center space-x-1.5 text-xs font-mono bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 px-3 py-1.5 rounded-lg transition"
          >
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span>View Full Execution Trace ({logs.length})</span>
          </button>
        )}
      </div>

      {/* Progress Status Banner */}
      {isOrchestrating ? (
        <div className="bg-cyan-950/40 border border-cyan-800/60 rounded-xl p-4 flex items-center space-x-4">
          <div className="w-4 h-4 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
          <div>
            <h4 className="text-xs font-bold font-mono text-cyan-300">ARGUS BRAIN PIPELINE RUNNING</h4>
            <p className="text-[11px] text-cyan-400/80">
              Understanding goal ➔ Inspecting evidence ➔ Planning tasks ➔ Executing tools ➔ Evaluating findings...
            </p>
          </div>
        </div>
      ) : (
        runInfo.status && (
          <div className="bg-emerald-950/40 border border-emerald-800/60 rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <h4 className="text-xs font-bold font-mono text-emerald-300">INVESTIGATION RUN COMPLETED</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">{runInfo.summary}</p>
              </div>
            </div>
            <div className="text-right text-[11px] font-mono text-slate-500">
              Run ID: <span className="text-slate-300">{runInfo.id?.slice(0, 8)}</span>
            </div>
          </div>
        )
      )}

      {/* Real Task Execution Cards */}
      {tasks.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
            Decomposed Investigation Tasks & Executed Capabilities ({tasks.length})
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
            {tasks.map((t, idx) => (
              <div key={idx} className="bg-slate-950 border border-slate-800 p-3 rounded-lg space-y-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-bold text-cyan-400">{t.tool_name}</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800">
                    {t.status || 'COMPLETED'}
                  </span>
                </div>

                <p className="text-slate-300 font-sans text-[11px] line-clamp-2">{t.objective}</p>

                {t.result && (
                  <div className="pt-2 border-t border-slate-900 text-[10px] text-slate-500 flex justify-between">
                    <span>Findings: <strong className="text-slate-300">{t.result.findings_extracted ?? 0}</strong></span>
                    <span>Time: <strong className="text-slate-300">{t.result.execution_time_ms ? `${t.result.execution_time_ms.toFixed(1)}ms` : 'N/A'}</strong></span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
