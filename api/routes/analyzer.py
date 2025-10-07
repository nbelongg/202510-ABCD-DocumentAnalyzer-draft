"""Analyzer API routes"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from typing import Optional, List
from schemas.analyzer import (
    AnalyzerRequest,
    AnalyzerResponse,
    AnalyzerSessionsResponse,
    AnalyzerFollowupRequest,
    AnalyzerFollowupResponse,
    AnalyzerFeedbackRequest
)
from schemas.common import DocumentType, UserRole, BaseResponse
from core.analyzer import DocumentAnalyzer
from db.analyzer_db import AnalyzerDB
from services.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
analyzer = DocumentAnalyzer()
analyzer_db = AnalyzerDB()


@router.post("/analyze", response_model=AnalyzerResponse)
async def analyze_document(
    user_id: str = Form(...),
    user_name: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    document_type: DocumentType = Form(DocumentType.PROGRAM_DESIGN),
    user_role: UserRole = Form(UserRole.IMPACT_CONSULTANT),
    organization_id: Optional[str] = Form(None),
    prompt_labels: List[str] = Form(["P1", "P2", "P3", "P4", "P5"]),
    showcase_items: int = Form(10),
    text_input: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None)
):
    """
    Analyze a document
    
    Provide either text_input or pdf_file.
    """
    try:
        # Read file data if provided
        file_data = None
        if pdf_file:
            file_data = await pdf_file.read()
        
        # Create request
        request = AnalyzerRequest(
            user_id=user_id,
            user_name=user_name,
            session_id=session_id,
            text_input=text_input,
            file_data=file_data,
            document_type=document_type,
            user_role=user_role,
            organization_id=organization_id,
            prompt_labels=prompt_labels,
            showcase_items=showcase_items
        )
        
        # Analyze
        response = await analyzer.analyze(request)
        return response
        
    except Exception as e:
        logger.error("analyze_endpoint_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/sessions", response_model=AnalyzerSessionsResponse)
async def get_sessions(user_id: str, limit: int = 20, offset: int = 0):
    """Get user's analyzer sessions"""
    try:
        sessions = analyzer_db.get_user_sessions(user_id, limit, offset)
        return AnalyzerSessionsResponse(
            sessions=sessions,
            total_count=len(sessions)
        )
    except Exception as e:
        logger.error("get_sessions_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get specific session details"""
    try:
        session_data = analyzer_db.get_session(session_id)
        return session_data
    except Exception as e:
        logger.error("get_session_failed", error=str(e))
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/followup", response_model=AnalyzerFollowupResponse)
async def followup_question(request: AnalyzerFollowupRequest):
    """Ask follow-up question about analysis"""
    try:
        answer = await analyzer.answer_followup(request)
        return AnalyzerFollowupResponse(
            answer=answer,
            section=request.section
        )
    except Exception as e:
        logger.error("followup_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=BaseResponse)
async def submit_feedback(request: AnalyzerFeedbackRequest):
    """Submit feedback on analysis section"""
    try:
        analyzer_db.save_feedback(
            session_id=request.session_id,
            section=request.section,
            feedback=request.feedback,
            feedback_note=request.feedback_note
        )
        return BaseResponse(
            success=True,
            message="Feedback saved successfully"
        )
    except Exception as e:
        logger.error("feedback_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

