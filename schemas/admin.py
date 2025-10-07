"""Schemas for admin functionality"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== PROMPT MANAGEMENT ====================

class PromptType(str, Enum):
    """Types of prompts in the system"""
    ANALYZER = "analyzer"
    EVALUATOR = "evaluator"
    CHATBOT = "chatbot"
    SUMMARY = "summary"
    CUSTOM = "custom"


class PromptCreate(BaseModel):
    """Create new prompt"""
    prompt_type: PromptType = Field(..., description="Type of prompt")
    prompt_name: str = Field(..., min_length=1, max_length=255, description="Unique prompt name")
    prompt_text: str = Field(..., min_length=1, description="Full prompt template")
    description: Optional[str] = Field(None, max_length=1000, description="Prompt description")
    version: str = Field(default="1.0", description="Prompt version")
    is_active: bool = Field(default=True, description="Whether prompt is active")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_type": "analyzer",
                "prompt_name": "default_analyzer_prompt",
                "prompt_text": "Analyze the following document...",
                "description": "Default prompt for document analysis",
                "version": "1.0",
                "is_active": True
            }
        }


class PromptUpdate(BaseModel):
    """Update existing prompt"""
    prompt_text: Optional[str] = Field(None, min_length=1, description="Updated prompt template")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    version: Optional[str] = Field(None, description="Updated version")
    is_active: Optional[bool] = Field(None, description="Whether prompt is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_text": "Updated prompt text...",
                "version": "1.1",
                "is_active": True
            }
        }


class PromptResponse(BaseModel):
    """Prompt response model"""
    prompt_id: str
    prompt_type: str
    prompt_name: str
    prompt_text: str
    description: Optional[str] = None
    version: str
    is_active: bool
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_id": "prompt-123",
                "prompt_type": "analyzer",
                "prompt_name": "default_analyzer_prompt",
                "prompt_text": "Analyze the following...",
                "description": "Default analyzer prompt",
                "version": "1.0",
                "is_active": True,
                "created_at": "2025-10-06T10:00:00"
            }
        }


class PromptsListResponse(BaseModel):
    """List of prompts response"""
    prompts: List[PromptResponse]
    total_count: int
    prompt_type: Optional[str] = None


# ==================== ORGANIZATION MANAGEMENT ====================

class OrganizationCreate(BaseModel):
    """Create new organization"""
    organization_id: str = Field(..., min_length=1, max_length=255, description="Unique organization ID")
    organization_name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization settings")
    is_active: bool = Field(default=True, description="Whether organization is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org-unicef",
                "organization_name": "UNICEF",
                "description": "United Nations Children's Fund",
                "is_active": True
            }
        }


class OrganizationUpdate(BaseModel):
    """Update existing organization"""
    organization_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    """Organization response model"""
    organization_id: str
    organization_name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    guidelines_count: int = 0


class OrganizationsListResponse(BaseModel):
    """List of organizations response"""
    organizations: List[OrganizationResponse]
    total_count: int


# ==================== GUIDELINE MANAGEMENT ====================

class GuidelineCreate(BaseModel):
    """Create new organization guideline"""
    organization_id: str = Field(..., description="Organization identifier")
    guideline_name: str = Field(..., min_length=1, max_length=255, description="Guideline name")
    guideline_text: str = Field(..., min_length=1, description="Full guideline text")
    description: Optional[str] = Field(None, max_length=1000, description="Guideline description")
    is_active: bool = Field(default=True, description="Whether guideline is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org-unicef",
                "guideline_name": "Proposal Evaluation Criteria 2025",
                "guideline_text": "All proposals must...",
                "description": "Standard evaluation criteria for 2025",
                "is_active": True
            }
        }


class GuidelineUpdate(BaseModel):
    """Update existing guideline"""
    guideline_name: Optional[str] = Field(None, min_length=1, max_length=255)
    guideline_text: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class GuidelineResponse(BaseModel):
    """Guideline response model"""
    guideline_id: str
    organization_id: str
    guideline_name: str
    guideline_text: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class GuidelinesListResponse(BaseModel):
    """List of guidelines response"""
    guidelines: List[GuidelineResponse]
    organization_id: str
    total_count: int


# ==================== ANALYTICS & STATISTICS ====================

class UsageStatistics(BaseModel):
    """System usage statistics"""
    total_analyzer_sessions: int = 0
    total_chatbot_sessions: int = 0
    total_evaluator_sessions: int = 0
    total_users: int = 0
    total_organizations: int = 0
    active_prompts: int = 0
    active_guidelines: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class AnalyticsResponse(BaseModel):
    """Analytics response"""
    statistics: UsageStatistics
    top_users: List[Dict[str, Any]] = []
    top_organizations: List[Dict[str, Any]] = []
    recent_activity: List[Dict[str, Any]] = []


# ==================== API KEY MANAGEMENT ====================

class APIKeyCreate(BaseModel):
    """Create new API key"""
    user_id: str = Field(..., description="User identifier")
    key_name: str = Field(..., min_length=1, max_length=255, description="Key name/description")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    permissions: List[str] = Field(default_factory=list, description="List of permissions")
    expires_at: Optional[datetime] = Field(None, description="Key expiration date")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "key_name": "Production API Key",
                "organization_id": "org-unicef",
                "permissions": ["analyzer", "chatbot", "evaluator"],
                "expires_at": "2026-01-01T00:00:00"
            }
        }


class APIKeyResponse(BaseModel):
    """API key response model"""
    key_id: str
    user_id: str
    key_name: str
    api_key: str  # Only returned on creation
    organization_id: Optional[str] = None
    permissions: List[str] = []
    is_active: bool = True
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


class APIKeysListResponse(BaseModel):
    """List of API keys response"""
    api_keys: List[APIKeyResponse]
    total_count: int


# ==================== USER MANAGEMENT ====================

class UserCreate(BaseModel):
    """Create new user"""
    user_id: str = Field(..., min_length=1, max_length=255, description="Unique user ID")
    user_name: str = Field(..., min_length=1, max_length=255, description="User name")
    user_email: str = Field(..., description="User email")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    role: str = Field(default="user", description="User role")
    is_active: bool = Field(default=True, description="Whether user is active")
    
    @validator('user_email')
    def validate_email(cls, v):
        """Basic email validation"""
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "user_name": "John Doe",
                "user_email": "john@example.com",
                "organization_id": "org-unicef",
                "role": "user",
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """Update existing user"""
    user_name: Optional[str] = Field(None, min_length=1, max_length=255)
    user_email: Optional[str] = None
    organization_id: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model"""
    user_id: str
    user_name: str
    user_email: str
    organization_id: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UsersListResponse(BaseModel):
    """List of users response"""
    users: List[UserResponse]
    total_count: int


# ==================== BATCH OPERATIONS ====================

class BatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[str] = Field(..., min_items=1, description="List of IDs to delete")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ids": ["id1", "id2", "id3"]
            }
        }


class BatchOperationResponse(BaseModel):
    """Batch operation response"""
    success_count: int
    failure_count: int
    failed_ids: List[str] = []
    message: str

