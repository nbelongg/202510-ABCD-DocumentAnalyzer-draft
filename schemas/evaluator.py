"""Schemas for custom evaluator functionality"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from schemas.common import DocumentType, BaseResponse


class EvaluatorRequest(BaseModel):
    """Request model for proposal evaluation"""
    user_id: str = Field(..., min_length=1, description="User identifier")
    user_name: Optional[str] = Field(None, description="User's name")
    session_id: Optional[str] = Field(None, description="Session ID, auto-generated if not provided")
    
    # Organization context
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    org_guideline_id: Optional[str] = Field(None, description="Specific guideline to use")
    
    # Document configuration
    document_type: DocumentType = Field(default=DocumentType.PROPOSAL, description="Type of document")
    
    # Proposal input (one required)
    proposal_text_input: Optional[str] = Field(None, description="Proposal text content")
    proposal_file_data: Optional[bytes] = Field(None, description="Proposal PDF file bytes")
    
    # ToR input (one required)
    tor_text_input: Optional[str] = Field(None, description="Terms of Reference text")
    tor_file_data: Optional[bytes] = Field(None, description="ToR PDF file bytes")
    
    @validator('proposal_text_input')
    def validate_proposal_input(cls, v, values):
        """Ensure at least one proposal input is provided"""
        if not v and not values.get('proposal_file_data'):
            raise ValueError('Either proposal_text_input or proposal_file_data must be provided')
        return v
    
    @validator('tor_text_input')
    def validate_tor_input(cls, v, values):
        """Ensure at least one ToR input is provided"""
        if not v and not values.get('tor_file_data'):
            raise ValueError('Either tor_text_input or tor_file_data must be provided')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "user_name": "John Doe",
                "organization_id": "org-abc",
                "org_guideline_id": "guideline-xyz",
                "document_type": "Proposal",
                "proposal_text_input": "Our proposal aims to...",
                "tor_text_input": "The Terms of Reference require..."
            }
        }


class EvaluationSection(BaseModel):
    """Single evaluation section result"""
    section_type: str = Field(..., description="P_Internal | P_External | P_Delta")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Full analysis content")
    score: Optional[float] = Field(None, ge=0, le=100, description="Score out of 100")
    gaps: Optional[List[str]] = Field(default_factory=list, description="Identified gaps")
    strengths: Optional[List[str]] = Field(default_factory=list, description="Identified strengths")
    recommendations: Optional[List[str]] = Field(default_factory=list, description="Recommendations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "section_type": "P_Internal",
                "title": "Internal Consistency Analysis",
                "content": "The proposal demonstrates...",
                "score": 85.0,
                "gaps": ["Missing budget details"],
                "strengths": ["Clear objectives", "Strong team"],
                "recommendations": ["Add detailed budget breakdown"]
            }
        }


class EvaluatorResponse(BaseModel):
    """Response model for proposal evaluation"""
    session_id: str = Field(..., description="Evaluation session ID")
    user_id: str = Field(..., description="User identifier")
    
    # Evaluation results
    internal_analysis: EvaluationSection = Field(..., description="Proposal internal consistency")
    external_analysis: EvaluationSection = Field(..., description="Alignment with ToR")
    delta_analysis: EvaluationSection = Field(..., description="Gaps between proposal and ToR")
    
    overall_score: Optional[float] = Field(None, ge=0, le=100, description="Overall evaluation score")
    summary: Optional[str] = Field(None, description="Executive summary of evaluation")
    recommendation: Optional[str] = Field(None, description="Final recommendation")
    
    # Metadata
    processing_time_seconds: float = Field(..., description="Time taken for evaluation")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "eval-session-123",
                "user_id": "user123",
                "internal_analysis": {
                    "section_type": "P_Internal",
                    "title": "Internal Consistency",
                    "content": "Analysis...",
                    "score": 85.0
                },
                "external_analysis": {
                    "section_type": "P_External",
                    "title": "ToR Alignment",
                    "content": "Analysis...",
                    "score": 78.0
                },
                "delta_analysis": {
                    "section_type": "P_Delta",
                    "title": "Gap Analysis",
                    "content": "Analysis...",
                    "score": 82.0
                },
                "overall_score": 81.7,
                "processing_time_seconds": 45.2
            }
        }


class SessionSummary(BaseModel):
    """Summary of evaluation session"""
    session_id: str
    user_id: str
    user_name: Optional[str] = None
    document_type: Optional[str] = None
    organization_id: Optional[str] = None
    session_title: Optional[str] = None
    overall_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class EvaluatorSessionsResponse(BaseModel):
    """List of evaluation sessions"""
    sessions: List[SessionSummary]
    total_count: int


class EvaluatorFollowupRequest(BaseModel):
    """Follow-up question for evaluation"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Evaluation session ID")
    query: str = Field(..., min_length=1, max_length=2000, description="Follow-up question")
    section: Optional[str] = Field(None, description="Specific section (P_Internal, P_External, P_Delta)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "session_id": "eval-session-123",
                "query": "Can you elaborate on the budget gaps?",
                "section": "P_Delta"
            }
        }


class EvaluatorFollowupResponse(BaseModel):
    """Response to follow-up question"""
    session_id: str
    query: str
    answer: str
    section: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluatorFeedbackRequest(BaseModel):
    """Feedback on evaluation section"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Evaluation session ID")
    section: str = Field(..., description="Section type (P_Internal, P_External, P_Delta)")
    response_id: Optional[str] = Field(None, description="Specific response identifier")
    feedback: bool = Field(..., description="True for positive, False for negative")
    feedback_note: Optional[str] = Field(None, max_length=1000, description="Optional feedback text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "session_id": "eval-session-123",
                "section": "P_Internal",
                "feedback": True,
                "feedback_note": "Very thorough analysis"
            }
        }


class SessionTitleUpdateRequest(BaseModel):
    """Update session title"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Evaluation session ID")
    session_title: str = Field(..., min_length=1, max_length=500, description="New session title")


class OrganizationGuideline(BaseModel):
    """Organization-specific evaluation guidelines"""
    guideline_id: str
    organization_id: str
    guideline_name: str
    guideline_text: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrganizationGuidelinesResponse(BaseModel):
    """Response containing organization guidelines"""
    guidelines: List[OrganizationGuideline]
    organization_id: str
    total_count: int

