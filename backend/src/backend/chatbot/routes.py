"""
FastAPI routes for chatbot API.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
import os
from openai import OpenAI
import base64
import io

from .schemas import (
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    StartChatRequest,
    StartChatResponse,
)
from .service import ChatbotService
from .logger import logger

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
            button_helper_text=response.button_helper_text,
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


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using OpenAI Whisper-large.

    Args:
        audio: Audio file (mp3, wav, m4a, webm, etc.)

    Returns:
        Transcribed text
    """
    logger.info(f"🎤 API: /chatbot/transcribe called")
    logger.info(f"   Audio file: {audio.filename}, type: {audio.content_type}")
    
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Create a temporary file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = audio.filename or "audio.webm"
        
        # Transcribe using Whisper-large
        logger.info("   Calling OpenAI Whisper API...")
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",  # OpenAI's Whisper model (large-v2)
            file=audio_file,
            language="en"  # Can be changed or auto-detected
        )
        
        transcribed_text = transcript.text
        logger.info(f"   ✅ Transcription successful: '{transcribed_text[:50]}...'")
        
        return {
            "text": transcribed_text,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"   ❌ Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/ocr")
async def extract_text_from_image(image: UploadFile = File(...)):
    """
    Extract text from image using OpenAI Vision API.

    Args:
        image: Image file (jpg, png, etc.)

    Returns:
        Extracted text and description
    """
    logger.info(f"📷 API: /chatbot/ocr called")
    logger.info(f"   Image file: {image.filename}, type: {image.content_type}")
    
    try:
        # Read image file
        image_data = await image.read()
        
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Determine image type from content_type
        image_type = image.content_type or "image/jpeg"
        if not image_type.startswith("image/"):
            image_type = "image/jpeg"
        
        logger.info("   Calling OpenAI Vision API...")
        
        # Use OpenAI Vision to extract text and understand the image
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # GPT-4 Vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image. If it's a receipt, invoice, or document, extract transaction details like amount, recipient name, account number, date, and description. Return ONLY the extracted information in a clear, structured format."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        extracted_text = response.choices[0].message.content.strip()
        
        if not extracted_text:
            logger.warning("   ⚠️ No text detected in image")
            return {
                "text": "",
                "success": True,
                "message": "No text detected in the image"
            }
        
        logger.info(f"   ✅ Vision API successful: '{extracted_text[:100]}...'")
        
        return {
            "text": extracted_text,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"   ❌ Vision API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")
