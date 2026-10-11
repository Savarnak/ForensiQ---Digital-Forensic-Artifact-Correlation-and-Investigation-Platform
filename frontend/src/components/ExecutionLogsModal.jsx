import React from 'react';
import { Terminal, X } from 'lucide-react';

export default function ExecutionLogsModal({ logs, onClose }) {
  if (!logs) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-2xl w-full shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center space-x-2 font-mono">
            <Terminal className="w-5 h-5 text-cyan-400" />
            <span>LangGraph Brain Execution Logs</span>
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-lg text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-slate-300 max-h-[350px] overflow-y-auto space-y-1.5">
          {logs.map((log, idx) => (
            <div key={idx} className="flex items-start space-x-2">
              <span className="text-cyan-500 font-bold shrink-0">&gt;</span>
              <span>{log}</span>
            </div>
          ))}
        </div>

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg text-xs transition"
          >
            Close Logs
          </button>
        </div>
      </div>
    </div>
  );
}
