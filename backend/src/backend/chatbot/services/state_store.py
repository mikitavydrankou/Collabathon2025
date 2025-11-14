from __future__ import annotations

from typing import Dict

from ..graph import ConversationState, Step


# Very simple in-memory store: session_id -> ConversationState
_STATE_STORE: Dict[str, ConversationState] = {}


def get_state(session_id: str, user_id: str) -> ConversationState:
    """
    Get existing ConversationState for a given session_id,
    or create a new one if it doesn't exist yet.
    """
    if session_id in _STATE_STORE:
        return _STATE_STORE[session_id]

    # Create a fresh state for this session
    state = ConversationState(
        user_id=user_id,
        session_id=session_id,
        step=Step.IDLE,
    )
    _STATE_STORE[session_id] = state
    return state


def save_state(session_id: str, state: ConversationState) -> None:
    """
    Persist updated ConversationState back to the in-memory store.
    """
    _STATE_STORE[session_id] = state


def clear_state(session_id: str) -> None:
    """
    Remove state for a given session_id (useful for tests / manual reset).
    """
    _STATE_STORE.pop(session_id, None)


def clear_all_states() -> None:
    """
    Remove all stored states.
    Useful for development / testing; not for production.
    """
    _STATE_STORE.clear()