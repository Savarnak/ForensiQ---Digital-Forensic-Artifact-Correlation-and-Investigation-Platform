import React, { useState } from 'react';
import { Search, Filter, FileText, CheckCircle, Database, Tag } from 'lucide-react';

export default function FindingsViewer({ orchestratorResults }) {
  const [filterTool, setFilterTool] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const rawFindings = orchestratorResults?.findings?.raw || [];
  const standardizedFindings = orchestratorResults?.findings?.standardized || [];

  if (rawFindings.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-xs">
        5. Findings Workspace: No findings generated yet. Run ARGUS Investigation to extract standardized findings from evidence files.
      </div>
    );
  }

  // Filter tools
  const tools = ['ALL', ...new Set(rawFindings.map((f) => f.tool_name).filter(Boolean))];

  const filteredFindings = rawFindings.filter((f) => {
    const matchesTool = filterTool === 'ALL' || f.tool_name === filterTool;
    const matchesSearch =
      !searchQuery ||
      JSON.stringify(f).toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTool && matchesSearch;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            5. Standardized Evidence Findings ({filteredFindings.length} Items)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Standardized findings extracted across registered investigative tools. Every finding contains source evidence provenance.
          </p>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-48">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search findings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <select
            value={filterTool}
            onChange={(e) => setFilterTool(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none font-mono"
          >
            {tools.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-3 font-mono text-xs">
        {filteredFindings.map((finding, idx) => {
          const provenance = finding.provenance || {};
          const sourceEv = provenance.source_evidence || finding.evidence_id || 'Unknown Evidence Source';
          const content = finding.content || {};

          return (
            <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 hover:border-slate-700 transition">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
                    {finding.tool_name}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-slate-300 border border-slate-800">
                    TYPE: {finding.finding_type}
                  </span>
                </div>

                {/* Clear Source Evidence Citation Badge */}
                <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700/80 px-2.5 py-1 rounded-md text-[11px] text-cyan-300">
                  <Tag className="w-3 h-3 text-cyan-400" />
                  <span>SOURCE EVIDENCE:</span>
                  <span className="font-bold text-emerald-400">{sourceEv}</span>
                </div>
              </div>

              {/* Finding Details */}
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 text-[11px] text-slate-300 leading-relaxed font-sans">
                <pre className="whitespace-pre-wrap font-mono text-slate-300 text-[11px]">
                  {JSON.stringify(content, null, 2)}
                </pre>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-500">
                <span>Confidence: <strong className="text-emerald-400">{((finding.confidence || 0.95) * 100).toFixed(0)}%</strong></span>
                <span>Task ID: {provenance.task_id || 'N/A'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
