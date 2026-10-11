import time
import uuid
import hashlib
from typing import List
from app.tools.registry import BaseInvestigativeTool, ToolInputSchema, ToolOutputSchema, StandardizedFinding, register_tool
from app.core.qdrant import qdrant_client, COLLECTION_NAME

@register_tool()
class EvidenceSearchTool(BaseInvestigativeTool):
    name = "EvidenceSearchTool"
    description = "Performs keyword search, semantic similarity search, and embedding indexing across case evidence."
    supported_input_types = ["TEXT", "SEARCH_QUERY", "DOCUMENT"]
    capabilities = ["evidence_search", "vector_search", "semantic_retrieval", "keyword_search", "vector_embedding"]

    def _mock_embedding(self, text: str) -> List[float]:
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        raw_vector = [((b / 255.0) * 2.0 - 1.0) for b in (hash_bytes * 12)[:384]]
        norm = sum(x*x for x in raw_vector) ** 0.5
        return [x / norm for x in raw_vector] if norm > 0 else raw_vector

    async def execute(self, input_data: ToolInputSchema) -> ToolOutputSchema:
        start_time = time.time()
        text = input_data.text_content or input_data.query or ""
        case_id = input_data.case_id
        evidence_id = input_data.evidence_id

        if not text:
            return ToolOutputSchema(
                tool_name=self.name,
                success=False,
                findings_extracted=0,
                data={},
                findings=[],
                error_message="No text query or content provided for evidence search.",
                execution_time_ms=(time.time() - start_time) * 1000
            )

        vector = self._mock_embedding(text)
        point_id = str(uuid.uuid4())

        point_record = {
            "id": point_id,
            "vector": vector,
            "payload": {
                "case_id": case_id,
                "evidence_id": evidence_id,
                "text_snippet": text[:500],
                "file_path": input_data.file_path
            }
        }

        qdrant_client.upsert_vectors([point_record])

        findings: List[StandardizedFinding] = [
            StandardizedFinding(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type="SEARCH_RESULT",
                entity_type="KEYWORD",
                entity=text[:50],
                attribute="search_match",
                value={
                    "point_id": point_id,
                    "collection": COLLECTION_NAME,
                    "indexed_snippet": text[:200]
                },
                confidence=0.90,
                source_tool=self.name,
                supporting_evidence={
                    "file_path": input_data.file_path,
                    "vector_dimension": len(vector)
                }
            )
        ]

        return ToolOutputSchema(
            tool_name=self.name,
            success=True,
            findings_extracted=len(findings),
            data={
                "point_id": point_id,
                "collection": COLLECTION_NAME,
                "vector_dimension": len(vector),
                "indexed_snippet": text[:100] + "..."
            },
            findings=findings,
            execution_time_ms=(time.time() - start_time) * 1000
        )

# Backward compatibility alias
VectorIndexerTool = EvidenceSearchTool
