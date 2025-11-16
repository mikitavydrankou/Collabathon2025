from typing import Dict, Any, Optional
import logging

# Import logging setup first
from . import setup_qa_logging
setup_qa_logging()

from .agents.main_agent import MainAgent
from .memory import conversation_memory

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChatbotService:
    """Service for handling chatbot conversations."""
    
    def __init__(self):
        self.main_agent = MainAgent()
        self.memory = conversation_memory
    
    def process_message(
        self, 
        user_message: str, 
        user_id: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message and return response.
        
        Args:
            user_message: User's input message
            user_id: User ID
            session_id: Existing session ID or None for new session
            
        Returns:
            Dict with response and session info
        """
        # Create or get session
        if not session_id or not self.memory.session_exists(session_id):
            session_id = self.memory.create_session(user_id)
        
        # Get conversation context
        context = self.memory.get_context(session_id)
        
        # Add user message to history
        self.memory.add_message(session_id, "user", user_message)
        
        logger.info(f"\n{'#'*100}")
        logger.info(f"# QA CHATBOT - NEW REQUEST")
        logger.info(f"{'#'*100}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message: {user_message}")
        logger.info(f"{'#'*100}\n")
        
        # Process with main agent
        agent_response = self.main_agent.process_query(
            user_message, 
            user_id, 
            context
        )
        
        logger.info(f"\n{'#'*100}")
        logger.info(f"# QA CHATBOT - REQUEST COMPLETE")
        logger.info(f"{'#'*100}")
        logger.info(f"Success: {agent_response.get('success')}")
        logger.info(f"Message length: {len(agent_response.get('message', ''))}")
        logger.info(f"{'#'*100}\n\n")
        
        # Extract response message
        response_message = agent_response.get("message", ".")
        tools_used = agent_response.get("tools_used", [])
        
        # Add assistant response to history
        tool_label = ", ".join(tools_used) if tools_used else None
        self.memory.add_message(session_id, "assistant", response_message, tool_label)
        
        return {
            "session_id": session_id,
            "message": response_message,
            "tools_used": tools_used,
            "metadata": agent_response.get("metadata", {})
        }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        if self.memory.session_exists(session_id):
            self.memory.clear_session(session_id)
            return True
        return False
    
    def get_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        messages = self.memory.get_history(session_id)
        return [msg.to_dict() for msg in messages]


chatbot_service = ChatbotService()