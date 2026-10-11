import React, { useState, useEffect } from 'react';
import { Calendar, Clock, AlertTriangle, CheckCircle, Info, MapPin, Tag } from 'lucide-react';
import { fetchTimeline } from '../services/api';

export default function TimelineView({ activeCase, orchestratorResults }) {
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeCase) {
      loadTimeline();
    }
  }, [activeCase, orchestratorResults]);

  const loadTimeline = async () => {
    setLoading(true);
    try {
      const data = await fetchTimeline(activeCase.id);
      setTimelineData(data);
    } catch (err) {
      console.error('Error loading timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  const timelineEvents = timelineData?.timeline || orchestratorResults?.correlations?.timeline_events || [];
  const overlaps = timelineData?.temporal_overlaps || [];
  const gaps = timelineData?.suspicious_gaps || [];
  const conflicts = timelineData?.conflicting_timestamps || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-cyan-400" />
            7. Reconstructed Investigation Timeline ({timelineEvents.length} Events)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Chronological event timeline merged from chats, calls, telematics GPS logs, images, and reports with event explanations.
          </p>
        </div>

        <button
          onClick={loadTimeline}
          disabled={loading}
          className="text-xs font-mono bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 px-3 py-1.5 rounded-lg transition"
        >
          {loading ? 'Refreshing...' : 'Refresh Timeline Engine'}
        </button>
      </div>

      {/* Temporal Anomalies Alert Panel */}
      {(overlaps.length > 0 || gaps.length > 0 || conflicts.length > 0) && (
        <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-4 space-y-3 font-mono text-xs">
          <h3 className="font-bold text-amber-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Temporal Anomalies & Integrity Warnings Detected
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="bg-slate-950/80 p-3 rounded-lg border border-amber-900/60">
              <span className="text-amber-400 font-bold block mb-1">Temporal Overlaps ({overlaps.length})</span>
              <p className="text-[11px] text-slate-400">Events occurring within 60 seconds across distinct evidence sources.</p>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-lg border border-amber-900/60">
              <span className="text-amber-400 font-bold block mb-1">Suspicious Gaps ({gaps.length})</span>
              <p className="text-[11px] text-slate-400">Operational inactivity gaps exceeding 10 minutes during active timelines.</p>
            </div>

            <div className="bg-slate-950/80 p-3 rounded-lg border border-amber-900/60">
              <span className="text-amber-400 font-bold block mb-1">Conflicting Timestamps ({conflicts.length})</span>
              <p className="text-[11px] text-slate-400">Events within 5 minutes reporting physically conflicting locations.</p>
            </div>
          </div>
        </div>
      )}

      {/* Timeline Stream */}
      {timelineEvents.length === 0 ? (
        <div className="text-center py-8 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
          No timeline events generated yet. Run ARGUS Investigation to reconstruct the chronological event sequence.
        </div>
      ) : (
        <div className="relative border-l-2 border-slate-800 ml-4 space-y-6 font-mono text-xs">
          {timelineEvents.map((evt, idx) => (
            <div key={idx} className="relative pl-6 space-y-2 group">
              {/* Event Marker */}
              <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-slate-900 border-2 border-cyan-400 group-hover:bg-cyan-400 transition" />

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2 hover:border-slate-700 transition">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-2 border-b border-slate-900 pb-2">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="font-bold text-cyan-300">{evt.timestamp}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-slate-400 border border-slate-800">
                      {evt.event_type || 'EVENT'}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                    <Tag className="w-3 h-3 text-cyan-400" />
                    <span>SOURCE: <strong className="text-emerald-400">{evt.source_evidence || 'Evidence File'}</strong></span>
                  </div>
                </div>

                <h4 className="font-bold text-slate-200 font-sans text-sm">{evt.description || evt.title}</h4>

                {/* Event Explanation */}
                {evt.explanation && (
                  <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-400 font-sans flex items-start gap-2">
                    <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-cyan-300 font-mono text-[10px] block uppercase">Rationale & Extraction Explanation:</strong>
                      <span>{evt.explanation}</span>
                    </div>
                  </div>
                )}

                {evt.location && (
                  <div className="flex items-center space-x-1 text-[11px] text-rose-400 font-mono pt-1">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>Location: {evt.location}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
