from typing import List, Dict, Any
from app.orchestrator.state import CaseState, TaskStep
from app.tools.registry import tool_registry
from app.core.logging import logger

async def understand_goal_node(state: CaseState) -> CaseState:
    """Step 1: Analyzes the investigation goal and identifies target priorities."""
    logger.info(f"[Planner Node: Understand Goal] Goal for Case {state.case_number}: '{state.investigation_goal}'")
    state.execution_logs.append(f"Brain Step 1: Goal Analyzed -> '{state.investigation_goal}'")
    
    # Audit log
    state.audit_events.append({
        "event_type": "GOAL_UNDERSTOOD",
        "actor": "ARGUS_PLANNER_BRAIN",
        "details": {"goal": state.investigation_goal, "case_id": state.case_id}
    })
    return state

async def inspect_evidence_node(state: CaseState) -> CaseState:
    """Step 2: Scans case evidence items and file metadata."""
    logger.info(f"[Planner Node: Inspect Evidence] Inspecting {len(state.evidence_items)} evidence files.")
    file_types = list(set(ev.get("file_type", "UNKNOWN") for ev in state.evidence_items))
    state.execution_logs.append(f"Brain Step 2: Evidence Inspected -> {len(state.evidence_items)} items (Types: {file_types})")
    
    state.audit_events.append({
        "event_type": "EVIDENCE_INSPECTED",
        "actor": "ARGUS_PLANNER_BRAIN",
        "details": {"total_evidence": len(state.evidence_items), "types": file_types}
    })
    return state

async def plan_tasks_node(state: CaseState) -> CaseState:
    """Step 3 & 4: Decomposes goal into initial tasks and matches capabilities from registry."""
    logger.info(f"[Planner Node: Plan Tasks] Decomposing tasks for Case ID: {state.case_id}")
    
    existing_keys = set((t.tool_name, t.evidence_id) for t in state.tasks)
    tasks: List[TaskStep] = list(state.tasks)
    task_counter = len(tasks) + 1

    for item in state.evidence_items:
        file_type = item.get("file_type", "").upper()
        file_name = item.get("file_name", "evidence")
        evidence_id = item.get("id")

        # Helper to append unique task step
        def add_task_if_unique(tool_obj, obj_desc):
            nonlocal task_counter
            key = (tool_obj.name, evidence_id)
            if key not in existing_keys:
                existing_keys.add(key)
                tasks.append(TaskStep(
                    task_id=f"TASK-{task_counter:03d}",
                    tool_name=tool_obj.name,
                    objective=obj_desc,
                    evidence_id=evidence_id,
                    file_name=file_name
                ))
                task_counter += 1

        # 1. Metadata Extraction Capability
        for tool in tool_registry.find_by_capability("metadata_extraction"):
            add_task_if_unique(tool, f"Extract metadata and GPS coordinates from '{file_name}' using {tool.name}")

        # 2. OCR Capability
        if file_type in ["IMAGE", "DOCUMENT", "FILE"]:
            ocr_tools = tool_registry.find_by_capability("ocr", input_type=file_type) or tool_registry.find_by_capability("ocr")
            for tool in ocr_tools:
                add_task_if_unique(tool, f"Perform OCR text extraction on '{file_name}' using {tool.name}")

        # 3. Entity Extraction Capability
        for tool in tool_registry.find_by_capability("entity_extraction"):
            add_task_if_unique(tool, f"Extract handles, contact details, and entities from '{file_name}' using {tool.name}")

        # 4. Vector/Evidence Search Capability
        search_tools = tool_registry.find_by_capability("evidence_search") or tool_registry.find_by_capability("vector_embedding")
        for tool in search_tools:
            add_task_if_unique(tool, f"Perform evidence search indexing on '{file_name}' using {tool.name}")

    newly_planned = len(tasks) - len(state.tasks)
    state.tasks = tasks
    state.execution_logs.append(f"Brain Step 3: Planned {newly_planned} new tasks (Total: {len(tasks)} tasks).")
    state.audit_events.append({
        "event_type": "TASKS_PLANNED",
        "actor": "ARGUS_PLANNER_BRAIN",
        "details": {"planned_tasks": [t.task_id for t in tasks]}
    })
    return state

async def evaluate_findings_node(state: CaseState) -> CaseState:
    """Step 7 & 8: Evaluates extracted findings and decides if follow-up investigation is warranted."""
    state.iteration_count += 1
    logger.info(f"[Planner Node: Evaluate Findings] Iteration {state.iteration_count}/{state.max_iterations} | Findings Count: {len(state.raw_findings)}")

    timeline_tools = tool_registry.find_by_capability("timeline_extraction")
    timeline_tool_names = set(t.name for t in timeline_tools)
    
    # Check if timeline extraction task has ALREADY been planned or executed
    has_planned_timeline = any(t.tool_name in timeline_tool_names for t in state.tasks)

    # Inspect findings for un-analyzed OCR text
    has_unprocessed_text = False
    if not has_planned_timeline:
        for f in state.raw_findings:
            content = f.get("content", {})
            if "extracted_text" in content and len(content.get("extracted_text", "")) > 20:
                has_unprocessed_text = True
                break

    # Hard guard: Maximum iteration limit + check if timeline extraction already planned/executed
    if has_unprocessed_text and state.iteration_count < state.max_iterations:
        state.needs_additional_investigation = True
        state.execution_logs.append(f"Brain Step 7: Findings Evaluation -> Additional follow-up investigation JUSTIFIED (Iteration {state.iteration_count}).")
    else:
        state.needs_additional_investigation = False
        state.execution_logs.append(f"Brain Step 7: Findings Evaluation -> Findings sufficient. Proceeding to correlation.")

    state.audit_events.append({
        "event_type": "FINDINGS_EVALUATED",
        "actor": "ARGUS_PLANNER_BRAIN",
        "details": {
            "iteration": state.iteration_count,
            "needs_more": state.needs_additional_investigation,
            "total_findings": len(state.raw_findings)
        }
    })
    return state

async def plan_additional_tasks_node(state: CaseState) -> CaseState:
    """Step 9 & 10: Plans additional follow-up tasks when justified."""
    logger.info(f"[Planner Node: Plan Additional Tasks] Planning follow-up tasks for Iteration {state.iteration_count}")

    additional_tasks: List[TaskStep] = []
    existing_keys = set((t.tool_name, t.evidence_id) for t in state.tasks)
    task_counter = len(state.tasks) + 1

    timeline_tools = tool_registry.find_by_capability("timeline_extraction")
    for tool in timeline_tools:
        for item in state.evidence_items:
            key = (tool.name, item.get("id"))
            if key not in existing_keys:
                existing_keys.add(key)
                additional_tasks.append(TaskStep(
                    task_id=f"TASK-{task_counter:03d}",
                    tool_name=tool.name,
                    objective=f"Extract chronological timeline events from '{item.get('file_name', 'evidence')}' using {tool.name}",
                    evidence_id=item.get("id"),
                    file_name=item.get("file_name")
                ))
                task_counter += 1

    state.tasks.extend(additional_tasks)
    state.execution_logs.append(f"Brain Step 9: Planned {len(additional_tasks)} additional follow-up tasks.")
    state.audit_events.append({
        "event_type": "ADDITIONAL_TASKS_PLANNED",
        "actor": "ARGUS_PLANNER_BRAIN",
        "details": {"additional_tasks": [t.task_id for t in additional_tasks]}
    })
    return state

# Alias for backward compatibility
planner_node = plan_tasks_node
