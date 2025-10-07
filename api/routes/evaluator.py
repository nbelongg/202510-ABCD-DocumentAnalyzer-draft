"""Evaluator API routes"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status, Query
from typing import Optional, List
from core.evaluator import ProposalEvaluator
from db.evaluator_db import EvaluatorDB
from schemas.evaluator import (
    EvaluatorRequest,
    EvaluatorResponse,
    EvaluatorSessionsResponse,
    SessionSummary,
    EvaluatorFollowupRequest,
    EvaluatorFollowupResponse,
    EvaluatorFeedbackRequest,
    SessionTitleUpdateRequest,
    OrganizationGuidelinesResponse,
    OrganizationGuideline
)
from schemas.common import DocumentType, BaseResponse
from services.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize evaluator engine and database
evaluator_engine = ProposalEvaluator()
evaluator_db = EvaluatorDB()


@router.post("/evaluate", response_model=EvaluatorResponse)
async def evaluate_proposal(
    user_id: str = Form(...),
    user_name: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    document_type: DocumentType = Form(DocumentType.PROPOSAL),
    organization_id: Optional[str] = Form(None),
    org_guideline_id: Optional[str] = Form(None),
    proposal_text_input: Optional[str] = Form(None),
    proposal_pdf_file: Optional[UploadFile] = File(None),
    tor_text_input: Optional[str] = Form(None),
    tor_pdf_file: Optional[UploadFile] = File(None)
):
    """
    Evaluate proposal against Terms of Reference (ToR)
    
    This endpoint performs three-part analysis:
    1. P_Internal: Internal consistency of proposal
    2. P_External: Alignment between proposal and ToR
    3. P_Delta: Gap analysis between proposal and ToR
    
    Provide either text or PDF for both proposal and ToR.
    """
    try:
        logger.info(
            "evaluate_endpoint_called",
            user_id=user_id,
            session_id=session_id,
            has_organization=bool(organization_id)
        )
        
        # Validate inputs
        if not proposal_text_input and not proposal_pdf_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either proposal_text_input or proposal_pdf_file must be provided"
            )
        
        if not tor_text_input and not tor_pdf_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either tor_text_input or tor_pdf_file must be provided"
            )
        
        # Read file data if provided
        proposal_file_data = None
        if proposal_pdf_file:
            proposal_file_data = await proposal_pdf_file.read()
        
        tor_file_data = None
        if tor_pdf_file:
            tor_file_data = await tor_pdf_file.read()
        
        # Create request
        request = EvaluatorRequest(
            user_id=user_id,
            user_name=user_name,
            session_id=session_id,
            document_type=document_type,
            organization_id=organization_id,
            org_guideline_id=org_guideline_id,
            proposal_text_input=proposal_text_input,
            proposal_file_data=proposal_file_data,
            tor_text_input=tor_text_input,
            tor_file_data=tor_file_data
        )
        
        # Evaluate
        response = await evaluator_engine.evaluate(request)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("evaluate_endpoint_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/sessions", response_model=EvaluatorSessionsResponse)
async def get_sessions(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of sessions"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get list of user's evaluation sessions
    
    Returns sessions sorted by most recent first.
    """
    try:
        logger.info("get_evaluator_sessions_called", user_id=user_id)
        
        sessions = evaluator_db.get_user_sessions(user_id, limit, offset)
        
        # Convert to SessionSummary objects
        session_summaries = [
            SessionSummary(
                session_id=s['session_id'],
                user_id=s['user_id'],
                user_name=s.get('user_name'),
                document_type=s.get('document_type'),
                organization_id=s.get('organization_id'),
                session_title=s.get('session_title'),
                overall_score=s.get('overall_score'),
                created_at=s['created_at'],
                completed_at=s.get('completed_at')
            )
            for s in sessions
        ]
        
        return EvaluatorSessionsResponse(
            sessions=session_summaries,
            total_count=len(session_summaries)
        )
        
    except Exception as e:
        logger.error("get_evaluator_sessions_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=EvaluatorResponse)
async def get_session(session_id: str):
    """
    Get specific evaluation session details
    
    Returns complete evaluation including all three analyses.
    """
    try:
        logger.info("get_evaluator_session_called", session_id=session_id)
        
        session = evaluator_db.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Build response from session data
        response = EvaluatorResponse(
            session_id=session['session_id'],
            user_id=session['user_id'],
            internal_analysis=session.get('internal_analysis', {}),
            external_analysis=session.get('external_analysis', {}),
            delta_analysis=session.get('delta_analysis', {}),
            overall_score=session.get('overall_score'),
            processing_time_seconds=session.get('processing_time', 0.0),
            created_at=session['created_at']
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_evaluator_session_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.post("/followup", response_model=EvaluatorFollowupResponse)
async def followup_question(request: EvaluatorFollowupRequest):
    """
    Ask follow-up question about evaluation
    
    Allows users to ask questions about specific sections or general questions.
    """
    try:
        logger.info(
            "evaluator_followup_called",
            session_id=request.session_id,
            section=request.section
        )
        
        response = await evaluator_engine.answer_followup(request)
        return response
        
    except Exception as e:
        logger.error("evaluator_followup_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer followup: {str(e)}"
        )


@router.post("/feedback", response_model=BaseResponse)
async def submit_feedback(request: EvaluatorFeedbackRequest):
    """
    Submit feedback on evaluation section
    
    Allows users to rate specific sections of the evaluation.
    """
    try:
        logger.info(
            "evaluator_feedback_called",
            session_id=request.session_id,
            section=request.section,
            feedback=request.feedback
        )
        
        evaluator_db.save_feedback(
            session_id=request.session_id,
            user_id=request.user_id,
            section=request.section,
            feedback=request.feedback,
            response_id=request.response_id,
            feedback_note=request.feedback_note
        )
        
        return BaseResponse(
            success=True,
            message="Feedback submitted successfully"
        )
        
    except Exception as e:
        logger.error("evaluator_feedback_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.put("/sessions/{session_id}/title", response_model=BaseResponse)
async def update_session_title(
    session_id: str,
    request: SessionTitleUpdateRequest
):
    """
    Update session title
    
    Allows users to set a custom title for their evaluation session.
    """
    try:
        logger.info("update_session_title_called", session_id=session_id)
        
        evaluator_db.update_session_title(
            session_id=session_id,
            user_id=request.user_id,
            session_title=request.session_title
        )
        
        return BaseResponse(
            success=True,
            message="Session title updated successfully"
        )
        
    except Exception as e:
        logger.error("update_session_title_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session title: {str(e)}"
        )


@router.post("/sessions/batch")
async def get_sessions_batch(
    user_id: Optional[str] = None,
    session_ids: List[str] = [],
    number_of_sessions: Optional[int] = None
):
    """
    Get multiple sessions by IDs or get latest N sessions for user
    
    Batch retrieval endpoint for efficient fetching.
    """
    try:
        if session_ids:
            sessions = evaluator_db.get_sessions_by_ids(session_ids)
        elif user_id:
            limit = number_of_sessions or 20
            sessions = evaluator_db.get_user_sessions(user_id, limit=limit)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either user_id or session_ids must be provided"
            )
        
        return {"sessions": sessions, "total_count": len(sessions)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_sessions_batch_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions batch: {str(e)}"
        )


@router.get("/organizations/{organization_id}/guidelines", response_model=OrganizationGuidelinesResponse)
async def get_organization_guidelines(
    organization_id: str,
    guideline_id: Optional[str] = Query(None, description="Specific guideline ID")
):
    """
    Get organization-specific evaluation guidelines
    
    Returns guidelines used for proposal evaluation.
    """
    try:
        logger.info("get_org_guidelines_called", organization_id=organization_id)
        
        guidelines = evaluator_db.get_organization_guidelines(organization_id, guideline_id)
        
        guideline_objects = [
            OrganizationGuideline(
                guideline_id=g['guideline_id'],
                organization_id=g['organization_id'],
                guideline_name=g['guideline_name'],
                guideline_text=g['guideline_text'],
                description=g.get('description'),
                is_active=g.get('is_active', True),
                created_at=g['created_at'],
                updated_at=g.get('updated_at')
            )
            for g in guidelines
        ]
        
        return OrganizationGuidelinesResponse(
            guidelines=guideline_objects,
            organization_id=organization_id,
            total_count=len(guideline_objects)
        )
        
    except Exception as e:
        logger.error("get_org_guidelines_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get guidelines: {str(e)}"
        )

