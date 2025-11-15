"""
FastAPI routes for chatbot API.
"""

from fastapi import APIRouter, HTTPException

from .schemas import (
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    StartChatRequest,
    StartChatResponse,
)
from .service import ChatbotService
from .logger import logger

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/start", response_model=StartChatResponse)
def start_chat(request: StartChatRequest):
    """
    Start a new chatbot conversation.

    Args:
        request: Contains user_id

    Returns:
        Session ID and initial message
    """
    logger.info(f"🚀 API: /chatbot/start called for user {request.user_id}")
    try:
        response = ChatbotService.start_conversation(request.user_id)
        logger.info(f"   ✅ Session created: {response.session_id}")
        return StartChatResponse(
            session_id=response.session_id,
            message=response.message,
            buttons=response.buttons or [],
        )
    except Exception as e:
        logger.error(f"   ❌ Error starting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start chat: {str(e)}")


@router.post("/message", response_model=ChatbotMessageResponse)
def send_message(request: ChatbotMessageRequest):
    """
    Send a message or action to the chatbot.

    Args:
        request: Contains session_id, user_id, message (optional), action (optional)

    Returns:
        Chatbot response with next message and options
    """
    logger.info(f"💬 API: /chatbot/message called")
    logger.info(f"   Session ID: {request.session_id or 'None (new session)'}")
    logger.info(f"   User ID: {request.user_id}")
    logger.info(f"   Message: {request.message or 'None'}")
    logger.info(f"   Action: {request.action or 'None'}")
    
    try:
        # If no session_id, start new conversation
        if not request.session_id:
            logger.info("   Starting new conversation (no session_id provided)")
            response = ChatbotService.start_conversation(request.user_id)
            return response

        # Handle message
        response = ChatbotService.handle_message(
            session_id=request.session_id,
            message=request.message,
            action=request.action,
        )
        logger.info(f"   ✅ Response stage: {response.stage}")
        return response

    except Exception as e:
        logger.error(f"   ❌ Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}", response_model=ChatbotMessageResponse)
def get_session(session_id: str):
    """
    Get current session state.

    Args:
        session_id: Session ID

    Returns:
        Current chatbot state
    """
    state = ChatbotService.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    return ChatbotMessageResponse(
        session_id=state.session_id,
        stage=state.stage,
        message="Current session state",
        buttons=None,
        transaction_data=state.transaction_data,
    )
