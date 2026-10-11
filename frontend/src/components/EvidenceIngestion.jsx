import React, { useState } from 'react';
import { UploadCloud, FileCode, Image, FileText, Sparkles, Check } from 'lucide-react';
import { uploadEvidence } from '../services/api';

export default function EvidenceIngestion({ activeCase, evidenceList, onEvidenceUploaded, onRunOrchestrator, isOrchestrating }) {
  const [fileType, setFileType] = useState('IMAGE');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  if (!activeCase) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-sm">
        Please select or create an investigation case above to begin evidence ingestion.
      </div>
    );
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError('');
    try {
      const uploaded = await uploadEvidence(activeCase.id, fileType, file);
      onEvidenceUploaded(uploaded);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleLoadSyntheticEvidence = async () => {
    setUploading(true);
    setError('');
    try {
      // Create synthetic chat log blob
      const chatBlob = new Blob([
        `[2026-08-10 14:00:12] @CyberHawk: Are you ready for the sync?
[2026-08-10 14:00:45] @NightOwl: Yes, I am at the meeting location. Contact me on +1-555-0199 or email alpha@fictional-domain.test.
[2026-08-10 14:01:20] @CyberHawk: Sending the file now. Confirm receipt at 192.168.1.105.
[2026-08-10 14:02:00] @NightOwl: Received. Payment routed to wallet 0x71C7656EC7ab88b098defB751B7401B5f6d8976F.`
      ], { type: 'text/plain' });
      const chatFile = new File([chatBlob], "synthetic_chat_log.txt", { type: "text/plain" });

      await uploadEvidence(activeCase.id, "CHAT_LOG", chatFile);

      // Create synthetic photo blob
      const imgCanvas = document.createElement("canvas");
      imgCanvas.width = 400;
      imgCanvas.height = 300;
      const ctx = imgCanvas.getContext("2d");
      ctx.fillStyle = "#1e293b";
      ctx.fillRect(0, 0, 400, 300);
      ctx.fillStyle = "#38bdf8";
      ctx.font = "16px sans-serif";
      ctx.fillText("SYNTHETIC GEOTAG EVIDENCE", 40, 100);
      ctx.fillText("@CyberHawk / @NightOwl Meeting Location", 40, 140);
      
      imgCanvas.toBlob(async (blob) => {
        const imgFile = new File([blob], "synthetic_geotag_photo.jpg", { type: "image/jpeg" });
        const uploadedImg = await uploadEvidence(activeCase.id, "IMAGE", imgFile);
        onEvidenceUploaded(uploadedImg);
        setUploading(false);
      }, "image/jpeg");

    } catch (err) {
      setError(err.message);
      setUploading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <UploadCloud className="w-4 h-4 text-cyan-400" />
            <span>Digital Evidence Vault</span>
          </h2>
          <p className="text-xs text-slate-400">Ingest chats, images, documents for multi-modal analysis</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleLoadSyntheticEvidence}
            disabled={uploading}
            className="bg-slate-800 hover:bg-slate-750 text-cyan-300 border border-cyan-500/30 px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Load Synthetic Demo Files</span>
          </button>

          <button
            onClick={onRunOrchestrator}
            disabled={isOrchestrating || evidenceList.length === 0}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-2 shadow-lg ${
              isOrchestrating || evidenceList.length === 0
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 shadow-emerald-500/20'
            }`}
          >
            {isOrchestrating ? (
              <span>Orchestrating Pipeline...</span>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Run ARGUS Orchestrator</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs p-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Evidence List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {evidenceList.length === 0 ? (
          <div className="col-span-full border-2 border-dashed border-slate-800 rounded-xl p-6 text-center">
            <p className="text-xs text-slate-400 mb-3">No evidence ingested yet for this case.</p>
            <label className="cursor-pointer inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg text-xs font-medium border border-slate-700 transition">
              <UploadCloud className="w-4 h-4 text-cyan-400" />
              <span>Select File to Ingest</span>
              <input type="file" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>
        ) : (
          evidenceList.map((item) => (
            <div key={item.id} className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 flex items-start space-x-3">
              <div className="p-2 bg-slate-900 border border-slate-800 rounded-lg text-cyan-400 shrink-0">
                {item.file_type === 'IMAGE' ? <Image className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-xs font-semibold text-slate-200 truncate">{item.file_name}</h4>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                    {item.file_type}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono truncate">
                    SHA: {item.hash_sha256 ? item.hash_sha256.substring(0, 8) : 'Pending'}...
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
