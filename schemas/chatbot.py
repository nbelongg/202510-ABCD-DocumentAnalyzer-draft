"""Schemas for chatbot functionality"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from schemas.common import BaseResponse


class LLMModel(str, Enum):
    """Available LLM models for chat"""
    GPT_4 = "gpt-4"
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"


class ContextInfo(BaseModel):
    """Context information from knowledge base"""
    pdf_name: str = Field(..., description="Source PDF name")
    pdf_context: str = Field(..., description="Relevant text context")
    score: Optional[float] = Field(None, description="Relevance score")


class SourceInfo(BaseModel):
    """Source document information"""
    sno: Optional[str] = Field(None, description="Serial number")
    title: Optional[str] = Field(None, description="Document title")
    author_organization: Optional[str] = Field(None, description="Author or organization")
    publication_year: Optional[str] = Field(None, description="Publication year")
    link: Optional[str] = Field(None, description="Document link")
    pdf_title: str = Field(..., description="PDF filename")


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request for chatbot response"""
    user_id: str = Field(..., min_length=1)
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    session_id: Optional[str] = Field(None, description="Session ID, will be created if not provided")
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    model: LLMModel = Field(default=LLMModel.GPT_4O, description="LLM model to use")
    source: Optional[str] = Field(None, description="Source platform (e.g., 'WA' for WhatsApp)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "user_name": "John Doe",
                "question": "What are the key principles of impact evaluation?",
                "model": "gpt-4o",
                "source": "WA"
            }
        }


class ChatResponse(BaseModel):
    """Response from chatbot"""
    user_id: str
    session_id: str
    response: str = Field(..., description="Chatbot's answer")
    response_id: str = Field(..., description="Unique response identifier")
    contextInfo: List[ContextInfo] = Field(default_factory=list, description="Context used from knowledge base")
    sources: List[SourceInfo] = Field(default_factory=list, description="Source documents")
    within_knowledge_base: bool = Field(True, description="Whether answer is from knowledge base")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "session_id": "session-abc",
                "response": "Impact evaluation involves...",
                "response_id": "resp-xyz",
                "contextInfo": [],
                "sources": [],
                "within_knowledge_base": True
            }
        }


class SessionSummary(BaseModel):
    """Summary of a chat session"""
    session_id: str
    user_id: str
    user_name: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    last_message_at: datetime
    message_count: int = 0


class SessionsResponse(BaseModel):
    """Response containing list of sessions"""
    sessions: List[SessionSummary]
    total_count: int


class ConversationMessage(BaseModel):
    """Single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    response_id: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    sources: Optional[List[SourceInfo]] = None
    created_at: datetime


class SessionHistoryResponse(BaseModel):
    """Chat history for a session"""
    session_id: str
    conversation: List[ConversationMessage]
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-abc",
                "conversation": [
                    {"role": "user", "content": "What is impact evaluation?"},
                    {"role": "assistant", "content": "Impact evaluation is..."}
                ]
            }
        }


class LastSessionResponse(BaseModel):
    """Response for last session query"""
    session_id: Optional[str] = None
    user_id: str
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    last_query: Optional[str] = None
    last_response: Optional[str] = None
    message: Optional[str] = Field(None, description="Info message if no session found")


class ChatFeedbackRequest(BaseModel):
    """Feedback on chat response"""
    user_id: str
    response_id: str
    feedback: bool = Field(..., description="True for positive, False for negative")
    feedback_note: Optional[str] = Field(None, max_length=1000, description="Optional feedback text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "response_id": "resp-xyz",
                "feedback": True,
                "feedback_note": "Very helpful answer!"
            }
        }

