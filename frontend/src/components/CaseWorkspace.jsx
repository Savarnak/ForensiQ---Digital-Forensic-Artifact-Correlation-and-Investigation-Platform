import React, { useState } from 'react';
import { FolderPlus, Target, FileText, CheckCircle2 } from 'lucide-react';
import { createCase } from '../services/api';

export default function CaseWorkspace({ cases, activeCase, onSelectCase, onCaseCreated }) {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    case_number: `CASE-2026-${Math.floor(1000 + Math.random() * 9000)}`,
    title: '',
    description: '',
    investigation_goal: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const created = await createCase(formData);
      onCaseCreated(created);
      setShowModal(false);
      setFormData({
        case_number: `CASE-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        title: '',
        description: '',
        investigation_goal: ''
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <FolderPlus className="w-4 h-4 text-cyan-400" />
          <span>Investigation Cases</span>
        </h2>
        <button
          onClick={() => setShowModal(true)}
          className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-semibold px-3 py-1.5 rounded-lg text-xs transition shadow-md flex items-center space-x-1"
        >
          <span>+ New Case</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {cases.length === 0 ? (
          <div className="col-span-3 text-center py-6 text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
            No cases created yet. Click "+ New Case" to get started.
          </div>
        ) : (
          cases.map((c) => {
            const isSelected = activeCase?.id === c.id;
            return (
              <div
                key={c.id}
                onClick={() => onSelectCase(c)}
                className={`p-3.5 rounded-lg border transition cursor-pointer relative ${
                  isSelected
                    ? 'bg-slate-850 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <span className="text-xs font-mono font-bold text-cyan-400">{c.case_number}</span>
                  {isSelected && <CheckCircle2 className="w-4 h-4 text-cyan-400" />}
                </div>
                <h3 className="text-sm font-semibold text-slate-100 mt-1 line-clamp-1">{c.title}</h3>
                <div className="mt-2 flex items-center text-xs text-slate-400 space-x-1">
                  <Target className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span className="truncate">{c.investigation_goal}</span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
              <FolderPlus className="w-5 h-5 text-cyan-400" />
              <span>Create New Investigation Case</span>
            </h3>

            {error && (
              <div className="mb-4 bg-red-500/10 border border-red-500/30 text-red-400 text-xs p-3 rounded-lg">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 mb-1 font-medium">Case Reference Number</label>
                <input
                  type="text"
                  required
                  value={formData.case_number}
                  onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">Case Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Operation Cygnus - Online Grooming Investigation"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">Investigation Goal</label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Identify primary suspect handles, cross-reference geotags, and reconstruct timeline of coordinated activity."
                  value={formData.investigation_goal}
                  onChange={(e) => setFormData({ ...formData, investigation_goal: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-lg transition"
                >
                  {loading ? 'Creating...' : 'Create Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
