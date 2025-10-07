"""
Organization access control utilities

Provides email-based organization detection and three-tier guideline access control:
1. Organization's own private guidelines
2. Public guidelines mapped to the organization (admin-controlled)
3. Universal public guidelines (available to all)
"""

from typing import Optional, List, Dict, Set, Tuple
import json
import os
from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import AuthorizationError, DatabaseError

logger = get_logger(__name__)


def get_organization_from_email(email: str) -> Optional[str]:
    """
    Extract organization ID from user email domain
    
    Checks the database for organizations with matching email domains.
    Falls back to environment variable mapping if needed.
    
    Args:
        email: User email address
        
    Returns:
        Organization ID or None if no match found
        
    Example:
        >>> get_organization_from_email("john@unicef.org")
        'org-unicef'
    """
    try:
        if not email or '@' not in email:
            logger.warning("invalid_email_format", email=email)
            return None
        
        domain = email.split('@')[-1].lower()
        
        # Check database for organization with this domain
        with get_db_cursor() as cursor:
            query = """
                SELECT organization_id, organization_name, email_domains
                FROM organizations
                WHERE is_active = TRUE
                  AND email_domains IS NOT NULL
            """
            cursor.execute(query)
            organizations = cursor.fetchall()
            
            # Check each organization's domains
            for org in organizations:
                domains = org.get('email_domains', [])
                
                # Handle both JSON string and list
                if isinstance(domains, str):
                    try:
                        domains = json.loads(domains)
                    except json.JSONDecodeError:
                        logger.warning("invalid_json_domains", org_id=org['organization_id'])
                        continue
                
                # Match domain (case-insensitive)
                if domain in [d.lower() for d in domains]:
                    logger.info(
                        "org_resolved_from_email",
                        email=email,
                        domain=domain,
                        org_id=org['organization_id']
                    )
                    return org['organization_id']
        
        # Fallback: check environment variable mapping
        try:
            env_mappings = json.loads(os.getenv('ORG_EMAIL_DOMAINS', '{}'))
            org_id = env_mappings.get(domain)
            if org_id:
                logger.info("org_resolved_from_env", domain=domain, org_id=org_id)
                return org_id
        except json.JSONDecodeError:
            logger.error("invalid_env_mappings", env_var="ORG_EMAIL_DOMAINS")
        
        logger.warning("no_org_for_domain", domain=domain, email=email)
        return None
        
    except Exception as e:
        logger.error("get_org_from_email_failed", error=str(e), email=email)
        return None


def get_accessible_guidelines(
    user_email: str,
    requested_org_id: Optional[str] = None
) -> List[Dict]:
    """
    Get all guidelines accessible to user including:
    1. Their organization's private guidelines
    2. Public guidelines mapped to their organization (admin-controlled)
    3. Universal public guidelines
    
    Args:
        user_email: User email address
        requested_org_id: Specific organization to filter by (optional)
        
    Returns:
        List of accessible guideline dictionaries with 'access_type' field
        
    Example:
        >>> guidelines = get_accessible_guidelines("john@unicef.org")
        >>> len([g for g in guidelines if g['access_type'] == 'organization'])
        5  # UNICEF's own guidelines
    """
    try:
        user_org_id = get_organization_from_email(user_email)
        
        if not user_org_id:
            logger.warning("no_org_no_guidelines", user_email=user_email)
            # Only return universal public guidelines for users without org
            return _get_universal_guidelines()
        
        with get_db_cursor() as cursor:
            # Build the query for three types of guidelines
            query = """
                -- 1. Organization's own private guidelines
                SELECT DISTINCT
                    g.guideline_id, g.organization_id, g.guideline_name,
                    g.guideline_text, g.description, g.is_active,
                    g.is_public, g.visibility_scope,
                    g.created_at, g.updated_at,
                    'organization' as access_type
                FROM organization_guidelines g
                WHERE g.organization_id = %s
                  AND g.is_active = TRUE
                  AND (g.is_public = FALSE OR g.visibility_scope = 'organization')
                
                UNION
                
                -- 2. Public guidelines mapped to this organization
                SELECT DISTINCT
                    g.guideline_id, g.organization_id, g.guideline_name,
                    g.guideline_text, g.description, g.is_active,
                    g.is_public, g.visibility_scope,
                    g.created_at, g.updated_at,
                    'public_mapped' as access_type
                FROM organization_guidelines g
                INNER JOIN organization_guideline_access oga
                    ON g.guideline_id = oga.guideline_id
                WHERE oga.organization_id = %s
                  AND g.is_active = TRUE
                  AND g.is_public = TRUE
                  AND g.visibility_scope = 'public_mapped'
                
                UNION
                
                -- 3. Universal public guidelines (available to all)
                SELECT DISTINCT
                    g.guideline_id, g.organization_id, g.guideline_name,
                    g.guideline_text, g.description, g.is_active,
                    g.is_public, g.visibility_scope,
                    g.created_at, g.updated_at,
                    'universal' as access_type
                FROM organization_guidelines g
                WHERE g.is_active = TRUE
                  AND g.is_public = TRUE
                  AND g.visibility_scope = 'universal'
                
                ORDER BY access_type, guideline_name
            """
            
            cursor.execute(query, (user_org_id, user_org_id))
            guidelines = cursor.fetchall()
            
            # Filter by requested org if specified
            if requested_org_id:
                guidelines = [
                    g for g in guidelines 
                    if g['organization_id'] == requested_org_id or 
                       g['access_type'] in ('public_mapped', 'universal')
                ]
            
            logger.info(
                "guidelines_retrieved",
                user_org=user_org_id,
                user_email=user_email,
                total_count=len(guidelines),
                by_type={
                    'organization': len([g for g in guidelines if g['access_type'] == 'organization']),
                    'public_mapped': len([g for g in guidelines if g['access_type'] == 'public_mapped']),
                    'universal': len([g for g in guidelines if g['access_type'] == 'universal'])
                }
            )
            
            return guidelines
            
    except Exception as e:
        logger.error("get_accessible_guidelines_failed", error=str(e), user_email=user_email)
        raise DatabaseError(f"Failed to get accessible guidelines: {str(e)}")


def _get_universal_guidelines() -> List[Dict]:
    """
    Get only universal public guidelines
    
    These are available to all users, regardless of organization.
    
    Returns:
        List of universal guideline dictionaries
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT guideline_id, organization_id, guideline_name,
                       guideline_text, description, is_active,
                       is_public, visibility_scope,
                       created_at, updated_at,
                       'universal' as access_type
                FROM organization_guidelines
                WHERE is_active = TRUE
                  AND is_public = TRUE
                  AND visibility_scope = 'universal'
                ORDER BY guideline_name
            """
            cursor.execute(query)
            guidelines = cursor.fetchall()
            
            logger.info("universal_guidelines_retrieved", count=len(guidelines))
            return guidelines
            
    except Exception as e:
        logger.error("get_universal_guidelines_failed", error=str(e))
        return []


def can_access_specific_guideline(
    user_email: str,
    guideline_id: str
) -> Tuple[bool, str]:
    """
    Check if user can access a specific guideline
    
    Args:
        user_email: User email
        guideline_id: Guideline identifier
        
    Returns:
        Tuple of (can_access: bool, reason: str)
        
    Example:
        >>> can_access, reason = can_access_specific_guideline(
        ...     "john@unicef.org", 
        ...     "guideline-unicef-001"
        ... )
        >>> print(can_access, reason)
        True "Organization's own guideline"
    """
    try:
        user_org_id = get_organization_from_email(user_email)
        
        with get_db_cursor() as cursor:
            # Get the guideline
            query = """
                SELECT organization_id, is_public, visibility_scope, is_active
                FROM organization_guidelines
                WHERE guideline_id = %s
            """
            cursor.execute(query, (guideline_id,))
            guideline = cursor.fetchone()
            
            if not guideline:
                return False, "Guideline not found"
            
            if not guideline['is_active']:
                return False, "Guideline is inactive"
            
            # Universal public - everyone can access
            if guideline['is_public'] and guideline['visibility_scope'] == 'universal':
                return True, "Universal public guideline"
            
            # No organization - can only access universal
            if not user_org_id:
                return False, "User has no organization"
            
            # Organization's own guideline
            if guideline['organization_id'] == user_org_id:
                return True, "Organization's own guideline"
            
            # Public mapped - check if access granted
            if guideline['is_public'] and guideline['visibility_scope'] == 'public_mapped':
                query = """
                    SELECT COUNT(*) as count
                    FROM organization_guideline_access
                    WHERE organization_id = %s AND guideline_id = %s
                """
                cursor.execute(query, (user_org_id, guideline_id))
                result = cursor.fetchone()
                
                if result and result['count'] > 0:
                    return True, "Public guideline mapped to organization"
            
            return False, "Access denied"
            
    except Exception as e:
        logger.error("can_access_guideline_failed", error=str(e))
        return False, f"Error checking access: {str(e)}"


def verify_guideline_access(
    user_email: str,
    guideline_org_id: str
) -> bool:
    """
    Verify if user can access guidelines from specific organization
    
    Args:
        user_email: User email
        guideline_org_id: Organization ID of the guideline
        
    Returns:
        True if access granted
        
    Raises:
        AuthorizationError if access denied
    """
    user_org = get_organization_from_email(user_email)
    
    # If user has no organization, deny access to org-specific guidelines
    if not user_org:
        logger.warning(
            "access_denied_no_org",
            user_email=user_email,
            requested_org=guideline_org_id
        )
        raise AuthorizationError(
            f"User from domain not authorized to access {guideline_org_id} guidelines"
        )
    
    # User can only access their organization's guidelines
    if user_org != guideline_org_id:
        logger.warning(
            "access_denied_wrong_org",
            user_email=user_email,
            user_org=user_org,
            requested_org=guideline_org_id
        )
        raise AuthorizationError(
            f"Access denied: User belongs to {user_org}, not {guideline_org_id}"
        )
    
    logger.info("guideline_access_granted", user_email=user_email, org=user_org)
    return True


def get_accessible_guideline_ids(
    user_email: str,
    organization_id: str
) -> Set[str]:
    """
    Get set of guideline IDs user can access
    
    Args:
        user_email: User email
        organization_id: Organization ID
        
    Returns:
        Set of accessible guideline IDs
    """
    try:
        guidelines = get_accessible_guidelines(user_email, organization_id)
        return {g['guideline_id'] for g in guidelines}
    except Exception as e:
        logger.error("get_accessible_ids_failed", error=str(e))
        return set()


def log_guideline_access(
    user_id: str,
    user_email: str,
    organization_id: str,
    guideline_id: str,
    access_granted: bool,
    access_reason: str,
    session_id: Optional[str] = None
) -> None:
    """
    Log guideline access attempt for audit
    
    Args:
        user_id: User identifier
        user_email: User email
        organization_id: Organization ID
        guideline_id: Guideline ID
        access_granted: Whether access was granted
        access_reason: Reason for decision
        session_id: Optional session ID
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                INSERT INTO guideline_access_log
                (user_id, user_email, organization_id, guideline_id,
                 access_granted, access_reason, session_id, accessed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (
                user_id, user_email.lower(), organization_id, guideline_id,
                access_granted, access_reason, session_id
            ))
            
            logger.debug(
                "access_logged",
                user_id=user_id,
                guideline_id=guideline_id,
                granted=access_granted
            )
            
    except Exception as e:
        logger.error("log_access_failed", error=str(e))
        # Don't raise - logging failure shouldn't break access
