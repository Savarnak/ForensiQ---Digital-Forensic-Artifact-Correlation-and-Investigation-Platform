import time
import re
from typing import List
from app.tools.registry import BaseInvestigativeTool, ToolInputSchema, ToolOutputSchema, StandardizedFinding, register_tool

@register_tool()
class TimelineExtractor(BaseInvestigativeTool):
    name = "TimelineExtractor"
    description = "Parses timestamps, date expressions, chronological sequences, and event logs from evidence text to build timelines."
    supported_input_types = ["TEXT", "CHAT_LOG", "TIMELINE", "DOCUMENT"]
    capabilities = ["timeline_extraction", "temporal_analysis", "event_sequencing", "chronology"]

    async def execute(self, input_data: ToolInputSchema) -> ToolOutputSchema:
        start_time = time.time()
        text = input_data.text_content or ""
        case_id = input_data.case_id
        evidence_id = input_data.evidence_id

        # Patterns for ISO dates, standard dates, and time expressions
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}(?: \d{1,2}:\d{2}(?: ?[AP]M)?)?\b',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        ]

        extracted_events = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                ts = m.group(0)
                start_idx = max(0, m.start() - 40)
                end_idx = min(len(text), m.end() + 60)
                snippet = text[start_idx:end_idx].strip()

                extracted_events.append({
                    "timestamp": ts,
                    "context": snippet
                })

        findings: List[StandardizedFinding] = []
        for event in extracted_events:
            findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="TIMELINE_EVENT",
                entity_type="DATETIME",
                entity=event["timestamp"],
                attribute="event_timestamp",
                value=event,
                confidence=0.88,
                source_tool=self.name,
                supporting_evidence={"context_snippet": event["context"]}
            ))

        return ToolOutputSchema(
            tool_name=self.name,
            success=True,
            findings_extracted=len(findings),
            data={
                "events_count": len(findings),
                "timeline_events": [f.value for f in findings]
            },
            findings=findings,
            execution_time_ms=(time.time() - start_time) * 1000
        )
