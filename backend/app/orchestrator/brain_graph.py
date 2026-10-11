from app.orchestrator.state import CaseState
from app.orchestrator.planner import (
    understand_goal_node,
    inspect_evidence_node,
    plan_tasks_node,
    evaluate_findings_node,
    plan_additional_tasks_node
)
from app.orchestrator.executor import executor_node, store_findings_node
from app.orchestrator.correlator import correlator_node
from app.orchestrator.lead_generator import lead_generator_node, human_review_node
from app.core.logging import logger

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    StateGraph = None
    END = None
    HAS_LANGGRAPH = False

class FallbackGraph:
    """Deterministic fallback pipeline executing the exact LangGraph state machine loop."""
    async def ainvoke(self, input_state_dict: dict) -> dict:
        state = CaseState(**input_state_dict)

        # 1. Understand Goal
        state = await understand_goal_node(state)
        # 2. Inspect Evidence
        state = await inspect_evidence_node(state)
        # 3. Plan Tasks & Match Tools
        state = await plan_tasks_node(state)
        
        # 4. Execute & Store Loop with Evaluation
        while True:
            state = await executor_node(state)
            state = await store_findings_node(state)
            state = await evaluate_findings_node(state)

            if state.needs_additional_investigation and state.iteration_count < state.max_iterations:
                state = await plan_additional_tasks_node(state)
            else:
                break

        # 5. Correlate Findings & Knowledge Graph Construction
        state = await correlator_node(state)
        # 6. Generate Candidate Leads
        state = await lead_generator_node(state)
        # 7. Human Review Preparation
        state = await human_review_node(state)

        return state.model_dump() if hasattr(state, "model_dump") else state.dict()

def should_continue(state: CaseState) -> str:
    """Conditional edge decision function for LangGraph state machine."""
    if state.needs_additional_investigation and state.iteration_count < state.max_iterations:
        return "plan_additional_tasks"
    return "correlate_findings"

def build_investigation_graph():
    """Builds the full LangGraph state machine pipeline for ARGUS investigation orchestration."""
    if not HAS_LANGGRAPH:
        logger.info("LangGraph package not installed. Using deterministic state machine fallback.")
        return FallbackGraph()

    builder = StateGraph(CaseState)

    # Add Nodes
    builder.add_node("understand_goal", understand_goal_node)
    builder.add_node("inspect_evidence", inspect_evidence_node)
    builder.add_node("plan_tasks", plan_tasks_node)
    builder.add_node("execute_tasks", executor_node)
    builder.add_node("store_findings", store_findings_node)
    builder.add_node("evaluate_findings", evaluate_findings_node)
    builder.add_node("plan_additional_tasks", plan_additional_tasks_node)
    builder.add_node("correlate_findings", correlator_node)
    builder.add_node("generate_leads", lead_generator_node)
    builder.add_node("human_review", human_review_node)

    # Set Entry Point
    builder.set_entry_point("understand_goal")

    # Add Linear Edges
    builder.add_edge("understand_goal", "inspect_evidence")
    builder.add_edge("inspect_evidence", "plan_tasks")
    builder.add_edge("plan_tasks", "execute_tasks")
    builder.add_edge("execute_tasks", "store_findings")
    builder.add_edge("store_findings", "evaluate_findings")

    # Add Conditional Edge for Iterative Evaluation Loop
    builder.add_conditional_edges(
        "evaluate_findings",
        should_continue,
        {
            "plan_additional_tasks": "plan_additional_tasks",
            "correlate_findings": "correlate_findings"
        }
    )

    builder.add_edge("plan_additional_tasks", "execute_tasks")
    builder.add_edge("correlate_findings", "generate_leads")
    builder.add_edge("generate_leads", "human_review")
    builder.add_edge("human_review", END)

    graph = builder.compile()
    logger.info("LangGraph Brain Orchestrator state machine compiled successfully.")
    return graph

investigation_graph = build_investigation_graph()
