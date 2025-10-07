"""Schemas for document analyzer functionality"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from schemas.common import DocumentType, UserRole, BaseResponse


class PromptLabel(BaseModel):
    """Prompt configuration label"""
    label: str = Field(..., description="Prompt label (e.g., P1, P2, P3)")
    enabled: bool = True


class AnalyzerRequest(BaseModel):
    """Request model for document analysis"""
    user_id: str = Field(..., min_length=1)
    user_name: Optional[str] = None
    session_id: Optional[str] = None
    
    # Document input (one of these required)
    text_input: Optional[str] = Field(None, max_length=100000)
    file_data: Optional[bytes] = None
    
    # Analysis configuration
    document_type: DocumentType = DocumentType.PROGRAM_DESIGN
    user_role: UserRole = UserRole.IMPACT_CONSULTANT
    organization_id: Optional[str] = None
    
    # Prompt selection
    prompt_labels: List[str] = Field(
        default=["P1", "P2", "P3", "P4", "P5"],
        description="Which analysis prompts to run"
    )
    showcase_items: int = Field(default=10, ge=1, le=50)
    
    @validator("text_input", "file_data")
    def check_input_provided(cls, v, values):
        """Ensure at least one input method is provided"""
        if not v and "text_input" not in values and "file_data" not in values:
            raise ValueError("Either text_input or file_data must be provided")
        return v


class AnalyzerSectionResult(BaseModel):
    """Result from a single analysis section"""
    section_id: str
    label: str
    title: str
    content: str
    score: Optional[float] = None
    metadata: Optional[Dict] = None


class AnalyzerResponse(BaseResponse):
    """Response model for document analysis"""
    session_id: str
    user_id: str
    document_type: str
    
    # Analysis results
    sections: List[AnalyzerSectionResult]
    summary: Optional[str] = None
    
    # Metadata
    processing_time_seconds: float
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalyzerSessionsResponse(BaseModel):
    """List of user's analysis sessions"""
    sessions: List[dict]
    total_count: int


class AnalyzerFollowupRequest(BaseModel):
    """Request for follow-up analysis question"""
    user_id: str
    session_id: str
    query: str = Field(..., min_length=1, max_length=2000)
    section: Optional[str] = None


class AnalyzerFollowupResponse(BaseResponse):
    """Response for follow-up question"""
    answer: str
    section: Optional[str] = None
    related_sections: Optional[List[str]] = None


class AnalyzerFeedbackRequest(BaseModel):
    """Feedback on analysis section"""
    user_id: str
    session_id: str
    section: str
    feedback: bool = Field(..., description="Thumbs up/down")
    feedback_note: Optional[str] = None
    response_id: Optional[str] = None


class PromptConfiguration(BaseModel):
    """Prompt configuration for analysis"""
    prompt_id: str
    prompt_label: str
    document_type: DocumentType
    base_prompt: str
    customization_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    
    # Prompt metadata
    temperature: float = 0.7
    max_tokens: int = 4000
    use_corpus: bool = True
    corpus_id: Optional[str] = None
    num_examples: int = 5
    
    created_at: datetime
    updated_at: datetime

