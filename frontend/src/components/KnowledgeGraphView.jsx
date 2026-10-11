import React, { useState } from 'react';
import { Share2, Server, User, Smartphone, MapPin, FileText, Calendar, Link, Search } from 'lucide-react';

export default function KnowledgeGraphView({ orchestratorResults }) {
  const [filterType, setFilterType] = useState('ALL');
  const [searchNode, setSearchNode] = useState('');

  const nodes = orchestratorResults?.correlations?.knowledge_graph?.nodes || [];
  const edges = orchestratorResults?.correlations?.knowledge_graph?.edges || [];

  if (nodes.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-xs">
        6. Knowledge Graph: No nodes populated yet. Run ARGUS Investigation to reconstruct entity relationships in Neo4j knowledge graph.
      </div>
    );
  }

  const getNodeIcon = (label) => {
    switch (label) {
      case 'Person':
        return <User className="w-4 h-4 text-emerald-400" />;
      case 'Account':
        return <Share2 className="w-4 h-4 text-cyan-400" />;
      case 'Device':
        return <Smartphone className="w-4 h-4 text-amber-400" />;
      case 'Location':
        return <MapPin className="w-4 h-4 text-rose-400" />;
      case 'Evidence':
        return <FileText className="w-4 h-4 text-purple-400" />;
      case 'Event':
        return <Calendar className="w-4 h-4 text-blue-400" />;
      default:
        return <Server className="w-4 h-4 text-slate-400" />;
    }
  };

  const filteredNodes = nodes.filter((n) => {
    const matchesType = filterType === 'ALL' || n.label === filterType;
    const matchesSearch = !searchNode || n.name.toLowerCase().includes(searchNode.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Share2 className="w-5 h-5 text-cyan-400" />
            6. Neo4j Knowledge Graph & Entity Relationships ({nodes.length} Nodes, {edges.length} Edges)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Canonical entity nodes (Case, Person, Account, Device, Location, Evidence, Event) and evidence-backed relationships.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-48">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search graph nodes..."
              value={searchNode}
              onChange={(e) => setSearchNode(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none font-mono"
          >
            <option value="ALL">ALL NODES</option>
            <option value="Person">Person</option>
            <option value="Account">Account</option>
            <option value="Device">Device</option>
            <option value="Location">Location</option>
            <option value="Evidence">Evidence</option>
            <option value="Event">Event</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-mono text-xs">
        {/* Nodes Panel */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Canonical Resolved Entities ({filteredNodes.length})
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1">
            {filteredNodes.map((n) => (
              <div key={n.id} className="bg-slate-950 border border-slate-800 p-3 rounded-lg space-y-1.5 hover:border-cyan-500/50 transition">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getNodeIcon(n.label)}
                    <span className="font-bold text-slate-200">{n.name}</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400">
                    {n.label}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 truncate">ID: {n.id}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Edges & Relationships Panel */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Graph Edges ({edges.length})
          </h3>

          <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl max-h-96 overflow-y-auto space-y-2 text-[11px]">
            {edges.length === 0 ? (
              <div className="text-slate-500 text-center py-4">No edges generated</div>
            ) : (
              edges.map((e, idx) => (
                <div key={idx} className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-cyan-300 font-bold">
                    <span className="truncate max-w-[100px]">{e.source}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                      {e.relationship}
                    </span>
                    <span className="truncate max-w-[100px]">{e.target}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex justify-between pt-1">
                    <span>Conf: {((e.confidence || 0.90) * 100).toFixed(0)}%</span>
                    <span>Provenanced</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
