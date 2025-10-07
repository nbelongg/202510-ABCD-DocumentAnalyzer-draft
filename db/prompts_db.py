"""Database operations for prompt management"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)


class PromptsDB:
    """Database operations for prompt configuration"""
    
    @staticmethod
    def get_prompt_config(
        prompt_label: str,
        document_type: str,
        organization_id: Optional[str] = None
    ) -> Dict:
        """
        Get prompt configuration
        
        Args:
            prompt_label: Prompt label (e.g., P1, P2, P3)
            document_type: Document type
            organization_id: Optional organization for custom prompts
            
        Returns:
            Prompt configuration dict
        """
        try:
            with get_db_cursor() as cursor:
                # Try organization-specific first
                if organization_id:
                    query = """
                        SELECT prompt_id, prompt_label, document_type,
                               base_prompt, customization_prompt, system_prompt,
                               temperature, max_tokens, use_corpus, corpus_id,
                               num_examples, created_at, updated_at
                        FROM analyzer_prompts
                        WHERE prompt_label = %s AND document_type = %s
                          AND (organization_id = %s OR organization_id IS NULL)
                        ORDER BY organization_id DESC
                        LIMIT 1
                    """
                    cursor.execute(query, (prompt_label, document_type, organization_id))
                else:
                    # Default prompts
                    query = """
                        SELECT prompt_id, prompt_label, document_type,
                               base_prompt, customization_prompt, system_prompt,
                               temperature, max_tokens, use_corpus, corpus_id,
                               num_examples, created_at, updated_at
                        FROM analyzer_prompts
                        WHERE prompt_label = %s AND document_type = %s
                          AND organization_id IS NULL
                        LIMIT 1
                    """
                    cursor.execute(query, (prompt_label, document_type))
                
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("Prompt", f"{prompt_label}/{document_type}")
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_prompt_config_failed", error=str(e))
            raise DatabaseError(f"Failed to get prompt config: {str(e)}")
    
    @staticmethod
    def get_all_prompts_for_document(
        document_type: str,
        prompt_labels: List[str],
        organization_id: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Get all prompts for a document type
        
        Args:
            document_type: Document type
            prompt_labels: List of prompt labels to fetch
            organization_id: Optional organization ID
            
        Returns:
            Dictionary mapping label to prompt config
        """
        results = {}
        
        for label in prompt_labels:
            try:
                config = PromptsDB.get_prompt_config(label, document_type, organization_id)
                results[label] = config
            except NotFoundError:
                logger.warning("prompt_not_found", label=label, document_type=document_type)
                continue
        
        return results
    
    @staticmethod
    def update_prompt(
        prompt_label: str,
        document_type: str,
        base_prompt: Optional[str] = None,
        customization_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> None:
        """
        Update prompt configuration
        
        Args:
            prompt_label: Prompt label
            document_type: Document type
            base_prompt: Updated base prompt
            customization_prompt: Updated customization prompt
            system_prompt: Updated system prompt
            organization_id: Optional organization ID
        """
        try:
            with get_db_cursor() as cursor:
                # Build dynamic update query
                updates = []
                params = []
                
                if base_prompt is not None:
                    updates.append("base_prompt = %s")
                    params.append(base_prompt)
                
                if customization_prompt is not None:
                    updates.append("customization_prompt = %s")
                    params.append(customization_prompt)
                
                if system_prompt is not None:
                    updates.append("system_prompt = %s")
                    params.append(system_prompt)
                
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                
                # Add WHERE conditions
                params.extend([prompt_label, document_type])
                
                query = f"""
                    UPDATE analyzer_prompts
                    SET {', '.join(updates)}
                    WHERE prompt_label = %s AND document_type = %s
                """
                
                if organization_id:
                    query += " AND organization_id = %s"
                    params.append(organization_id)
                else:
                    query += " AND organization_id IS NULL"
                
                cursor.execute(query, tuple(params))
                
                logger.info("prompt_updated", label=prompt_label, document_type=document_type)
                
        except Exception as e:
            logger.error("update_prompt_failed", error=str(e))
            raise DatabaseError(f"Failed to update prompt: {str(e)}")
    
    # ==================== GENERIC PROMPT CRUD OPERATIONS ====================
    
    @staticmethod
    def create_prompt(
        prompt_type: str,
        prompt_name: str,
        prompt_text: str,
        description: Optional[str] = None,
        version: str = "1.0",
        is_active: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new prompt
        
        Args:
            prompt_type: Type of prompt (analyzer, evaluator, chatbot, summary, custom)
            prompt_name: Unique prompt name
            prompt_text: Full prompt template text
            description: Optional description
            version: Prompt version
            is_active: Whether prompt is active
            metadata: Additional metadata as JSON
            
        Returns:
            Created prompt ID
        """
        try:
            prompt_id = str(uuid.uuid4())
            
            with get_db_cursor() as cursor:
                query = """
                    INSERT INTO prompts
                    (prompt_id, prompt_type, prompt_name, prompt_text, description,
                     version, is_active, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    prompt_id, prompt_type, prompt_name, prompt_text, description,
                    version, is_active, json.dumps(metadata) if metadata else None,
                    datetime.utcnow()
                ))
                
                logger.info("prompt_created", prompt_id=prompt_id, prompt_name=prompt_name)
                return prompt_id
                
        except Exception as e:
            logger.error("create_prompt_failed", error=str(e))
            raise DatabaseError(f"Failed to create prompt: {str(e)}")
    
    @staticmethod
    def get_prompt_by_id(prompt_id: str) -> Dict:
        """
        Get prompt by ID
        
        Args:
            prompt_id: Prompt identifier
            
        Returns:
            Prompt dictionary
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT prompt_id, prompt_type, prompt_name, prompt_text,
                           description, version, is_active, metadata,
                           created_at, updated_at
                    FROM prompts
                    WHERE prompt_id = %s
                """
                cursor.execute(query, (prompt_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("Prompt", prompt_id)
                
                # Parse metadata JSON
                if result.get('metadata'):
                    result['metadata'] = json.loads(result['metadata'])
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_prompt_failed", error=str(e))
            raise DatabaseError(f"Failed to get prompt: {str(e)}")
    
    @staticmethod
    def get_prompt_by_name(prompt_name: str) -> Dict:
        """
        Get prompt by name
        
        Args:
            prompt_name: Prompt name
            
        Returns:
            Prompt dictionary
        """
        try:
            with get_db_cursor() as cursor:
                query = """
                    SELECT prompt_id, prompt_type, prompt_name, prompt_text,
                           description, version, is_active, metadata,
                           created_at, updated_at
                    FROM prompts
                    WHERE prompt_name = %s
                """
                cursor.execute(query, (prompt_name,))
                result = cursor.fetchone()
                
                if not result:
                    raise NotFoundError("Prompt", prompt_name)
                
                # Parse metadata JSON
                if result.get('metadata'):
                    result['metadata'] = json.loads(result['metadata'])
                
                return result
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("get_prompt_by_name_failed", error=str(e))
            raise DatabaseError(f"Failed to get prompt by name: {str(e)}")
    
    @staticmethod
    def list_prompts(
        prompt_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List prompts with optional filtering
        
        Args:
            prompt_type: Filter by prompt type
            is_active: Filter by active status
            limit: Maximum number of prompts
            offset: Offset for pagination
            
        Returns:
            List of prompt dictionaries
        """
        try:
            with get_db_cursor() as cursor:
                # Build dynamic query
                where_clauses = []
                params = []
                
                if prompt_type:
                    where_clauses.append("prompt_type = %s")
                    params.append(prompt_type)
                
                if is_active is not None:
                    where_clauses.append("is_active = %s")
                    params.append(is_active)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                query = f"""
                    SELECT prompt_id, prompt_type, prompt_name, prompt_text,
                           description, version, is_active, metadata,
                           created_at, updated_at
                    FROM prompts
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                params.extend([limit, offset])
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                
                # Parse metadata JSON for each result
                for result in results:
                    if result.get('metadata'):
                        result['metadata'] = json.loads(result['metadata'])
                
                return results
                
        except Exception as e:
            logger.error("list_prompts_failed", error=str(e))
            raise DatabaseError(f"Failed to list prompts: {str(e)}")
    
    @staticmethod
    def update_prompt_by_id(
        prompt_id: str,
        prompt_text: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update prompt by ID
        
        Args:
            prompt_id: Prompt identifier
            prompt_text: Updated prompt text
            description: Updated description
            version: Updated version
            is_active: Updated active status
            metadata: Updated metadata
        """
        try:
            with get_db_cursor() as cursor:
                # Build dynamic update query
                updates = []
                params = []
                
                if prompt_text is not None:
                    updates.append("prompt_text = %s")
                    params.append(prompt_text)
                
                if description is not None:
                    updates.append("description = %s")
                    params.append(description)
                
                if version is not None:
                    updates.append("version = %s")
                    params.append(version)
                
                if is_active is not None:
                    updates.append("is_active = %s")
                    params.append(is_active)
                
                if metadata is not None:
                    updates.append("metadata = %s")
                    params.append(json.dumps(metadata))
                
                if not updates:
                    logger.warning("no_updates_provided", prompt_id=prompt_id)
                    return
                
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                
                params.append(prompt_id)
                
                query = f"""
                    UPDATE prompts
                    SET {', '.join(updates)}
                    WHERE prompt_id = %s
                """
                
                cursor.execute(query, tuple(params))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("Prompt", prompt_id)
                
                logger.info("prompt_updated", prompt_id=prompt_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("update_prompt_by_id_failed", error=str(e))
            raise DatabaseError(f"Failed to update prompt: {str(e)}")
    
    @staticmethod
    def delete_prompt(prompt_id: str) -> None:
        """
        Delete prompt by ID
        
        Args:
            prompt_id: Prompt identifier
        """
        try:
            with get_db_cursor() as cursor:
                query = "DELETE FROM prompts WHERE prompt_id = %s"
                cursor.execute(query, (prompt_id,))
                
                if cursor.rowcount == 0:
                    raise NotFoundError("Prompt", prompt_id)
                
                logger.info("prompt_deleted", prompt_id=prompt_id)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("delete_prompt_failed", error=str(e))
            raise DatabaseError(f"Failed to delete prompt: {str(e)}")
    
    @staticmethod
    def batch_delete_prompts(prompt_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple prompts
        
        Args:
            prompt_ids: List of prompt identifiers
            
        Returns:
            Dictionary with success/failure counts
        """
        success_count = 0
        failed_ids = []
        
        for prompt_id in prompt_ids:
            try:
                PromptsDB.delete_prompt(prompt_id)
                success_count += 1
            except Exception as e:
                logger.error("batch_delete_failed_for_prompt", prompt_id=prompt_id, error=str(e))
                failed_ids.append(prompt_id)
        
        return {
            "success_count": success_count,
            "failure_count": len(failed_ids),
            "failed_ids": failed_ids
        }

