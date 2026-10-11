import time
import re
from typing import List, Dict, Any
from app.tools.registry import BaseInvestigativeTool, ToolInputSchema, ToolOutputSchema, StandardizedFinding, register_tool

@register_tool()
class TextEntityExtractor(BaseInvestigativeTool):
    name = "TextEntityExtractor"
    description = "Parses text or chat logs to extract key investigative entities (handles, phone numbers, emails, IP addresses, crypto wallets, timestamps)."
    supported_input_types = ["TEXT", "CHAT_LOG", "DOCUMENT"]
    capabilities = ["entity_extraction", "nlp", "handle_detection", "contact_extraction", "text_analysis"]

    async def execute(self, input_data: ToolInputSchema) -> ToolOutputSchema:
        start_time = time.time()
        text = input_data.text_content or ""
        case_id = input_data.case_id
        evidence_id = input_data.evidence_id

        # Extraction Regexes
        handles = list(set(re.findall(r'@[a-zA-Z0-9_]{3,30}', text)))
        raw_phones = list(set(re.findall(r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)))
        phone_numbers = [p for p in raw_phones if len(re.sub(r'\D', '', p)) >= 7]
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)))
        ip_addresses = list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)))
        crypto_wallets = list(set(re.findall(r'\b(0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b', text)))
        timestamps = list(set(re.findall(r'\b\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:\d{2})?\b', text)))

        standardized_findings: List[StandardizedFinding] = []

        for h in handles:
            standardized_findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="ENTITY",
                entity_type="HANDLE",
                entity=h,
                attribute="handle_name",
                value=h,
                confidence=0.95,
                source_tool=self.name,
                supporting_evidence={"text_snippet": text[:200]}
            ))

        for p in phone_numbers:
            standardized_findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="ENTITY",
                entity_type="PHONE",
                entity=p,
                attribute="phone_number",
                value=p,
                confidence=0.90,
                source_tool=self.name,
                supporting_evidence={"text_snippet": text[:200]}
            ))

        for e in emails:
            standardized_findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="ENTITY",
                entity_type="EMAIL",
                entity=e,
                attribute="email_address",
                value=e,
                confidence=0.95,
                source_tool=self.name,
                supporting_evidence={"text_snippet": text[:200]}
            ))

        for ip in ip_addresses:
            standardized_findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="ENTITY",
                entity_type="IP_ADDRESS",
                entity=ip,
                attribute="ip_address",
                value=ip,
                confidence=0.95,
                source_tool=self.name,
                supporting_evidence={"text_snippet": text[:200]}
            ))

        for w in crypto_wallets:
            standardized_findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="ENTITY",
                entity_type="CRYPTO_WALLET",
                entity=w,
                attribute="crypto_address",
                value=w,
                confidence=0.98,
                source_tool=self.name,
                supporting_evidence={"text_snippet": text[:200]}
            ))

        for ts in timestamps:
            standardized_findings.append(StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="ENTITY",
                entity_type="TIMESTAMP",
                entity=ts,
                attribute="timestamp",
                value=ts,
                confidence=0.85,
                source_tool=self.name,
                supporting_evidence={"text_snippet": text[:200]}
            ))

        # Check for custom entities parameter
        if input_data.parameters and "custom_entities" in input_data.parameters:
            for ce in input_data.parameters["custom_entities"]:
                standardized_findings.append(StandardizedFinding(
                    case_id=case_id,
                    evidence_id=evidence_id,
                    finding_type="ENTITY",
                    entity_type=ce.get("type", "CUSTOM"),
                    entity=str(ce.get("value", "")),
                    attribute=ce.get("type", "custom").lower(),
                    value=ce.get("value"),
                    confidence=ce.get("confidence", 0.90),
                    source_tool=self.name,
                    supporting_evidence={"parameter_source": True}
                ))

        return ToolOutputSchema(
            tool_name=self.name,
            success=True,
            findings_extracted=len(standardized_findings),
            data={
                "total_entities": len(standardized_findings),
                "handles": handles,
                "phone_numbers": phone_numbers,
                "emails": emails,
                "ip_addresses": ip_addresses,
                "crypto_wallets": crypto_wallets,
                "timestamps": timestamps
            },
            findings=standardized_findings,
            execution_time_ms=(time.time() - start_time) * 1000
        )

# Backward compatibility alias
EntityExtractorTool = TextEntityExtractor
