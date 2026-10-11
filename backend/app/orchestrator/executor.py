import time
import json
import hashlib
from typing import Dict, Any
from app.orchestrator.state import CaseState
from app.tools.registry import tool_registry, ToolInputSchema, StandardizedFinding
from app.core.logging import logger

def compute_finding_dedup_key(case_id: str, evidence_id: str, tool_name: str, finding_type: str, content: Any) -> str:
    content_str = json.dumps(content, sort_keys=True) if isinstance(content, (dict, list)) else str(content)
    raw = f"{case_id}_{evidence_id}_{tool_name}_{finding_type}_{content_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

async def executor_node(state: CaseState) -> CaseState:
    """Executes pending tasks through the registered tool interface ('Hands')."""
    import os
    pending_tasks = [t for t in state.tasks if t.status == "PENDING"]
    logger.info(f"[Executor Node] Executing {len(pending_tasks)} pending tasks for Case ID: {state.case_id}")
    
    # Track existing finding keys for deterministic deduplication
    existing_finding_keys = set()
    for f in state.raw_findings:
        k = compute_finding_dedup_key(
            state.case_id,
            f.get("evidence_id") or "",
            f.get("tool_name") or "",
            f.get("finding_type") or "",
            f.get("content") or {}
        )
        existing_finding_keys.add(k)

    for task in pending_tasks:
        tool = tool_registry.get(task.tool_name) or tool_registry.get_tool(task.tool_name)
        if not tool:
            logger.warning(f"Tool capability '{task.tool_name}' not found in registry.")
            task.status = "FAILED"
            state.audit_events.append({
                "event_type": "TOOL_EXECUTION_FAILED",
                "actor": "ARGUS_EXECUTOR",
                "details": {"task_id": task.task_id, "tool_name": task.tool_name, "error": "Tool not registered"}
            })
            continue

        # Target specific evidence item assigned to task
        matched_evidences = [
            ev for ev in state.evidence_items 
            if (task.evidence_id and ev.get("id") == task.evidence_id) or
               (task.file_name and ev.get("file_name") == task.file_name) or
               (ev.get("file_name") and ev.get("file_name") in task.objective)
        ]
        
        target_evidences = matched_evidences
        if not target_evidences:
            # Fallback: if task objective doesn't name a file, execute on evidence items without duplicate execution
            target_evidences = state.evidence_items[:1] if state.evidence_items else [{}]

        task_success = True
        total_extracted = 0

        for target_evidence in target_evidences:
            file_path = target_evidence.get("file_path")
            text_content = target_evidence.get("text_content")

            # Load actual evidence text content from disk if not populated
            if (not text_content or text_content == target_evidence.get("file_name")) and file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text_content = f.read()
                except Exception as err:
                    logger.warning(f"Failed to read evidence file '{file_path}': {err}")

            input_data = ToolInputSchema(
                case_id=state.case_id,
                evidence_id=target_evidence.get("id"),
                file_path=file_path,
                text_content=text_content or target_evidence.get("file_name", ""),
                query=state.investigation_goal,
                parameters=target_evidence.get("extracted_metadata") or {}
            )

            try:
                output = await tool.execute(input_data)
                if not output.success:
                    task_success = False

                if output.success:
                    finding_type = tool.capabilities[0] if tool.capabilities else "GENERAL"
                    dedup_key = compute_finding_dedup_key(
                        state.case_id,
                        target_evidence.get("id") or "",
                        tool.name,
                        finding_type,
                        output.data
                    )

                    # Deduplicate before appending to state
                    if dedup_key not in existing_finding_keys:
                        existing_finding_keys.add(dedup_key)
                        total_extracted += output.findings_extracted
                        
                        # Add standardized findings to state
                        for sf in output.findings:
                            sf_dict = sf.model_dump() if hasattr(sf, "model_dump") else sf.dict()
                            sf_dict["timestamp"] = str(sf_dict["timestamp"])
                            state.standardized_findings.append(sf_dict)

                        # Maintain raw_findings compatibility
                        finding_item = {
                            "case_id": state.case_id,
                            "evidence_id": target_evidence.get("id"),
                            "tool_name": tool.name,
                            "finding_type": finding_type,
                            "content": output.data,
                            "confidence": 0.95,
                            "extracted_at": time.time(),
                            "provenance": {
                                "source_evidence": target_evidence.get("file_name"),
                                "source_tool": tool.name,
                                "task_id": task.task_id,
                                "execution_time_ms": output.execution_time_ms
                            }
                        }
                        state.raw_findings.append(finding_item)
            except Exception as err:
                logger.error(f"Error executing task {task.task_id} on '{target_evidence.get('file_name')}' with '{tool.name}': {err}")
                task_success = False

        task.status = "COMPLETED" if task_success else "FAILED"
        state.execution_logs.append(
            f"Task {task.task_id} completed by '{tool.name}' ({total_extracted} findings extracted)."
        )
        state.audit_events.append({
            "event_type": "TOOL_EXECUTED",
            "actor": tool.name,
            "details": {
                "task_id": task.task_id,
                "findings_count": total_extracted
            }
        })

    return state

async def store_findings_node(state: CaseState) -> CaseState:
    """Step 6: Persists and indexes all generated findings into state."""
    logger.info(f"[Store Findings Node] Stored {len(state.standardized_findings)} standardized findings.")
    state.execution_logs.append(f"Brain Step 6: Stored {len(state.standardized_findings)} findings across evidence.")
    return state
