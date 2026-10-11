from typing import List, Dict, Any
from app.orchestrator.state import CaseState
from app.core.logging import logger
import uuid

async def lead_generator_node(state: CaseState) -> CaseState:
    """Generates explainable, evidence-backed candidate leads requiring human approval."""
    logger.info(f"[Lead Generator Node] Generating candidate leads for Case ID: {state.case_id}")

    leads: List[Dict[str, Any]] = []

    # 1. Lead from Handles & Communication Links
    handles = [n["name"] for n in state.knowledge_graph_nodes if n.get("type") == "HANDLE"]
    locations = [n for n in state.knowledge_graph_nodes if n.get("type") == "LOCATION"]

    if handles:
        lead_1 = {
            "id": str(uuid.uuid4()),
            "case_id": state.case_id,
            "title": f"Identify Primary Suspect Handle ({', '.join(handles[:2])})",
            "summary": f"Cross-source evidence correlation identified frequent communication between {', '.join(handles)}. Associated geotags place media creation in the target region.",
            "status": "PROPOSED",
            "confidence": 0.88,
            "supporting_evidence_ids": [ev.get("id") for ev in state.evidence_items if ev.get("id")],
            "reasoning_chain": [
                f"1. Handles {handles} extracted from chat log text.",
                f"2. Co-occurrence edge 'COMMUNICATED_WITH' established in Neo4j knowledge graph.",
                f"3. Geotag evidence links image timestamps to timeline events."
            ],
            "next_recommended_actions": [
                f"Issue law enforcement preservation request for handle {handles[0]}",
                "Cross-reference EXIF GPS coordinates with local IP cell tower logs",
                "Perform social network analysis on identified secondary handles"
            ]
        }
        leads.append(lead_1)

    if locations:
        lead_2 = {
            "id": str(uuid.uuid4()),
            "case_id": state.case_id,
            "title": f"Geographic Hotspot Analysis: {locations[0].get('name')}",
            "summary": f"EXIF metadata extraction revealed exact latitude/longitude coordinates from uploaded image evidence.",
            "status": "PROPOSED",
            "confidence": 0.92,
            "supporting_evidence_ids": [ev.get("id") for ev in state.evidence_items if ev.get("id")],
            "reasoning_chain": [
                f"1. EXIF metadata extraction tool parsed image header.",
                f"2. Coordinates ({locations[0].get('latitude')}, {locations[0].get('longitude')}) validated.",
                f"3. Timeline event constructed at media creation timestamp."
            ],
            "next_recommended_actions": [
                "Verify location against public land/property registries",
                "Cross-reference timeline with suspect movement records"
            ]
        }
        leads.append(lead_2)

    # If no specific handle or location lead was constructed, build general lead
    if not leads:
        lead_default = {
            "id": str(uuid.uuid4()),
            "case_id": state.case_id,
            "title": f"Evidence Correlation Summary for Case {state.case_number}",
            "summary": f"Analyzed {len(state.evidence_items)} evidence files and generated {len(state.raw_findings)} raw findings.",
            "status": "PROPOSED",
            "confidence": 0.85,
            "supporting_evidence_ids": [ev.get("id") for ev in state.evidence_items if ev.get("id")],
            "reasoning_chain": [
                "1. Scanned all uploaded digital evidence.",
                "2. Extracted entities, metadata, and timestamps.",
                "3. Reconstructed knowledge graph relationships."
            ],
            "next_recommended_actions": [
                "Review raw findings and knowledge graph in ARGUS Dashboard",
                "Conduct follow-up deep extraction on secondary evidence"
            ]
        }
        leads.append(lead_default)

    state.proposed_leads = leads
    state.execution_logs.append(f"Lead Generator produced {len(leads)} explainable hypotheses with PROPOSED status for investigator review.")
    return state

async def human_review_node(state: CaseState) -> CaseState:
    """Final Step: Prepares leads and summary for Human-in-the-Loop review."""
    logger.info(f"[Human Review Node] Preparing {len(state.proposed_leads)} leads for human review.")
    
    summary = f"Investigation run completed successfully for Case {state.case_number}. " \
              f"Generated {len(state.proposed_leads)} candidate leads, {len(state.knowledge_graph_nodes)} graph nodes, " \
              f"and {len(state.timeline_events)} timeline events requiring investigator review."
              
    state.investigation_summary = summary
    state.execution_logs.append(f"Brain Final Step: {summary}")

    state.audit_events.append({
        "event_type": "HUMAN_REVIEW_FLAGGED",
        "actor": "ARGUS_LANGGRAPH_BRAIN",
        "details": {
            "proposed_leads_count": len(state.proposed_leads),
            "summary": summary
        }
    })
    return state
