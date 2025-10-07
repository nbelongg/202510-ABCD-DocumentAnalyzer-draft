"""Database operations for chatbot functionality"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import DatabaseError

logger = get_logger(__name__)


class ChatbotDB:
    """Database operations for chatbot"""
    
    @staticmethod
    def create_session(
        user_id: str,
        session_id: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        source: Optional[str] = None
    ) -> str:
        """
        Create chat session
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            user_name: User's name (optional)
            user_email: User's email (optional)
            source: Source platform (e.g., 'WA')
            
        Returns:
            Session ID
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO chatbot_sessions
                    (session_id, user_id, user_name, user_email, source, created_at, last_message_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                now = datetime.utcnow()
                cursor.execute(query, (session_id, user_id, user_name, user_email, source, now, now))
                logger.info("chat_session_created", session_id=session_id, user_id=user_id)
                return session_id
        except Exception as e:
            logger.error("create_chat_session_failed", error=str(e))
            raise DatabaseError(f"Failed to create chat session: {str(e)}")
    
    @staticmethod
    def save_message(
        session_id: str,
        role: str,
        content: str,
        response_id: Optional[str] = None,
        context_data: Optional[Dict] = None,
        sources: Optional[List[Dict]] = None
    ) -> None:
        """
        Save chat message with context and sources
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            response_id: Response identifier (for assistant messages)
            context_data: Context information from knowledge base
            sources: Source documents information
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO chatbot_messages
                    (session_id, role, content, response_id, context_data, sources, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    session_id,
                    role,
                    content,
                    response_id,
                    json.dumps(context_data) if context_data else None,
                    json.dumps(sources) if sources else None,
                    datetime.utcnow()
                ))
                
                # Update last message time
                update_query = """
                    UPDATE chatbot_sessions
                    SET last_message_at = %s
                    WHERE session_id = %s
                """
                cursor.execute(update_query, (datetime.utcnow(), session_id))
                
        except Exception as e:
            logger.error("save_message_failed", error=str(e))
            raise DatabaseError(f"Failed to save message: {str(e)}")
    
    @staticmethod
    def get_session_history(session_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for session"""
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT role, content, created_at
                    FROM chatbot_messages
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (session_id, limit))
                return list(reversed(cursor.fetchall()))
        except Exception as e:
            logger.error("get_history_failed", error=str(e))
            raise DatabaseError(f"Failed to get history: {str(e)}")
    
    @staticmethod
    def get_user_sessions(user_id: str, source: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Get user's chat sessions
        
        Args:
            user_id: User identifier
            source: Filter by source (e.g., 'WA')
            limit: Maximum number of sessions
            
        Returns:
            List of session dictionaries
        """
        try:
            with get_db_cursor() as cursor:
                if source:
                    query = """
                        SELECT s.session_id, s.user_id, s.user_name, s.source,
                               s.created_at, s.last_message_at,
                               COUNT(m.id) as message_count
                        FROM chatbot_sessions s
                        LEFT JOIN chatbot_messages m ON s.session_id = m.session_id
                        WHERE s.user_id = %s AND s.source = %s
                        GROUP BY s.session_id
                        ORDER BY s.last_message_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (user_id, source, limit))
                else:
                    query = """
                        SELECT s.session_id, s.user_id, s.user_name, s.source,
                               s.created_at, s.last_message_at,
                               COUNT(m.id) as message_count
                        FROM chatbot_sessions s
                        LEFT JOIN chatbot_messages m ON s.session_id = m.session_id
                        WHERE s.user_id = %s
                        GROUP BY s.session_id
                        ORDER BY s.last_message_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (user_id, limit))
                
                return cursor.fetchall()
        except Exception as e:
            logger.error("get_user_sessions_failed", error=str(e))
            raise DatabaseError(f"Failed to get user sessions: {str(e)}")
    
    @staticmethod
    def get_user_conversations(user_id: str, session_id: str) -> str:
        """
        Get conversation history as formatted string
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Formatted conversation string
        """
        try:
            messages = ChatbotDB.get_session_history(session_id)
            
            conversation_parts = []
            for msg in messages:
                role = msg.get('role', '')
                content = msg.get('content', '')
                
                if role == 'user':
                    conversation_parts.append(f"User: {content}")
                elif role == 'assistant':
                    conversation_parts.append(f"Assistant: {content}")
            
            return '\n\n'.join(conversation_parts)
        except Exception as e:
            logger.error("get_user_conversations_failed", error=str(e))
            return ""
    
    @staticmethod
    def get_user_data(user_id: str, source: Optional[str] = None) -> Optional[Dict]:
        """
        Get user's last session data
        
        Args:
            user_id: User identifier
            source: Filter by source
            
        Returns:
            Dictionary with last session data or None
        """
        try:
            sessions = ChatbotDB.get_user_sessions(user_id, source, limit=1)
            
            if not sessions:
                return None
            
            session = sessions[0]
            session_id = session['session_id']
            
            # Get last few messages
            messages = ChatbotDB.get_session_history(session_id, limit=10)
            
            # Find last query and response
            last_query = None
            last_response = None
            
            for msg in reversed(messages):
                if msg['role'] == 'user' and not last_query:
                    last_query = msg['content']
                if msg['role'] == 'assistant' and not last_response:
                    last_response = msg['content']
                if last_query and last_response:
                    break
            
            return {
                'session_id': session_id,
                'user_id': user_id,
                'last_message_at': session.get('last_message_at'),
                'message_count': session.get('message_count', 0),
                'last_query': last_query,
                'last_response': last_response
            }
        except Exception as e:
            logger.error("get_user_data_failed", error=str(e))
            return None
    
    @staticmethod
    def save_feedback(user_id: str, response_id: str, feedback: bool, feedback_note: Optional[str] = None) -> None:
        """
        Save feedback on a response
        
        Args:
            user_id: User identifier
            response_id: Response identifier
            feedback: True for positive, False for negative
            feedback_note: Optional feedback text
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO chatbot_feedback
                    (user_id, response_id, feedback, feedback_note, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (user_id, response_id, feedback, feedback_note, datetime.utcnow()))
                logger.info("feedback_saved", response_id=response_id, feedback=feedback)
        except Exception as e:
            logger.error("save_feedback_failed", error=str(e))
            raise DatabaseError(f"Failed to save feedback: {str(e)}")

