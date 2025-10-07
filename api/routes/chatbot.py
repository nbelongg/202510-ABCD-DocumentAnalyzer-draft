"""Chatbot API routes"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from core.chatbot import ChatbotEngine
from db.chatbot_db import ChatbotDB
from schemas.chatbot import (
    ChatRequest,
    ChatResponse,
    SessionsResponse,
    SessionHistoryResponse,
    LastSessionResponse,
    ChatFeedbackRequest,
    ConversationMessage,
    SessionSummary,
    SourceInfo
)
from schemas.common import BaseResponse
from services.logger import get_logger
import json

logger = get_logger(__name__)
router = APIRouter()

# Initialize chatbot engine and database
chatbot_engine = ChatbotEngine()
chatbot_db = ChatbotDB()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - Get answer to user's question
    
    This endpoint:
    1. Refines the query and determines if knowledge base retrieval is needed
    2. Extracts relevant context from Pinecone if needed
    3. Generates a response using LLM
    4. Saves the conversation to database
    5. Returns response with context and sources
    """
    try:
        logger.info(
            "chat_endpoint_called",
            user_id=request.user_id,
            session_id=request.session_id,
            source=request.source
        )
        
        response = await chatbot_engine.chat(request)
        return response
        
    except Exception as e:
        logger.error("chat_endpoint_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/sessions", response_model=SessionsResponse)
async def get_sessions(
    user_id: str = Query(..., description="User identifier"),
    source: Optional[str] = Query(None, description="Filter by source (e.g., 'WA')"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of sessions")
):
    """
    Get list of user's chat sessions
    
    Returns sessions sorted by most recent first.
    """
    try:
        logger.info("get_sessions_called", user_id=user_id, source=source)
        
        sessions = chatbot_db.get_user_sessions(user_id, source, limit)
        
        # Convert to SessionSummary objects
        session_summaries = [
            SessionSummary(
                session_id=s['session_id'],
                user_id=s['user_id'],
                user_name=s.get('user_name'),
                source=s.get('source'),
                created_at=s['created_at'],
                last_message_at=s['last_message_at'],
                message_count=s['message_count']
            )
            for s in sessions
        ]
        
        return SessionsResponse(
            sessions=session_summaries,
            total_count=len(session_summaries)
        )
        
    except Exception as e:
        logger.error("get_sessions_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session_chat(session_id: str):
    """
    Get full conversation history for a session
    
    Returns all messages in the session with context and sources.
    """
    try:
        logger.info("get_session_chat_called", session_id=session_id)
        
        messages = chatbot_db.get_session_history(session_id)
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No session found with id: {session_id}"
            )
        
        # Convert to ConversationMessage objects
        conversation = []
        for msg in messages:
            # Parse JSON fields
            context_data = None
            sources = None
            
            if msg.get('context_data'):
                try:
                    if isinstance(msg['context_data'], str):
                        context_data = json.loads(msg['context_data'])
                    else:
                        context_data = msg['context_data']
                except:
                    pass
            
            if msg.get('sources'):
                try:
                    if isinstance(msg['sources'], str):
                        sources_data = json.loads(msg['sources'])
                    else:
                        sources_data = msg['sources']
                    sources = [SourceInfo(**s) for s in sources_data] if sources_data else None
                except:
                    pass
            
            conversation.append(
                ConversationMessage(
                    role=msg['role'],
                    content=msg['content'],
                    response_id=msg.get('response_id'),
                    context_data=context_data,
                    sources=sources,
                    created_at=msg['created_at']
                )
            )
        
        return SessionHistoryResponse(
            session_id=session_id,
            conversation=conversation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_session_chat_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session chat: {str(e)}"
        )


@router.get("/sessions/last", response_model=LastSessionResponse)
async def get_last_session(
    user_id: str = Query(..., description="User identifier"),
    source: Optional[str] = Query(None, description="Filter by source (e.g., 'WA')")
):
    """
    Get user's most recent chat session
    
    Returns the last session with the most recent messages.
    """
    try:
        logger.info("get_last_session_called", user_id=user_id, source=source)
        
        session_data = chatbot_db.get_user_data(user_id, source)
        
        if not session_data:
            return LastSessionResponse(
                user_id=user_id,
                message=f"No sessions found for user_id: {user_id}"
            )
        
        return LastSessionResponse(
            session_id=session_data.get('session_id'),
            user_id=user_id,
            last_message_at=session_data.get('last_message_at'),
            message_count=session_data.get('message_count', 0),
            last_query=session_data.get('last_query'),
            last_response=session_data.get('last_response')
        )
        
    except Exception as e:
        logger.error("get_last_session_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get last session: {str(e)}"
        )


@router.post("/feedback", response_model=BaseResponse)
async def submit_feedback(request: ChatFeedbackRequest):
    """
    Submit feedback on a chat response
    
    Allows users to rate responses as helpful or not helpful.
    """
    try:
        logger.info(
            "submit_feedback_called",
            user_id=request.user_id,
            response_id=request.response_id,
            feedback=request.feedback
        )
        
        chatbot_db.save_feedback(
            user_id=request.user_id,
            response_id=request.response_id,
            feedback=request.feedback,
            feedback_note=request.feedback_note
        )
        
        return BaseResponse(
            success=True,
            message="Feedback submitted successfully"
        )
        
    except Exception as e:
        logger.error("submit_feedback_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

