"""Database operations for evaluator functionality"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import DatabaseError

logger = get_logger(__name__)


class EvaluatorDB:
    """Database operations for proposal evaluator"""
    
    @staticmethod
    def create_session(
        user_id: str,
        session_id: str,
        user_name: Optional[str] = None,
        document_type: Optional[str] = None,
        organization_id: Optional[str] = None,
        guideline_id: Optional[str] = None,
        proposal_text: Optional[str] = None,
        proposal_url: Optional[str] = None,
        tor_text: Optional[str] = None,
        tor_url: Optional[str] = None
    ) -> str:
        """
        Create evaluator session
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            user_name: User's name
            document_type: Type of document
            organization_id: Organization identifier
            guideline_id: Guideline identifier
            proposal_text: Proposal text content
            proposal_url: S3 URL for proposal PDF
            tor_text: ToR text content
            tor_url: S3 URL for ToR PDF
            
        Returns:
            Session ID
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO evaluator_sessions
                    (session_id, user_id, user_name, document_type, organization_id, guideline_id,
                     proposal_text, proposal_url, tor_text, tor_url, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    session_id, user_id, user_name, document_type, organization_id, guideline_id,
                    proposal_text, proposal_url, tor_text, tor_url, datetime.utcnow()
                ))
                logger.info("evaluator_session_created", session_id=session_id, user_id=user_id)
                return session_id
        except Exception as e:
            logger.error("create_evaluator_session_failed", error=str(e))
            raise DatabaseError(f"Failed to create evaluator session: {str(e)}")
    
    @staticmethod
    def save_evaluation_results(
        session_id: str,
        internal_analysis: Dict,
        external_analysis: Dict,
        delta_analysis: Dict,
        overall_score: Optional[float] = None,
        summary: Optional[str] = None,
        processing_time: Optional[float] = None
    ) -> None:
        """
        Save evaluation results
        
        Args:
            session_id: Session identifier
            internal_analysis: P_Internal analysis results
            external_analysis: P_External analysis results
            delta_analysis: P_Delta analysis results
            overall_score: Overall evaluation score
            summary: Executive summary
            processing_time: Time taken for evaluation
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    UPDATE evaluator_sessions
                    SET internal_analysis = %s, external_analysis = %s,
                        delta_analysis = %s, overall_score = %s,
                        processing_time = %s, completed_at = %s
                    WHERE session_id = %s
                """
                cursor.execute(query, (
                    json.dumps(internal_analysis),
                    json.dumps(external_analysis),
                    json.dumps(delta_analysis),
                    overall_score,
                    processing_time,
                    datetime.utcnow(),
                    session_id
                ))
                logger.info("evaluation_results_saved", session_id=session_id, overall_score=overall_score)
        except Exception as e:
            logger.error("save_evaluation_failed", error=str(e))
            raise DatabaseError(f"Failed to save evaluation: {str(e)}")
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """
        Get evaluation session details
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dictionary or None
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT session_id, user_id, user_name, document_type,
                           organization_id, guideline_id,
                           proposal_text, proposal_url, tor_text, tor_url,
                           internal_analysis, external_analysis, delta_analysis,
                           overall_score, session_title, processing_time,
                           created_at, completed_at
                    FROM evaluator_sessions
                    WHERE session_id = %s
                """
                cursor.execute(query, (session_id,))
                result = cursor.fetchone()
                
                if result:
                    # Parse JSON fields
                    if result.get('internal_analysis'):
                        result['internal_analysis'] = json.loads(result['internal_analysis'])
                    if result.get('external_analysis'):
                        result['external_analysis'] = json.loads(result['external_analysis'])
                    if result.get('delta_analysis'):
                        result['delta_analysis'] = json.loads(result['delta_analysis'])
                
                return result
        except Exception as e:
            logger.error("get_session_failed", error=str(e))
            raise DatabaseError(f"Failed to get session: {str(e)}")
    
    @staticmethod
    def get_user_sessions(user_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        Get user's evaluation sessions
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions
            offset: Offset for pagination
            
        Returns:
            List of session summaries
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT session_id, user_id, user_name, document_type,
                           organization_id, session_title, overall_score,
                           created_at, completed_at
                    FROM evaluator_sessions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, (user_id, limit, offset))
                return cursor.fetchall()
        except Exception as e:
            logger.error("get_user_sessions_failed", error=str(e))
            raise DatabaseError(f"Failed to get user sessions: {str(e)}")
    
    @staticmethod
    def save_followup(
        session_id: str,
        user_id: str,
        query: str,
        answer: str,
        section: Optional[str] = None
    ) -> None:
        """
        Save follow-up question and answer
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            query: Follow-up question
            answer: Answer to question
            section: Specific section (P_Internal, P_External, P_Delta)
        """
        try:
            with get_db_cursor() as cursor:
                query_sql = """
                    INSERT INTO evaluator_followups
                    (session_id, user_id, query, answer, section, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_sql, (session_id, user_id, query, answer, section, datetime.utcnow()))
                logger.info("followup_saved", session_id=session_id)
        except Exception as e:
            logger.error("save_followup_failed", error=str(e))
            raise DatabaseError(f"Failed to save followup: {str(e)}")
    
    @staticmethod
    def save_feedback(
        session_id: str,
        user_id: str,
        section: str,
        feedback: bool,
        response_id: Optional[str] = None,
        feedback_note: Optional[str] = None
    ) -> None:
        """
        Save feedback on evaluation section
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            section: Section type (P_Internal, P_External, P_Delta)
            feedback: True for positive, False for negative
            response_id: Specific response identifier
            feedback_note: Optional feedback text
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO evaluator_feedback
                    (session_id, user_id, section, response_id, feedback, feedback_note, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    session_id, user_id, section, response_id, feedback, feedback_note, datetime.utcnow()
                ))
                logger.info("feedback_saved", session_id=session_id, section=section, feedback=feedback)
        except Exception as e:
            logger.error("save_feedback_failed", error=str(e))
            raise DatabaseError(f"Failed to save feedback: {str(e)}")
    
    @staticmethod
    def update_session_title(session_id: str, user_id: str, session_title: str) -> None:
        """
        Update session title
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            session_title: New session title
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    UPDATE evaluator_sessions
                    SET session_title = %s
                    WHERE session_id = %s AND user_id = %s
                """
                cursor.execute(query, (session_title, session_id, user_id))
                logger.info("session_title_updated", session_id=session_id)
        except Exception as e:
            logger.error("update_session_title_failed", error=str(e))
            raise DatabaseError(f"Failed to update session title: {str(e)}")
    
    @staticmethod
    def get_sessions_by_ids(session_ids: List[str]) -> List[Dict]:
        """
        Get multiple sessions by IDs
        
        Args:
            session_ids: List of session identifiers
            
        Returns:
            List of session dictionaries
        """
        try:
            if not session_ids:
                return []
            
            with get_db_cursor() as cursor:
                placeholders = ', '.join(['%s'] * len(session_ids))
                query = f"""
                    SELECT session_id, user_id, user_name, document_type,
                           organization_id, session_title, overall_score,
                           created_at, completed_at
                    FROM evaluator_sessions
                    WHERE session_id IN ({placeholders})
                    ORDER BY created_at DESC
                """
                cursor.execute(query, tuple(session_ids))
                return cursor.fetchall()
        except Exception as e:
            logger.error("get_sessions_by_ids_failed", error=str(e))
            raise DatabaseError(f"Failed to get sessions by IDs: {str(e)}")
    
    @staticmethod
    def get_organization_guidelines(
        organization_id: str,
        guideline_id: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> List[Dict]:
        """
        Get organization-specific guidelines with three-tier access control
        
        Returns:
        1. Organization's own guidelines
        2. Public guidelines mapped to this organization (admin-controlled)
        3. Universal public guidelines (available to all)
        
        Args:
            organization_id: Organization identifier
            guideline_id: Specific guideline ID (optional)
            user_email: User email for access control (optional)
            
        Returns:
            List of guidelines with access type
        """
        try:
            # Use the enhanced utility function if email provided
            if user_email:
                from utils.organization_utils import get_accessible_guidelines
                
                all_guidelines = get_accessible_guidelines(user_email, organization_id)
                
                # Filter by specific guideline if requested
                if guideline_id:
                    all_guidelines = [
                        g for g in all_guidelines 
                        if g['guideline_id'] == guideline_id
                    ]
                
                logger.info(
                    "guidelines_retrieved_with_access_control",
                    org_id=organization_id,
                    user_email=user_email,
                    count=len(all_guidelines)
                )
                
                return all_guidelines
            
            # Fallback for backward compatibility (no email provided)
            # This returns only the organization's own guidelines
            with get_db_cursor() as cursor:
                if guideline_id:
                    query = """
                        SELECT guideline_id, organization_id, guideline_name,
                               guideline_text, description, is_active,
                               created_at, updated_at
                        FROM organization_guidelines
                        WHERE organization_id = %s AND guideline_id = %s AND is_active = TRUE
                    """
                    cursor.execute(query, (organization_id, guideline_id))
                else:
                    query = """
                        SELECT guideline_id, organization_id, guideline_name,
                               guideline_text, description, is_active,
                               created_at, updated_at
                        FROM organization_guidelines
                        WHERE organization_id = %s AND is_active = TRUE
                        ORDER BY guideline_name
                    """
                    cursor.execute(query, (organization_id,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error("get_guidelines_failed", error=str(e))
            raise DatabaseError(f"Failed to get guidelines: {str(e)}")

