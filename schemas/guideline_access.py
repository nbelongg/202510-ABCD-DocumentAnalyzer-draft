"""
Schemas for guideline access control and CSV sync
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class VisibilityScope(str, Enum):
    """Guideline visibility scope"""
    ORGANIZATION = "organization"  # Only owning organization
    PUBLIC_MAPPED = "public_mapped"  # Admin-controlled sharing
    UNIVERSAL = "universal"  # Available to all


class AccessType(str, Enum):
    """Type of guideline access"""
    ORGANIZATION = "organization"  # Own org's guidelines
    PUBLIC_MAPPED = "public_mapped"  # Shared public guidelines
    UNIVERSAL = "universal"  # Universal public guidelines


# ==================== GUIDELINE ACCESS ====================

class GuidelineAccessRequest(BaseModel):
    """Request to access guidelines"""
    user_email: str = Field(..., description="User email address")
    organization_id: Optional[str] = Field(None, description="Specific organization")
    guideline_ids: Optional[List[str]] = Field(None, description="Specific guideline IDs")
    
    @validator('user_email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()


class GuidelineWithAccess(BaseModel):
    """Guideline with access type information"""
    guideline_id: str
    organization_id: str
    guideline_name: str
    guideline_text: str
    description: Optional[str] = None
    is_active: bool
    is_public: bool
    visibility_scope: VisibilityScope
    access_type: AccessType
    created_at: datetime
    updated_at: Optional[datetime] = None


class GuidelineAccessResponse(BaseModel):
    """Response with accessible guidelines"""
    guidelines: List[GuidelineWithAccess]
    user_organization_id: Optional[str] = None
    total_available: int
    access_controlled: bool = True
    breakdown: Dict[str, int] = Field(
        default_factory=lambda: {
            "organization": 0,
            "public_mapped": 0,
            "universal": 0
        }
    )


# ==================== ORGANIZATION MANAGEMENT ====================

class OrganizationDomainMapping(BaseModel):
    """Organization email domain configuration"""
    organization_id: str
    organization_name: str
    email_domains: List[str] = Field(..., description="List of email domains")
    is_active: bool = True
    
    @validator('email_domains')
    def validate_domains(cls, v):
        """Ensure domains don't contain @ symbol"""
        for domain in v:
            if '@' in domain:
                raise ValueError(f"Domain '{domain}' should not contain @ symbol")
        return [d.lower() for d in v]


# ==================== GUIDELINE MAPPING ====================

class GuidelineAccessMapping(BaseModel):
    """Mapping between organization and guideline"""
    organization_id: str = Field(..., description="Organization to grant access")
    guideline_id: str = Field(..., description="Public guideline ID")
    granted_by: str = Field(..., description="Admin user granting access")
    notes: Optional[str] = Field(None, description="Notes about this mapping")


class GuidelineAccessMappingResponse(BaseModel):
    """Response for guideline access mapping"""
    id: int
    organization_id: str
    guideline_id: str
    guideline_name: str
    granted_by: str
    granted_at: datetime
    notes: Optional[str] = None


class BulkGuidelineAccessRequest(BaseModel):
    """Bulk grant access to multiple organizations"""
    guideline_id: str = Field(..., description="Guideline to share")
    organization_ids: List[str] = Field(..., min_items=1, description="Organizations to grant access")
    granted_by: str = Field(..., description="Admin user")
    notes: Optional[str] = None


class GuidelineVisibilityUpdate(BaseModel):
    """Update guideline visibility settings"""
    is_public: bool
    visibility_scope: VisibilityScope = Field(..., description="Visibility scope")


# ==================== CSV SYNC ====================

class CSVValidationError(BaseModel):
    """CSV validation error"""
    line_number: int
    field: str
    error_message: str


class SyncPreview(BaseModel):
    """Preview of changes before applying"""
    organizations_to_add: List[Dict[str, Any]] = []
    organizations_to_update: List[Dict[str, Any]] = []
    organizations_to_deactivate: List[Dict[str, Any]] = []
    
    guidelines_to_add: List[Dict[str, Any]] = []
    guidelines_to_update: List[Dict[str, Any]] = []
    guidelines_to_deactivate: List[Dict[str, Any]] = []
    
    access_to_add: List[Dict[str, Any]] = []
    access_to_remove: List[Dict[str, Any]] = []
    
    total_changes: int = 0
    has_errors: bool = False
    errors: List[str] = []
    warnings: List[str] = []


class SyncResult(BaseModel):
    """Result of applying sync"""
    success: bool
    changes_applied: int
    organizations_synced: int
    guidelines_synced: int
    access_mappings_synced: int
    errors: List[str] = []
    warnings: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== AUDIT LOG ====================

class GuidelineAccessAudit(BaseModel):
    """Audit log entry"""
    user_id: str
    user_email: str
    organization_id: str
    guideline_id: str
    access_granted: bool
    access_reason: str
    session_id: Optional[str] = None
    accessed_at: datetime = Field(default_factory=datetime.utcnow)


class AccessAuditQuery(BaseModel):
    """Query parameters for access audit logs"""
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    guideline_id: Optional[str] = None
    access_granted: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)


# ==================== EXPORT/IMPORT ====================

class OrganizationCSVRow(BaseModel):
    """Single row in organizations CSV"""
    organization_id: str
    organization_name: str
    email_domains: str  # Comma-separated
    is_active: str = "TRUE"  # TRUE/FALSE
    notes: Optional[str] = None


class GuidelineCSVRow(BaseModel):
    """Single row in guidelines CSV"""
    guideline_id: str
    guideline_name: str
    organization_id: str
    visibility_scope: str
    is_active: str = "TRUE"  # TRUE/FALSE
    description: Optional[str] = None


class GuidelineAccessCSVRow(BaseModel):
    """Single row in guideline access CSV"""
    organization_id: str
    guideline_id: str
    granted_by: Optional[str] = "admin@abcd.org"
    notes: Optional[str] = None


# ==================== ADMIN RESPONSES ====================

class AccessMappingListResponse(BaseModel):
    """List of access mappings"""
    mappings: List[Dict[str, Any]]
    total_count: int
    filtered_by: Optional[Dict[str, str]] = None


class PublicGuidelineListResponse(BaseModel):
    """List of public guidelines"""
    guidelines: List[Dict[str, Any]]
    total_count: int
    visibility_scope: Optional[str] = None


class BulkOperationResponse(BaseModel):
    """Result of bulk operation"""
    success: bool
    message: str
    success_count: int
    failure_count: int
    failed_items: List[str] = []
    details: Optional[Dict[str, Any]] = None
