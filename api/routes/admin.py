"""Admin API routes for prompts, organizations, users, and system management"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from datetime import datetime
from db.prompts_db import PromptsDB
from db.admin_db import OrganizationsDB, GuidelinesDB, UsersDB, APIKeysDB
from schemas.admin import (
    PromptCreate, PromptUpdate, PromptResponse, PromptsListResponse,
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, OrganizationsListResponse,
    GuidelineCreate, GuidelineUpdate, GuidelineResponse, GuidelinesListResponse,
    UserCreate, UserUpdate, UserResponse, UsersListResponse,
    APIKeyCreate, APIKeyResponse, APIKeysListResponse,
    BatchDeleteRequest, BatchOperationResponse,
    PromptType
)
from schemas.common import BaseResponse
from services.logger import get_logger
from services.exceptions import NotFoundError, DatabaseError

logger = get_logger(__name__)
router = APIRouter()

# Initialize database classes
prompts_db = PromptsDB()
organizations_db = OrganizationsDB()
guidelines_db = GuidelinesDB()
users_db = UsersDB()
api_keys_db = APIKeysDB()


# ==================== PROMPT MANAGEMENT ====================

@router.post("/prompts", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(request: PromptCreate):
    """Create new prompt"""
    try:
        logger.info("create_prompt_called", prompt_name=request.prompt_name)
        
        prompt_id = prompts_db.create_prompt(
            prompt_type=request.prompt_type.value,
            prompt_name=request.prompt_name,
            prompt_text=request.prompt_text,
            description=request.description,
            version=request.version,
            is_active=request.is_active,
            metadata=request.metadata
        )
        
        prompt = prompts_db.get_prompt_by_id(prompt_id)
        return PromptResponse(**prompt)
        
    except Exception as e:
        logger.error("create_prompt_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}"
        )


@router.get("/prompts", response_model=PromptsListResponse)
async def list_prompts(
    prompt_type: Optional[PromptType] = Query(None, description="Filter by prompt type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all prompts with optional filtering"""
    try:
        logger.info("list_prompts_called", prompt_type=prompt_type)
        
        prompts = prompts_db.list_prompts(
            prompt_type=prompt_type.value if prompt_type else None,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        prompt_responses = [PromptResponse(**p) for p in prompts]
        
        return PromptsListResponse(
            prompts=prompt_responses,
            total_count=len(prompt_responses),
            prompt_type=prompt_type.value if prompt_type else None
        )
        
    except Exception as e:
        logger.error("list_prompts_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """Get specific prompt by ID"""
    try:
        prompt = prompts_db.get_prompt_by_id(prompt_id)
        return PromptResponse(**prompt)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_prompt_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}"
        )


@router.put("/prompts/{prompt_id}", response_model=BaseResponse)
async def update_prompt(prompt_id: str, request: PromptUpdate):
    """Update prompt configuration"""
    try:
        logger.info("update_prompt_called", prompt_id=prompt_id)
        
        prompts_db.update_prompt_by_id(
            prompt_id=prompt_id,
            prompt_text=request.prompt_text,
            description=request.description,
            version=request.version,
            is_active=request.is_active,
            metadata=request.metadata
        )
        
        return BaseResponse(success=True, message="Prompt updated successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("update_prompt_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt: {str(e)}"
        )


@router.delete("/prompts/{prompt_id}", response_model=BaseResponse)
async def delete_prompt(prompt_id: str):
    """Delete prompt"""
    try:
        prompts_db.delete_prompt(prompt_id)
        return BaseResponse(success=True, message="Prompt deleted successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_prompt_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt: {str(e)}"
        )


@router.post("/prompts/batch-delete", response_model=BatchOperationResponse)
async def batch_delete_prompts(request: BatchDeleteRequest):
    """Batch delete prompts"""
    try:
        result = prompts_db.batch_delete_prompts(request.ids)
        
        return BatchOperationResponse(
            success_count=result['success_count'],
            failure_count=result['failure_count'],
            failed_ids=result['failed_ids'],
            message=f"Deleted {result['success_count']} of {len(request.ids)} prompts"
        )
        
    except Exception as e:
        logger.error("batch_delete_prompts_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch delete prompts: {str(e)}"
        )


# ==================== ORGANIZATION MANAGEMENT ====================

@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(request: OrganizationCreate):
    """Create new organization"""
    try:
        logger.info("create_organization_called", organization_id=request.organization_id)
        
        organizations_db.create_organization(
            organization_id=request.organization_id,
            organization_name=request.organization_name,
            description=request.description,
            settings=request.settings,
            is_active=request.is_active
        )
        
        org = organizations_db.get_organization(request.organization_id)
        return OrganizationResponse(**org)
        
    except Exception as e:
        logger.error("create_organization_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/organizations", response_model=OrganizationsListResponse)
async def list_organizations(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all organizations"""
    try:
        orgs = organizations_db.list_organizations(is_active, limit, offset)
        org_responses = [OrganizationResponse(**o) for o in orgs]
        
        return OrganizationsListResponse(
            organizations=org_responses,
            total_count=len(org_responses)
        )
        
    except Exception as e:
        logger.error("list_organizations_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}"
        )


@router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
async def get_organization(organization_id: str):
    """Get specific organization"""
    try:
        org = organizations_db.get_organization(organization_id)
        return OrganizationResponse(**org)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_organization_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization: {str(e)}"
        )


@router.put("/organizations/{organization_id}", response_model=BaseResponse)
async def update_organization(organization_id: str, request: OrganizationUpdate):
    """Update organization"""
    try:
        organizations_db.update_organization(
            organization_id=organization_id,
            organization_name=request.organization_name,
            description=request.description,
            settings=request.settings,
            is_active=request.is_active
        )
        
        return BaseResponse(success=True, message="Organization updated successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("update_organization_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )


@router.delete("/organizations/{organization_id}", response_model=BaseResponse)
async def delete_organization(organization_id: str):
    """Delete organization"""
    try:
        organizations_db.delete_organization(organization_id)
        return BaseResponse(success=True, message="Organization deleted successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_organization_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )


# ==================== GUIDELINE MANAGEMENT ====================

@router.post("/organizations/{organization_id}/guidelines", response_model=GuidelineResponse, status_code=status.HTTP_201_CREATED)
async def create_guideline(organization_id: str, request: GuidelineCreate):
    """Create new guideline for organization"""
    try:
        # Override organization_id from URL
        guideline_id = guidelines_db.create_guideline(
            organization_id=organization_id,
            guideline_name=request.guideline_name,
            guideline_text=request.guideline_text,
            description=request.description,
            is_active=request.is_active
        )
        
        guideline = guidelines_db.get_guideline(guideline_id)
        return GuidelineResponse(**guideline)
        
    except Exception as e:
        logger.error("create_guideline_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create guideline: {str(e)}"
        )


@router.get("/organizations/{organization_id}/guidelines", response_model=GuidelinesListResponse)
async def list_guidelines(
    organization_id: str,
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List guidelines for organization"""
    try:
        guidelines = guidelines_db.list_guidelines(organization_id, is_active, limit, offset)
        guideline_responses = [GuidelineResponse(**g) for g in guidelines]
        
        return GuidelinesListResponse(
            guidelines=guideline_responses,
            organization_id=organization_id,
            total_count=len(guideline_responses)
        )
        
    except Exception as e:
        logger.error("list_guidelines_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list guidelines: {str(e)}"
        )


@router.get("/guidelines/{guideline_id}", response_model=GuidelineResponse)
async def get_guideline(guideline_id: str):
    """Get specific guideline"""
    try:
        guideline = guidelines_db.get_guideline(guideline_id)
        return GuidelineResponse(**guideline)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_guideline_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get guideline: {str(e)}"
        )


@router.put("/guidelines/{guideline_id}", response_model=BaseResponse)
async def update_guideline(guideline_id: str, request: GuidelineUpdate):
    """Update guideline"""
    try:
        guidelines_db.update_guideline(
            guideline_id=guideline_id,
            guideline_name=request.guideline_name,
            guideline_text=request.guideline_text,
            description=request.description,
            is_active=request.is_active
        )
        
        return BaseResponse(success=True, message="Guideline updated successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("update_guideline_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update guideline: {str(e)}"
        )


@router.delete("/guidelines/{guideline_id}", response_model=BaseResponse)
async def delete_guideline(guideline_id: str):
    """Delete guideline"""
    try:
        guidelines_db.delete_guideline(guideline_id)
        return BaseResponse(success=True, message="Guideline deleted successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_guideline_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete guideline: {str(e)}"
        )


# ==================== USER MANAGEMENT ====================

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: UserCreate):
    """Create new user"""
    try:
        users_db.create_user(
            user_id=request.user_id,
            user_name=request.user_name,
            user_email=request.user_email,
            organization_id=request.organization_id,
            role=request.role,
            is_active=request.is_active
        )
        
        user = users_db.get_user(request.user_id)
        return UserResponse(**user)
        
    except Exception as e:
        logger.error("create_user_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users", response_model=UsersListResponse)
async def list_users(
    organization_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List users"""
    try:
        users = users_db.list_users(organization_id, is_active, limit, offset)
        user_responses = [UserResponse(**u) for u in users]
        
        return UsersListResponse(
            users=user_responses,
            total_count=len(user_responses)
        )
        
    except Exception as e:
        logger.error("list_users_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get specific user"""
    try:
        user = users_db.get_user(user_id)
        return UserResponse(**user)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_user_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=BaseResponse)
async def update_user(user_id: str, request: UserUpdate):
    """Update user"""
    try:
        users_db.update_user(
            user_id=user_id,
            user_name=request.user_name,
            user_email=request.user_email,
            organization_id=request.organization_id,
            role=request.role,
            is_active=request.is_active
        )
        
        return BaseResponse(success=True, message="User updated successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("update_user_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=BaseResponse)
async def delete_user(user_id: str):
    """Delete user"""
    try:
        users_db.delete_user(user_id)
        return BaseResponse(success=True, message="User deleted successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_user_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


# ==================== API KEY MANAGEMENT ====================

@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(request: APIKeyCreate):
    """Create new API key"""
    try:
        result = api_keys_db.create_api_key(
            user_id=request.user_id,
            key_name=request.key_name,
            organization_id=request.organization_id,
            permissions=request.permissions,
            expires_at=request.expires_at
        )
        
        return APIKeyResponse(**result, permissions=request.permissions, is_active=True, created_at=datetime.utcnow())
        
    except Exception as e:
        logger.error("create_api_key_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/api-keys", response_model=APIKeysListResponse)
async def list_api_keys(
    user_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List API keys"""
    try:
        keys = api_keys_db.list_api_keys(user_id, is_active, limit, offset)
        
        # Don't return actual API keys in list
        for key in keys:
            key['api_key'] = "***"
        
        key_responses = [APIKeyResponse(**k) for k in keys]
        
        return APIKeysListResponse(
            api_keys=key_responses,
            total_count=len(key_responses)
        )
        
    except Exception as e:
        logger.error("list_api_keys_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.delete("/api-keys/{key_id}", response_model=BaseResponse)
async def delete_api_key(key_id: str):
    """Delete API key"""
    try:
        api_keys_db.delete_api_key(key_id)
        return BaseResponse(success=True, message="API key deleted successfully")
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_api_key_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
        )

