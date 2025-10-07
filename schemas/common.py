"""Common schemas used across the application"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum
from datetime import datetime


class DocumentType(str, Enum):
    """Types of documents that can be analyzed"""
    PROGRAM_DESIGN = "Program_Design_Document"
    POLICY_DOCUMENT = "Policy_Document"
    PROPOSAL = "Proposal"
    REPORT = "Report"
    GUIDELINE = "Guideline"
    OTHER = "Other"


class UserRole(str, Enum):
    """User roles for context-specific analysis"""
    IMPACT_CONSULTANT = "Impact_Consultant"
    PROGRAM_MANAGER = "Program_Manager"
    POLICY_ADVISOR = "Policy_Advisor"
    EVALUATOR = "Evaluator"
    RESEARCHER = "Researcher"


class FileSource(BaseModel):
    """Source file information"""
    filename: str
    size_bytes: int
    content_type: str
    s3_url: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class BaseResponse(BaseModel):
    """Base response model with common fields"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    database: str
    services: dict

