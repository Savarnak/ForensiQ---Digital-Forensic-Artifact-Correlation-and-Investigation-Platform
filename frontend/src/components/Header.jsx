import React from 'react';
import { Shield, Cpu, Activity, UserCheck, AlertTriangle } from 'lucide-react';

export default function Header({ systemStatus, activeCase }) {
  const isHealthy = systemStatus?.status === 'ok';

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-40 shadow-lg">
      {/* Brand & System Title */}
      <div className="flex items-center space-x-4">
        <div className="bg-gradient-to-br from-cyan-500 to-blue-700 p-2.5 rounded-lg text-slate-950 font-bold flex items-center justify-center shadow-cyan-500/20 shadow-md">
          <Shield className="w-6 h-6 text-slate-950" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-extrabold tracking-tight text-slate-100 uppercase">
              ARGUS <span className="text-cyan-400 font-medium text-xs tracking-wider border border-cyan-500/30 bg-cyan-950/60 px-2 py-0.5 rounded ml-2">V2.4 INTEL</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400 font-mono tracking-wide">
            Agentic Cyber Investigation Backbone • Law Enforcement Decision Support System
          </p>
        </div>
      </div>

      {/* Center Active Case Badge */}
      {activeCase && (
        <div className="hidden md:flex items-center space-x-3 bg-slate-950/80 border border-slate-800 px-4 py-2 rounded-lg">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <div className="text-xs">
            <span className="text-slate-400 font-mono">ACTIVE CASE:</span>{' '}
            <span className="font-mono text-cyan-300 font-bold">{activeCase.case_number}</span>
          </div>
          <span className="text-xs text-slate-500">|</span>
          <div className="text-xs text-slate-300 font-medium max-w-xs truncate">
            {activeCase.title}
          </div>
        </div>
      )}

      {/* System Status & Investigator Badge */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-xs bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-md">
          <Activity className={`w-3.5 h-3.5 ${isHealthy ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span className="text-slate-400 font-mono">SYSTEM:</span>
          <span className={`font-mono font-semibold ${isHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isHealthy ? 'OPERATIONAL' : 'DEGRADED'}
          </span>
        </div>

        <div className="flex items-center space-x-2 text-xs bg-slate-800/80 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-md font-mono">
          <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>INV-4099</span>
        </div>
      </div>
    </header>
  );
}
