const API_BASE = 'https://forensiq-2c4x.onrender.com/api';

async function parseJsonResponse(res, defaultErrMsg) {
  const text = await res.text();

  if (!res.ok) {
    let detail = text;
    if (text) {
      try {
        const parsed = JSON.parse(text);
        if (parsed && parsed.detail) detail = parsed.detail;
      } catch {
        // Use raw text if not valid JSON
      }
    }
    throw new Error(`API request failed (${res.status}): ${detail || res.statusText || defaultErrMsg}`);
  }

  if (res.status === 204 || !text || !text.trim()) {
    return null;
  }

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const trimmed = text.trim();
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
      try {
        return JSON.parse(trimmed);
      } catch {
        // Fall back to error throw below
      }
    }
    throw new Error(`Invalid response format (Content-Type '${contentType}'): ${text.substring(0, 100)}`);
  }

  try {
    return JSON.parse(text);
  } catch (err) {
    throw new Error(`Failed to parse JSON response: ${err.message}`);
  }
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return parseJsonResponse(res, 'Backend server unavailable');
}

export async function fetchCases() {
  const res = await fetch(`${API_BASE}/cases`);
  return parseJsonResponse(res, 'Failed to fetch cases');
}

export async function createCase(caseData) {
  const res = await fetch(`${API_BASE}/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(caseData),
  });
  return parseJsonResponse(res, 'Failed to create case');
}

export async function loadSyntheticCase() {
  const res = await fetch(`${API_BASE}/cases/synthetic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return parseJsonResponse(res, 'Failed to load synthetic case 001');
}

export async function fetchCaseById(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}`);
  return parseJsonResponse(res, 'Failed to fetch case details');
}

export async function uploadEvidence(caseId, fileType, file) {
  const formData = new FormData();
  formData.append('file_type', fileType);
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/cases/${caseId}/evidence`, {
    method: 'POST',
    body: formData,
  });
  return parseJsonResponse(res, 'Failed to upload evidence');
}

export async function fetchEvidence(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/evidence`);
  return parseJsonResponse(res, 'Failed to fetch evidence files');
}

export async function fetchGoals(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/goals`);
  if (!res.ok) return [];
  try {
    const text = await res.text();
    if (!text || !text.trim()) return [];
    return JSON.parse(text);
  } catch {
    return [];
  }
}

export async function saveGoal(caseId, goalText) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/goals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal_text: goalText, status: 'ACTIVE' }),
  });
  return parseJsonResponse(res, 'Failed to save goal');
}

export async function runOrchestrator(caseId) {
  const res = await fetch(`${API_BASE}/orchestrator/run/${caseId}`, {
    method: 'POST',
  });
  return parseJsonResponse(res, 'ARGUS Brain orchestration failed');
}

export async function fetchOrchestratorResults(caseId) {
  const res = await fetch(`${API_BASE}/orchestrator/results/${caseId}`);
  return parseJsonResponse(res, 'Failed to fetch orchestrator results');
}

export async function fetchTimeline(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/timeline`);
  return parseJsonResponse(res, 'Failed to fetch case timeline');
}

export async function fetchGapsAndContradictions(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/analysis/gaps-contradictions`);
  return parseJsonResponse(res, 'Failed to fetch gaps and contradictions');
}

export async function fetchAuditEvents(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/audit`);
  const data = await parseJsonResponse(res, 'Failed to fetch audit events');
  return data || [];
}

export async function fetchLeads(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/leads`);
  const data = await parseJsonResponse(res, 'Failed to fetch candidate leads');
  if (!data) return [];
  return Array.isArray(data) ? data : (data.leads || []);
}

export async function approveLead(leadId, investigatorId, reason) {
  const res = await fetch(`${API_BASE}/leads/${leadId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ investigator_id: investigatorId, reason }),
  });
  return parseJsonResponse(res, 'Lead approval failed');
}

export async function rejectLead(leadId, investigatorId, reason) {
  const res = await fetch(`${API_BASE}/leads/${leadId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ investigator_id: investigatorId, reason }),
  });
  return parseJsonResponse(res, 'Lead rejection failed');
}

export async function requestAnalysisLead(leadId, investigatorId, reason) {
  const res = await fetch(`${API_BASE}/leads/${leadId}/request-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ investigator_id: investigatorId, reason }),
  });
  return parseJsonResponse(res, 'Request analysis failed');
}
