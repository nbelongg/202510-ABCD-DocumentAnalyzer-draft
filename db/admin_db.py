"""Database operations for admin functionality (organizations, users, API keys)"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
import secrets
from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


class OrganizationsDB:
    """Database operations for organization management"""
    
    @staticmethod
    def create_organization(
        organization_id: str,
        organization_name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> str:
        """Create new organization"""
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO organizations
                    (organization_id, organization_name, description, settings, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    organization_id, organization_name, description,
                    json.dumps(settings) if settings else None,
                    is_active, datetime.utcnow()
                ))
                
                logger.info("organization_created", organization_id=organization_id)
                return organization_id
                
        except Exception as e:
            logger.error("create_organization_failed", error=str(e))
            raise DatabaseError(f"Failed to create organization: {str(e)}")
    
    @staticmethod
    def get_organization(organization_id: str) -> Dict:
        """Get organization by ID"""
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT o.organization_id, o.organization_name, o.description,
                           o.settings, o.is_active, o.created_at, o.updated_at,
                           COUNT(g.id) as guidelines_count
                    FROM organizations o
                    LEFT JOIN organization_guidelines g ON o.organization_id = g.organization_id
                    WHERE o.organization_id = %s
                    GROUP BY o.organization_id
                """
                cursor.execute(query, (organization_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("Organization", organization_id)
                
                # Parse settings JSON
                if result.get('settings'):
                    result['settings'] = json.loads(result['settings'])
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_organization_failed", error=str(e))
            raise DatabaseError(f"Failed to get organization: {str(e)}")
    
    @staticmethod
    def list_organizations(
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """List organizations"""
        try:
            with get_db_cursor() as cursor:
                where_clause = "WHERE o.is_active = %s" if is_active is not None else ""
                params = [is_active] if is_active is not None else []
                
                query = f"""
                    SELECT o.organization_id, o.organization_name, o.description,
                           o.settings, o.is_active, o.created_at, o.updated_at,
                           COUNT(g.id) as guidelines_count
                    FROM organizations o
                    LEFT JOIN organization_guidelines g ON o.organization_id = g.organization_id
                    {where_clause}
                    GROUP BY o.organization_id
                    ORDER BY o.created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                
                # Parse settings JSON
                for result in results:
                    if result.get('settings'):
                        result['settings'] = json.loads(result['settings'])
                
                return results
                
        except Exception as e:
            logger.error("list_organizations_failed", error=str(e))
            raise DatabaseError(f"Failed to list organizations: {str(e)}")
    
    @staticmethod
    def update_organization(
        organization_id: str,
        organization_name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> None:
        """Update organization"""
        try:
            with get_db_cursor() as cursor:
                updates = []
                params = []
                
                if organization_name is not None:
                    updates.append("organization_name = %s")
                    params.append(organization_name)
                
                if description is not None:
                    updates.append("description = %s")
                    params.append(description)
                
                if settings is not None:
                    updates.append("settings = %s")
                    params.append(json.dumps(settings))
                
                if is_active is not None:
                    updates.append("is_active = %s")
                    params.append(is_active)
                
                if not updates:
                    return
                
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                params.append(organization_id)
                
                query = f"""
                    UPDATE organizations
                    SET {', '.join(updates)}
                    WHERE organization_id = %s
                """
                
                cursor.execute(query, tuple(params))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("Organization", organization_id)
                
                logger.info("organization_updated", organization_id=organization_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("update_organization_failed", error=str(e))
            raise DatabaseError(f"Failed to update organization: {str(e)}")
    
    @staticmethod
    def delete_organization(organization_id: str) -> None:
        """Delete organization"""
        try:
            with get_db_cursor() as cursor:
                query = "DELETE FROM organizations WHERE organization_id = %s"
                cursor.execute(query, (organization_id,))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("Organization", organization_id)
                
                logger.info("organization_deleted", organization_id=organization_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("delete_organization_failed", error=str(e))
            raise DatabaseError(f"Failed to delete organization: {str(e)}")


class GuidelinesDB:
    """Database operations for organization guidelines"""
    
    @staticmethod
    def create_guideline(
        organization_id: str,
        guideline_name: str,
        guideline_text: str,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> str:
        """Create new guideline"""
        try:
            guideline_id = str(uuid.uuid4())
            
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO organization_guidelines
                    (guideline_id, organization_id, guideline_name, guideline_text,
                     description, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    guideline_id, organization_id, guideline_name, guideline_text,
                    description, is_active, datetime.utcnow()
                ))
                
                logger.info("guideline_created", guideline_id=guideline_id)
                return guideline_id
                
        except Exception as e:
            logger.error("create_guideline_failed", error=str(e))
            raise DatabaseError(f"Failed to create guideline: {str(e)}")
    
    @staticmethod
    def get_guideline(guideline_id: str) -> Dict:
        """Get guideline by ID"""
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT guideline_id, organization_id, guideline_name,
                           guideline_text, description, is_active,
                           created_at, updated_at
                    FROM organization_guidelines
                    WHERE guideline_id = %s
                """
                cursor.execute(query, (guideline_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("Guideline", guideline_id)
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_guideline_failed", error=str(e))
            raise DatabaseError(f"Failed to get guideline: {str(e)}")
    
    @staticmethod
    def list_guidelines(
        organization_id: str,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """List guidelines for organization"""
        try:
            with get_db_cursor() as cursor:
                where_clauses = ["organization_id = %s"]
                params = [organization_id]
                
                if is_active is not None:
                    where_clauses.append("is_active = %s")
                    params.append(is_active)
                
                query = f"""
                    SELECT guideline_id, organization_id, guideline_name,
                           guideline_text, description, is_active,
                           created_at, updated_at
                    FROM organization_guidelines
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
                
        except Exception as e:
            logger.error("list_guidelines_failed", error=str(e))
            raise DatabaseError(f"Failed to list guidelines: {str(e)}")
    
    @staticmethod
    def update_guideline(
        guideline_id: str,
        guideline_name: Optional[str] = None,
        guideline_text: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> None:
        """Update guideline"""
        try:
            with get_db_cursor() as cursor:
                updates = []
                params = []
                
                if guideline_name is not None:
                    updates.append("guideline_name = %s")
                    params.append(guideline_name)
                
                if guideline_text is not None:
                    updates.append("guideline_text = %s")
                    params.append(guideline_text)
                
                if description is not None:
                    updates.append("description = %s")
                    params.append(description)
                
                if is_active is not None:
                    updates.append("is_active = %s")
                    params.append(is_active)
                
                if not updates:
                    return
                
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                params.append(guideline_id)
                
                query = f"""
                    UPDATE organization_guidelines
                    SET {', '.join(updates)}
                    WHERE guideline_id = %s
                """
                
                cursor.execute(query, tuple(params))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("Guideline", guideline_id)
                
                logger.info("guideline_updated", guideline_id=guideline_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("update_guideline_failed", error=str(e))
            raise DatabaseError(f"Failed to update guideline: {str(e)}")
    
    @staticmethod
    def delete_guideline(guideline_id: str) -> None:
        """Delete guideline"""
        try:
            with get_db_cursor() as cursor:
                query = "DELETE FROM organization_guidelines WHERE guideline_id = %s"
                cursor.execute(query, (guideline_id,))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("Guideline", guideline_id)
                
                logger.info("guideline_deleted", guideline_id=guideline_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("delete_guideline_failed", error=str(e))
            raise DatabaseError(f"Failed to delete guideline: {str(e)}")


class UsersDB:
    """Database operations for user management"""
    
    @staticmethod
    def create_user(
        user_id: str,
        user_name: str,
        user_email: str,
        organization_id: Optional[str] = None,
        role: str = "user",
        is_active: bool = True
    ) -> str:
        """Create new user"""
        try:
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO users
                    (user_id, user_name, user_email, organization_id, role, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    user_id, user_name, user_email.lower(), organization_id,
                    role, is_active, datetime.utcnow()
                ))
                
                logger.info("user_created", user_id=user_id)
                return user_id
                
        except Exception as e:
            logger.error("create_user_failed", error=str(e))
            raise DatabaseError(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def get_user(user_id: str) -> Dict:
        """Get user by ID"""
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT user_id, user_name, user_email, organization_id,
                           role, is_active, created_at, last_login_at
                    FROM users
                    WHERE user_id = %s
                """
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("User", user_id)
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_user_failed", error=str(e))
            raise DatabaseError(f"Failed to get user: {str(e)}")
    
    @staticmethod
    def list_users(
        organization_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """List users"""
        try:
            with get_db_cursor() as cursor:
                where_clauses = []
                params = []
                
                if organization_id:
                    where_clauses.append("organization_id = %s")
                    params.append(organization_id)
                
                if is_active is not None:
                    where_clauses.append("is_active = %s")
                    params.append(is_active)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                query = f"""
                    SELECT user_id, user_name, user_email, organization_id,
                           role, is_active, created_at, last_login_at
                    FROM users
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
                
        except Exception as e:
            logger.error("list_users_failed", error=str(e))
            raise DatabaseError(f"Failed to list users: {str(e)}")
    
    @staticmethod
    def update_user(
        user_id: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> None:
        """Update user"""
        try:
            with get_db_cursor() as cursor:
                updates = []
                params = []
                
                if user_name is not None:
                    updates.append("user_name = %s")
                    params.append(user_name)
                
                if user_email is not None:
                    updates.append("user_email = %s")
                    params.append(user_email.lower())
                
                if organization_id is not None:
                    updates.append("organization_id = %s")
                    params.append(organization_id)
                
                if role is not None:
                    updates.append("role = %s")
                    params.append(role)
                
                if is_active is not None:
                    updates.append("is_active = %s")
                    params.append(is_active)
                
                if not updates:
                    return
                
                params.append(user_id)
                
                query = f"""
                    UPDATE users
                    SET {', '.join(updates)}
                    WHERE user_id = %s
                """
                
                cursor.execute(query, tuple(params))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("User", user_id)
                
                logger.info("user_updated", user_id=user_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("update_user_failed", error=str(e))
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    @staticmethod
    def delete_user(user_id: str) -> None:
        """Delete user"""
        try:
            with get_db_cursor() as cursor:
                query = "DELETE FROM users WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("User", user_id)
                
                logger.info("user_deleted", user_id=user_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("delete_user_failed", error=str(e))
            raise DatabaseError(f"Failed to delete user: {str(e)}")


class APIKeysDB:
    """Database operations for API key management"""
    
    @staticmethod
    def create_api_key(
        user_id: str,
        key_name: str,
        organization_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict:
        """Create new API key"""
        try:
            key_id = str(uuid.uuid4())
            api_key = secrets.token_urlsafe(32)
            
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO api_keys
                    (key_id, user_id, key_name, api_key, organization_id,
                     permissions, is_active, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    key_id, user_id, key_name, api_key, organization_id,
                    json.dumps(permissions) if permissions else None,
                    True, datetime.utcnow(), expires_at
                ))
                
                logger.info("api_key_created", key_id=key_id, user_id=user_id)
                
                return {
                    "key_id": key_id,
                    "api_key": api_key,
                    "user_id": user_id,
                    "key_name": key_name
                }
                
        except Exception as e:
            logger.error("create_api_key_failed", error=str(e))
            raise DatabaseError(f"Failed to create API key: {str(e)}")
    
    @staticmethod
    def get_api_key(key_id: str) -> Dict:
        """Get API key by ID"""
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT key_id, user_id, key_name, api_key, organization_id,
                           permissions, is_active, created_at, expires_at, last_used_at
                    FROM api_keys
                    WHERE key_id = %s
                """
                cursor.execute(query, (key_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("APIKey", key_id)
                
                # Parse permissions JSON
                if result.get('permissions'):
                    result['permissions'] = json.loads(result['permissions'])
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_api_key_failed", error=str(e))
            raise DatabaseError(f"Failed to get API key: {str(e)}")
    
    @staticmethod
    def list_api_keys(
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """List API keys"""
        try:
            with get_db_cursor() as cursor:
                where_clauses = []
                params = []
                
                if user_id:
                    where_clauses.append("user_id = %s")
                    params.append(user_id)
                
                if is_active is not None:
                    where_clauses.append("is_active = %s")
                    params.append(is_active)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                query = f"""
                    SELECT key_id, user_id, key_name, organization_id,
                           permissions, is_active, created_at, expires_at, last_used_at
                    FROM api_keys
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                
                # Parse permissions JSON
                for result in results:
                    if result.get('permissions'):
                        result['permissions'] = json.loads(result['permissions'])
                
                return results
                
        except Exception as e:
            logger.error("list_api_keys_failed", error=str(e))
            raise DatabaseError(f"Failed to list API keys: {str(e)}")
    
    @staticmethod
    def delete_api_key(key_id: str) -> None:
        """Delete API key"""
        try:
            with get_db_cursor() as cursor:
                query = "DELETE FROM api_keys WHERE key_id = %s"
                cursor.execute(query, (key_id,))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("APIKey", key_id)
                
                logger.info("api_key_deleted", key_id=key_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("delete_api_key_failed", error=str(e))
            raise DatabaseError(f"Failed to delete API key: {str(e)}")

