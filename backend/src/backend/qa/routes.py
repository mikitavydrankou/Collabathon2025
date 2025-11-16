"""
Routes for QA chatbot - multi-agent system for transaction queries.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

# Import logging setup first
from . import setup_qa_logging
setup_qa_logging()

from backend.auth.routes import get_current_user
from backend.models import User
from .chatbot_service import chatbot_service

router = APIRouter(prefix="/qa", tags=["QA Chatbot"])


class ChatMessage(BaseModel):
    """Request model for chat messages."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    session_id: str
    message: str
    tools_used: list[str]
    metadata: dict


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """
    Process a chat message with the QA chatbot.
    
    The chatbot uses multiple agents:
    - SQL Agent: for transaction queries (balance, history, amounts)
    - RAG Agent: for finding similar transactions using semantic search
    
    Args:
        chat_message: User's message and optional session_id
        current_user: Authenticated user from JWT token
        
    Returns:
        ChatResponse with assistant's reply and metadata
    """
    try:
        user_id = current_user.user_id
        
        response = chatbot_service.process_message(
            user_message=chat_message.message,
            user_id=user_id,
            session_id=chat_message.session_id
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session ID to retrieve history for
        current_user: Authenticated user from JWT token
        
    Returns:
        List of conversation messages
    """
    try:
        history = chatbot_service.get_history(session_id)
        return {"session_id": session_id, "history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Session ID to clear
        current_user: Authenticated user from JWT token
        
    Returns:
        Success confirmation
    """
    success = chatbot_service.clear_session(session_id)
    
    if success:
        return {"message": "Session cleared successfully", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/health")
async def health_check():
    """
    Check if QA chatbot is operational.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "QA Chatbot",
        "agents": ["SQL Agent", "RAG Agent"]
    }
