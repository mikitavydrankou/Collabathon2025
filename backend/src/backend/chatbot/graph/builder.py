from __future__ import annotations

from functools import partial
from typing import Callable

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END

from .state import ConversationState, Step
from .nodes import (
    main_agent_node,
    fetch_history_node,
    suggestion_node,
    formatter_node,
    validation_node,
    completion_node,
)


def _route_from_main(state: ConversationState) -> str:
    """
    Decide where to go after the main_agent_node.

    We mostly branch based on the current step that MainAgent chose:
    - INTENT_DETECTED  -> fetch history & build suggestion
    - VALIDATING       -> validate the form
    - CANCELLED/COMPLETED or anything else -> stop for now (wait for user)
    """
    if state.step == Step.INTENT_DETECTED:
        return "to_history"
    if state.step == Step.VALIDATING:
        return "to_validation"
    # For ASK_CLARIFICATION, EDITING, CANCELLED, COMPLETED, IDLE, etc.
    return "end"


def _route_from_validation(state: ConversationState) -> str:
    """
    Decide where to go after validation_node.

    - If validation passes (step == COMPLETED) -> show final summary.
    - If validation fails (step == EDITING)   -> go back to MainAgent
      so it can ask the user to correct specific fields.
    - Otherwise -> stop (shouldn't happen often).
    """
    if state.step == Step.COMPLETED:
        return "to_completion"
    if state.step == Step.EDITING:
        return "to_main"
    return "end"


def build_graph(
    llm_main: BaseChatModel,
    llm_suggestion: BaseChatModel,
    llm_formatter: BaseChatModel,
):
    """
    Build and compile the LangGraph workflow for the chat-based
    money transfer assistant.

    The graph:
      entry -> main_agent
        - if user just expressed a money-transfer intent:
             main_agent -> fetch_history -> suggestion -> formatter -> END
             (user sees suggested transfer and must react)
        - if user confirmed suggestion:
             main_agent -> validation -> (completion or back to main_agent)
        - otherwise:
             main_agent -> END  (we just show a clarifying / neutral reply)
    """

    workflow = StateGraph(ConversationState)

    # --- Nodes ---

    # Wrap nodes that need LLM instances with partials
    workflow.add_node(
        "main_agent",
        partial(main_agent_node, llm_main=llm_main),
    )
    workflow.add_node("fetch_history", fetch_history_node)
    workflow.add_node(
        "suggestion",
        partial(suggestion_node, llm_suggestion=llm_suggestion),
    )
    workflow.add_node(
        "formatter",
        partial(formatter_node, llm_formatter=llm_formatter),
    )
    workflow.add_node("validation", validation_node)
    workflow.add_node("completion", completion_node)

    # --- Entry point ---

    workflow.set_entry_point("main_agent")

    # --- Static edges ---

    # When we decide to fetch history, we always go:
    # fetch_history -> suggestion -> formatter
    workflow.add_edge("fetch_history", "suggestion")
    workflow.add_edge("suggestion", "formatter")

    # After completion we are done
    workflow.add_edge("completion", END)

    # --- Conditional edges ---

    # After main_agent we decide what to do next
    workflow.add_conditional_edges(
        "main_agent",
        _route_from_main,  # condition function
        {
            "to_history": "fetch_history",
            "to_validation": "validation",
            "end": END,
        },
    )

    # After validation we either show final summary or go back to main_agent
    workflow.add_conditional_edges(
        "validation",
        _route_from_validation,
        {
            "to_completion": "completion",
            "to_main": "main_agent",
            "end": END,
        },
    )

    # Compile into a runnable app
    app = workflow.compile()
    return app
