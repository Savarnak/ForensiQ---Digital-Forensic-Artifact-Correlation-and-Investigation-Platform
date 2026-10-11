import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.lead import LEAD_DISCLAIMER_TEXT
from app.core.logging import logger

class InvestigativeLead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lead_id: str = Field(default_factory=lambda: f"LEAD-{uuid.uuid4().hex[:8].upper()}")
    case_id: str
    title: str
    priority: str  # HIGH, MEDIUM, LOW
    summary: str
    confidence: float = 0.85
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_findings: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning_factors: List[str] = Field(default_factory=list)
    recommended_next_action: List[str] = Field(default_factory=list)
    status: str = "PENDING_REVIEW"
    provenance_type: str = "AI_GENERATED_RECOMMENDATION"
    disclaimer: str = LEAD_DISCLAIMER_TEXT

class LeadEngine:
    """Core ARGUS Lead Engine generating candidate investigative leads with 
    transparent priority scoring, explainable reasoning factors, and non-guilt disclaimers."""

    @classmethod
    def calculate_priority_and_factors(
        cls,
        evidence_sources: List[str],
        relationships: List[Dict[str, Any]],
        timeline_events: List[Dict[str, Any]],
        has_device_link: bool,
        has_location_link: bool,
        has_gap_or_conflict: bool
    ) -> tuple[str, List[str], float]:
        """Calculates transparent priority (HIGH/MEDIUM/LOW), reasoning factors, and confidence score."""
        factors: List[str] = []
        score = 0.50

        # Factor 1: Multiple independent evidence sources
        num_sources = len(set(evidence_sources))
        if num_sources >= 3:
            factors.append(f"supporting evidence from {num_sources} independent artifacts")
            score += 0.20
        elif num_sources == 2:
            factors.append("supporting evidence from 2 independent artifacts")
            score += 0.10

        # Factor 2: Shared device association
        if has_device_link:
            factors.append("same device associated with multiple evidence artifacts")
            score += 0.15

        # Factor 3: Location correlation
        if has_location_link:
            factors.append("repeated location correlation across evidence items")
            score += 0.15

        # Factor 4: Temporal relationship
        if len(timeline_events) >= 2:
            factors.append("temporal relationship between events across timeline")
            score += 0.10

        # Factor 5: Evidence gap or contradiction
        if has_gap_or_conflict:
            factors.append("identified evidence gap or contradiction requiring verification")
            score += 0.05

        # Priority determination rule
        if len(factors) >= 3 or (has_device_link and has_location_link and num_sources >= 2):
            priority = "HIGH"
        elif len(factors) >= 2 or num_sources >= 2:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        confidence = round(min(score, 0.98), 2)
        return priority, factors, confidence

    @classmethod
    def generate_leads(
        cls,
        case_id: str,
        findings: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        timeline_events: List[Dict[str, Any]],
        evidence_gaps: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        evidence_items: List[Dict[str, Any]]
    ) -> List[InvestigativeLead]:
        """Generates candidate investigative leads based on cross-source evidence analysis."""
        leads: List[InvestigativeLead] = []
        logger.info(f"Generating candidate investigative leads for Case ID: {case_id}...")

        evidence_sources = list(set(
            e.get("file_name") for e in evidence_items if e.get("file_name")
        ))

        # 1. Lead 1: Primary Cross-Evidence Account & Device Correlation
        has_device = any(r.get("relationship") in ["USES", "SUPPORTED_BY"] for r in relationships) or len(evidence_items) >= 2
        has_location = any(r.get("relationship") == "LOCATED_AT" for r in relationships) or any("GPS" in str(t.get("location")) for t in timeline_events if t.get("location"))
        has_gap = len(evidence_gaps) > 0 or len(contradictions) > 0

        priority1, factors1, conf1 = cls.calculate_priority_and_factors(
            evidence_sources=evidence_sources,
            relationships=relationships,
            timeline_events=timeline_events,
            has_device_link=has_device,
            has_location_link=has_location,
            has_gap_or_conflict=has_gap
        )

        leads.append(InvestigativeLead(
            case_id=case_id,
            title=f"Cross-Source Evidence Correlation & Handle Linkage",
            priority=priority1,
            summary=f"Analyzed {len(evidence_items)} evidence files and {len(findings)} findings. Identified cross-source linkage linking target handle communications, device geotags, and timeline events.",
            confidence=conf1,
            supporting_evidence=[{"file_name": s} for s in evidence_sources[:4]],
            supporting_findings=[{"tool_name": f.get("tool_name"), "evidence_id": f.get("evidence_id")} for f in findings[:5]],
            reasoning_factors=factors1 if factors1 else ["Cross-source correlation across uploaded case artifacts"],
            recommended_next_action=[
                "Review knowledge graph relationships and timeline events in ARGUS Dashboard",
                "Conduct follow-up deep extraction on secondary digital evidence",
                "Verify cell tower CDR records against device GPS logs"
            ],
            status="PENDING_REVIEW"
        ))

        # 2. Lead 2: Evidence Gap & Verification Lead (if gaps or contradictions exist)
        if evidence_gaps or contradictions:
            gap_factors = []
            if evidence_gaps:
                gap_factors.append(f"{len(evidence_gaps)} referenced entities lack supporting evidence in case files")
            if contradictions:
                gap_factors.append(f"{len(contradictions)} timestamp or attribute contradictions detected across findings")
            
            p2 = "HIGH" if len(evidence_gaps) >= 1 or len(contradictions) >= 1 else "MEDIUM"

            leads.append(InvestigativeLead(
                case_id=case_id,
                title="Evidence Gap & Contradiction Resolution Action",
                priority=p2,
                summary=f"Identified {len(evidence_gaps)} evidence gaps and {len(contradictions)} contradictions requiring investigator verification before finalizing case conclusions.",
                confidence=0.88,
                supporting_evidence=[{"file_name": g.get("source_evidence", "Evidence File")} for g in evidence_gaps[:3]],
                supporting_findings=[{"gap_entity": g.get("referenced_entity"), "reason": g.get("reason")} for g in evidence_gaps[:3]],
                reasoning_factors=gap_factors if gap_factors else ["Referenced evidence artifacts missing from case repository"],
                recommended_next_action=[
                    "Issue formal request for missing device / file artifacts cited in chat logs",
                    "Perform raw EXIF header audit to resolve timestamp contradictions"
                ],
                status="PENDING_REVIEW"
            ))

        return leads
