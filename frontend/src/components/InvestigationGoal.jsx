import React, { useState } from 'react';
import { Target, Play, CheckCircle2, Sparkles } from 'lucide-react';
import { saveGoal } from '../services/api';

export default function InvestigationGoal({ activeCase, onRunOrchestrator, isOrchestrating }) {
  const [goalText, setGoalText] = useState(
    activeCase?.description ||
    "Identify relevant relationships between accounts, devices, locations and events and highlight evidence requiring investigator review."
  );
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  if (!activeCase) return null;

  const handleSaveGoal = async () => {
    setIsSaving(true);
    try {
      await saveGoal(activeCase.id, goalText);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert(`Failed to save goal: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-4">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Target className="w-5 h-5 text-cyan-400" />
            3. Investigation Goal & Orchestration Trigger
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Formulate the goal-driven objective for the ARGUS LangGraph multi-agent orchestration brain.
          </p>
        </div>

        <button
          onClick={onRunOrchestrator}
          disabled={isOrchestrating}
          className="flex items-center space-x-2 text-xs font-extrabold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 px-5 py-2.5 rounded-lg shadow-lg shadow-cyan-500/20 transition disabled:opacity-50"
        >
          <Play className={`w-4 h-4 text-slate-950 ${isOrchestrating ? 'animate-spin' : ''}`} />
          <span>{isOrchestrating ? 'RUNNING ARGUS BRAIN...' : 'RUN ARGUS INVESTIGATION'}</span>
        </button>
      </div>

      <div className="space-y-3">
        <label className="block text-xs font-mono font-semibold text-slate-300">
          Target Objective Prompt (Goal-Driven Planner Guidance):
        </label>
        <textarea
          rows={3}
          value={goalText}
          onChange={(e) => setGoalText(e.target.value)}
          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-100 font-sans focus:outline-none focus:border-cyan-500 leading-relaxed"
        />

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={handleSaveGoal}
              disabled={isSaving}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-md transition font-mono"
            >
              {isSaving ? 'Saving Goal...' : 'Update Goal'}
            </button>
            {saveSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" /> Goal Saved
              </span>
            )}
          </div>

          <div className="text-[11px] text-slate-500 font-mono">
            Autonomous execution strictly constrained to registered capabilities (`TextEntityExtractor`, `OCRTool`, `MetadataExtractor`, `EvidenceSearchTool`, `TimelineExtractor`).
          </div>
        </div>
      </div>
    </div>
  );
}
