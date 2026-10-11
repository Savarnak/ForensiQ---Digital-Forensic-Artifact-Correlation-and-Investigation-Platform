import React, { useState } from 'react';
import { Upload, FileText, Image as ImageIcon, FileCode, Check, AlertCircle, File, Sparkles } from 'lucide-react';
import { uploadEvidence } from '../services/api';

export default function EvidenceWorkspace({ activeCase, evidenceList, onEvidenceUploaded }) {
  const [fileType, setFileType] = useState('CHAT_LOG');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isSyntheticUploading, setIsSyntheticUploading] = useState(false);

  if (!activeCase) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500">
        Please select or create an active case above to manage evidence.
      </div>
    );
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMsg(null);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    setIsUploading(true);
    setErrorMsg(null);
    try {
      const uploaded = await uploadEvidence(activeCase.id, fileType, selectedFile);
      onEvidenceUploaded(uploaded);
      setSelectedFile(null);
    } catch (err) {
      setErrorMsg(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadSyntheticSet = async () => {
    setIsSyntheticUploading(true);
    setErrorMsg(null);
    try {
      // Create synthetic blob files representing case_001 evidence
      const syntheticFiles = [
        {
          name: "chats.json",
          type: "CHAT_LOG",
          mime: "application/json",
          content: JSON.stringify([
            {
              chat_id: "CHAT-1001",
              timestamp: "2026-08-10T14:00:00Z",
              sender_handle: "@CyberHawk",
              recipient_handle: "@NightOwl",
              message_text: "Confirming sync at Dock 14 near coordinates 37.774929, -122.419416. Call me on +1-555-0199.",
              ip_address: "192.168.1.105",
              device_id: "DEV-SPH-9001"
            }
          ])
        },
        {
          name: "calls.csv",
          type: "CALL_LOG",
          mime: "text/csv",
          content: "call_id,timestamp,caller_number,recipient_number,duration_sec,cell_tower_id,caller_account,recipient_account\nCALL-5002,2026-08-10T14:02:15Z,+1-555-0199,+1-555-0144,124,TOWER-SF-104,@CyberHawk,@NightOwl"
        },
        {
          name: "gps.csv",
          type: "GPS_LOG",
          mime: "text/csv",
          content: "timestamp,device_id,latitude,longitude,location_label\n2026-08-10T14:05:30Z,DEV-SPH-9001,37.774929,-122.419416,San Francisco Dock 14 (LOC-SF-01)"
        },
        {
          name: "evidence_photo_01.txt",
          type: "IMAGE",
          mime: "text/plain",
          content: "EXIF_MAKE: Samsung\nEXIF_MODEL: Galaxy S22 (DEV-SPH-9001)\nEXIF_DATETIME: 2026-08-10 14:05:30\nGPS_LAT: 37.774929\nGPS_LON: -122.419416\nOCR_TEXT: TARGET HANDLE @CyberHawk LOCATED AT SF DOCK 14"
        }
      ];

      for (const item of syntheticFiles) {
        const blob = new Blob([item.content], { type: item.mime });
        const fileObj = new File([blob], item.name, { type: item.mime });
        const res = await uploadEvidence(activeCase.id, item.type, fileObj);
        onEvidenceUploaded(res);
      }
      alert("Successfully ingested Synthetic Case 001 evidence set into Case workspace!");
    } catch (err) {
      setErrorMsg(`Synthetic batch upload error: ${err.message}`);
    } finally {
      setIsSyntheticUploading(false);
    }
  };

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'IMAGE':
        return <ImageIcon className="w-4 h-4 text-purple-400" />;
      case 'CHAT_LOG':
      case 'CALL_LOG':
        return <FileCode className="w-4 h-4 text-cyan-400" />;
      default:
        return <FileText className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Upload className="w-5 h-5 text-cyan-400" />
            2. Evidence Workspace & Digital Forensic Ingestion
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ingest digital evidence (chats, call CDRs, telematics GPS logs, images, reports) into Case <span className="font-mono text-cyan-400 font-bold">{activeCase.case_number}</span>.
          </p>
        </div>

        <button
          onClick={handleUploadSyntheticSet}
          disabled={isSyntheticUploading}
          className="flex items-center space-x-2 text-xs font-semibold bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 px-3.5 py-2 rounded-lg transition shadow-sm"
        >
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>{isSyntheticUploading ? 'Ingesting Batch...' : 'Upload Synthetic Case 001 Evidence Set'}</span>
        </button>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-950/80 border border-rose-800 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Upload Form Grid */}
      <form onSubmit={handleUploadSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs">
        <div>
          <label className="block text-slate-400 mb-1 font-mono">Evidence Category *</label>
          <select
            value={fileType}
            onChange={(e) => setFileType(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="CHAT_LOG">CHAT_LOG (json/txt)</option>
            <option value="CALL_LOG">CALL_LOG (cdr/csv)</option>
            <option value="GPS_LOG">GPS_LOG (telematics/csv)</option>
            <option value="IMAGE">IMAGE (jpg/png)</option>
            <option value="DOCUMENT">DOCUMENT (pdf/txt)</option>
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="block text-slate-400 mb-1 font-mono">Select Evidence File *</label>
          <input
            type="file"
            required
            onChange={handleFileChange}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-300 focus:outline-none focus:border-cyan-500 font-mono file:mr-3 file:py-1 file:px-2 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-cyan-950 file:text-cyan-400"
          />
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={isUploading || !selectedFile}
            className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-bold rounded-lg transition flex items-center justify-center space-x-2"
          >
            <Upload className="w-4 h-4" />
            <span>{isUploading ? 'Ingesting...' : 'Ingest Evidence'}</span>
          </button>
        </div>
      </form>

      {/* Evidence Repository Inventory Table */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
            Ingested Evidence Repository ({evidenceList.length} Files)
          </h3>
        </div>

        {evidenceList.length === 0 ? (
          <div className="text-center py-8 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
            No evidence artifacts ingested for Case {activeCase.case_number}. Upload files or click 'Upload Synthetic Case 001 Evidence Set' above.
          </div>
        ) : (
          <div className="overflow-x-auto border border-slate-800 rounded-lg bg-slate-950/50">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 font-mono">
                  <th className="p-3">Category</th>
                  <th className="p-3">File Name</th>
                  <th className="p-3">MIME / Type</th>
                  <th className="p-3">File Path / Reference</th>
                  <th className="p-3">Extracted Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {evidenceList.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-900/60 transition">
                    <td className="p-3">
                      <div className="flex items-center space-x-2">
                        {getFileIcon(ev.file_type)}
                        <span className="font-bold text-slate-300">{ev.file_type}</span>
                      </div>
                    </td>
                    <td className="p-3 font-semibold text-cyan-300">{ev.file_name}</td>
                    <td className="p-3 text-slate-400">{ev.mime_type || 'text/plain'}</td>
                    <td className="p-3 text-slate-500 text-[11px] max-w-xs truncate">{ev.file_path}</td>
                    <td className="p-3 text-slate-400 text-[11px]">
                      {ev.extracted_metadata ? (
                        <span className="text-emerald-400 font-sans">
                          Parsed ({Object.keys(ev.extracted_metadata).length} keys)
                        </span>
                      ) : (
                        <span className="text-slate-600">Pending Extraction</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
