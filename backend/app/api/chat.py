import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.services.chat_service import ChatService
from app.core.logging import log_exception

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    llm_provider: str
    selected_tools: List[str] = []

class ChatResponse(BaseModel):
    response: str
    provider_used: str
    tools_used: List[str] = []

def get_chat_service() -> ChatService:
    return ChatService()

def get_user_email(request: Request) -> str:
    return getattr(request.state, 'user_email', 'unknown')

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
    user_email: str = Depends(get_user_email)
):
    try:
        if not chat_message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not chat_message.llm_provider:
            raise HTTPException(status_code=400, detail="LLM provider must be specified")

        response = await chat_service.process_message(
            chat_message.message,
            chat_message.llm_provider,
            chat_message.selected_tools,
            user_email
        )
        
        return ChatResponse(
            response=response['content'],
            provider_used=response['provider'],
            tools_used=response['tools_used']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_exception(logger, e, "processing chat message")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/history")
async def get_chat_history(
    request: Request,
    user_email: str = Depends(get_user_email),
    limit: int = 50
):
    try:
        chat_service = ChatService()
        history = await chat_service.get_chat_history(user_email, limit)
        return {"history": history}
    except Exception as e:
        log_exception(logger, e, "retrieving chat history")
        raise HTTPException(status_code=500, detail="Internal server error")