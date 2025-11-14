from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["user", "assistant", "system"]


class ChatMessage(BaseModel):
    """
    Generic chat message used in ConversationState.chat_history.
    Compatible with typical LLM APIs.
    """

    role: Role
    content: str
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Optional timestamp; if None, can be filled in by caller.",
    )
