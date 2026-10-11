import React, { useState } from 'react';
import { Network, User, Smartphone, MapPin, FileCode, ArrowRight } from 'lucide-react';

export default function KnowledgeGraph({ graphData }) {
  const [selectedNode, setSelectedNode] = useState(null);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
        <Network className="w-8 h-8 text-slate-700 mx-auto mb-2" />
        Knowledge graph empty. Run the ARGUS Orchestrator to generate cross-evidence entity resolution graph.
      </div>
    );
  }

  const getNodeIcon = (type) => {
    switch (type) {
      case 'HANDLE': return <User className="w-4 h-4 text-cyan-400" />;
      case 'DEVICE': return <Smartphone className="w-4 h-4 text-purple-400" />;
      case 'LOCATION': return <MapPin className="w-4 h-4 text-emerald-400" />;
      default: return <FileCode className="w-4 h-4 text-amber-400" />;
    }
  };

  const getNodeBadgeColor = (type) => {
    switch (type) {
      case 'HANDLE': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'DEVICE': return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'LOCATION': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      default: return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Network className="w-4 h-4 text-cyan-400" />
            <span>Cross-Evidence Knowledge Graph</span>
          </h2>
          <p className="text-xs text-slate-400">Entity resolution & multi-source relationship topology (Neo4j)</p>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          <span className="bg-slate-950 px-2.5 py-1 rounded border border-slate-800 text-slate-300 font-mono">
            {graphData.nodes.length} Nodes
          </span>
          <span className="bg-slate-950 px-2.5 py-1 rounded border border-slate-800 text-slate-300 font-mono">
            {graphData.edges.length} Edges
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Visual Graph Cards representation */}
        <div className="lg:col-span-2 bg-slate-950 border border-slate-850 rounded-xl p-4 min-h-[280px] space-y-3 relative overflow-hidden">
          <div className="text-[11px] font-mono text-slate-500 mb-2 uppercase tracking-wider">Discovered Graph Nodes</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {graphData.nodes.map((node) => (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className={`p-3 rounded-lg border transition cursor-pointer flex items-center justify-between ${
                  selectedNode?.id === node.id
                    ? 'bg-slate-850 border-cyan-400 shadow-md shadow-cyan-500/10'
                    : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
                    {getNodeIcon(node.type)}
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-100">{node.name}</div>
                    <div className="text-[10px] font-mono text-slate-400">{node.id}</div>
                  </div>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border font-mono ${getNodeBadgeColor(node.type)}`}>
                  {node.type}
                </span>
              </div>
            ))}
          </div>

          {/* Relationship Connections */}
          {graphData.edges.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-850">
              <div className="text-[11px] font-mono text-slate-500 mb-2 uppercase tracking-wider">Identified Relationships</div>
              <div className="space-y-2">
                {graphData.edges.map((edge, idx) => (
                  <div key={idx} className="bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs flex items-center justify-between">
                    <span className="font-mono text-cyan-300 font-medium">{edge.source}</span>
                    <div className="flex items-center space-x-1 text-slate-500 font-mono text-[10px]">
                      <ArrowRight className="w-3 h-3 text-cyan-400" />
                      <span className="bg-slate-950 text-cyan-400 px-1.5 py-0.5 rounded border border-cyan-500/20">{edge.relationship}</span>
                      <ArrowRight className="w-3 h-3 text-cyan-400" />
                    </div>
                    <span className="font-mono text-cyan-300 font-medium">{edge.target}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Node Detail Drawer */}
        <div className="bg-slate-950 border border-slate-850 rounded-xl p-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Entity Properties & Provenance</h3>
          {selectedNode ? (
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                <div className="text-slate-400 text-[10px] uppercase font-mono">Selected Entity</div>
                <div className="text-sm font-bold text-cyan-400 mt-0.5">{selectedNode.name}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">ID: {selectedNode.id}</div>
              </div>
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-slate-850 text-slate-400">
                  <span>Entity Type:</span>
                  <span className="text-slate-200 font-mono">{selectedNode.type}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-850 text-slate-400">
                  <span>Knowledge Graph Status:</span>
                  <span className="text-emerald-400 font-mono">Neo4j Synced</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-slate-500 text-xs">
              Click any node in the knowledge graph to view detailed attributes and provenance.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
