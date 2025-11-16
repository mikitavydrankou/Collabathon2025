from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4


class Message:
    """Represents a single message in conversation."""
    
    def __init__(self, role: str, content: str, tool_used: Optional[str] = None):
        self.role = role
        self.content = content
        self.tool_used = tool_used
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "tool_used": self.tool_used,
            "timestamp": self.timestamp.isoformat()
        }


class ConversationMemory:
    """Manages conversation history for chatbot sessions."""
    
    def __init__(self, max_messages: int = 10):
        self._sessions: Dict[str, List[Message]] = {}
        self._max_messages = max_messages
    
    def create_session(self, user_id: int) -> str:
        """Create a new conversation session."""
        session_id = str(uuid4())
        self._sessions[session_id] = []
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, tool_used: Optional[str] = None):
        """Add a message to session history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        message = Message(role, content, tool_used)
        self._sessions[session_id].append(message)
        
        # Keep only last N messages
        if len(self._sessions[session_id]) > self._max_messages:
            self._sessions[session_id] = self._sessions[session_id][-self._max_messages:]
    
    def get_history(self, session_id: str) -> List[Message]:
        """Get conversation history for a session."""
        return self._sessions.get(session_id, [])
    
    def get_context(self, session_id: str) -> str:
        """Get formatted conversation context for LLM."""
        messages = self.get_history(session_id)
        if not messages:
            return ""
        
        context_lines = []
        for msg in messages:
            context_lines.append(f"{msg.role.upper()}: {msg.content}")
        
        return "\n".join(context_lines)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self._sessions
    
    def clear_session(self, session_id: str):
        """Clear session history."""
        if session_id in self._sessions:
            del self._sessions[session_id]


conversation_memory = ConversationMemory(max_messages=10)