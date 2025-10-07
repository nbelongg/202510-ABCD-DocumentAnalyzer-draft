"""Database operations for analyzer functionality"""
from typing import Optional, List, Dict
from datetime import datetime
import json
from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


class AnalyzerDB:
    """Database operations for document analyzer"""
    
    @staticmethod
    def create_session(
        user_id: str,
        session_id: str,
        document_type: str,
        user_role: str,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Create a new analyzer session
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            document_type: Type of document
            user_role: User role
            organization_id: Optional organization ID
            
        Returns:
            Created session ID
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO analyzer_sessions
                    (session_id, user_id, document_type, user_role, organization_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    session_id,
                    user_id,
                    document_type,
                    user_role,
                    organization_id,
                    datetime.utcnow()
                ))
                
                logger.info("analyzer_session_created", session_id=session_id)
                return session_id
                
        except Exception as e:
            logger.error("create_session_failed", error=str(e))
            raise DatabaseError(f"Failed to create session: {str(e)}")
    
    @staticmethod
    def save_analysis_results(
        session_id: str,
        sections: List[Dict],
        summary: Optional[str] = None,
        processing_time: float = 0.0
    ) -> None:
        """
        Save analysis results for a session
        
        Args:
            session_id: Session identifier
            sections: Analysis section results
            summary: Optional summary
            processing_time: Processing time in seconds
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    UPDATE analyzer_sessions
                    SET sections = %s, summary = %s, processing_time = %s,
                        completed_at = %s
                    WHERE session_id = %s
                """
                
                cursor.execute(query, (
                    json.dumps(sections),
                    summary,
                    processing_time,
                    datetime.utcnow(),
                    session_id
                ))
                
                logger.info("analysis_results_saved", session_id=session_id)
                
        except Exception as e:
            logger.error("save_results_failed", error=str(e))
            raise DatabaseError(f"Failed to save results: {str(e)}")
    
    @staticmethod
    def get_session(session_id: str) -> Dict:
        """
        Get session details
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT * FROM analyzer_sessions
                    WHERE session_id = %s
                """
                
                cursor.execute(query, (session_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("Session", session_id)
                
                # Parse JSON fields
                if result.get('sections'):
                    result['sections'] = json.loads(result['sections'])
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_session_failed", error=str(e))
            raise DatabaseError(f"Failed to get session: {str(e)}")
    
    @staticmethod
    def get_user_sessions(
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get user's analyzer sessions
        
        Args:
            user_id: User identifier
            limit: Number of sessions to return
            offset: Offset for pagination
            
        Returns:
            List of session summaries
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT session_id, document_type, user_role,
                           created_at, completed_at, processing_time
                    FROM analyzer_sessions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                cursor.execute(query, (user_id, limit, offset))
                results = cursor.fetchall()
                
                return results
                
        except Exception as e:
            logger.error("get_user_sessions_failed", error=str(e))
            raise DatabaseError(f"Failed to get user sessions: {str(e)}")
    
    @staticmethod
    def save_followup(
        session_id: str,
        query: str,
        answer: str,
        section: Optional[str] = None
    ) -> None:
        """
        Save follow-up question and answer
        
        Args:
            session_id: Session identifier
            query: User question
            answer: System answer
            section: Optional section reference
        """
        try:
            with get_db_cursor() as cursor:
                query_sql = """
                    INSERT INTO analyzer_followups
                    (session_id, query, answer, section, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(query_sql, (
                    session_id,
                    query,
                    answer,
                    section,
                    datetime.utcnow()
                ))
                
                logger.info("followup_saved", session_id=session_id)
                
        except Exception as e:
            logger.error("save_followup_failed", error=str(e))
            raise DatabaseError(f"Failed to save followup: {str(e)}")
    
    @staticmethod
    def save_feedback(
        session_id: str,
        section: str,
        feedback: bool,
        feedback_note: Optional[str] = None
    ) -> None:
        """
        Save feedback for analysis section
        
        Args:
            session_id: Session identifier
            section: Section identifier
            feedback: Thumbs up/down
            feedback_note: Optional note
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO analyzer_feedback
                    (session_id, section, feedback, feedback_note, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    session_id,
                    section,
                    feedback,
                    feedback_note,
                    datetime.utcnow()
                ))
                
                logger.info("feedback_saved", session_id=session_id, section=section)
                
        except Exception as e:
            logger.error("save_feedback_failed", error=str(e))
            raise DatabaseError(f"Failed to save feedback: {str(e)}")

