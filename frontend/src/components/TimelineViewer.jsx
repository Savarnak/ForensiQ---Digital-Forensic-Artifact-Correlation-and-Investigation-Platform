import React from 'react';
import { Clock, MapPin, MessageSquare, FileText } from 'lucide-react';

export default function TimelineViewer({ timelineEvents }) {
  if (!timelineEvents || timelineEvents.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
        <Clock className="w-8 h-8 text-slate-700 mx-auto mb-2" />
        No timeline events reconstructed yet. Execute the ARGUS Orchestrator to generate chronological event swimlanes.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Reconstructed Timeline Swimlanes</span>
          </h2>
          <p className="text-xs text-slate-400">Chronological sequencing across multi-modal evidence sources</p>
        </div>
        <span className="text-xs bg-slate-950 px-2.5 py-1 rounded border border-slate-800 text-slate-300 font-mono">
          {timelineEvents.length} Timed Events
        </span>
      </div>

      <div className="relative border-l-2 border-slate-800 ml-4 pl-6 space-y-4 py-2">
        {timelineEvents.map((evt, idx) => (
          <div key={idx} className="relative group">
            {/* Timeline dot */}
            <div className="absolute -left-[31px] top-1.5 w-3 h-3 rounded-full bg-cyan-500 border-2 border-slate-900 group-hover:scale-125 transition" />

            <div className="bg-slate-950 border border-slate-850 hover:border-cyan-500/40 transition rounded-lg p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-cyan-400">{evt.timestamp}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 font-mono">
                  {evt.source_evidence || 'Evidence File'}
                </span>
              </div>
              <h4 className="text-xs font-semibold text-slate-100">{evt.title}</h4>
              <p className="text-xs text-slate-300">{evt.description}</p>
              {evt.location && (
                <div className="flex items-center space-x-1 text-[11px] text-emerald-400 pt-1">
                  <MapPin className="w-3 h-3" />
                  <span>{evt.location}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
