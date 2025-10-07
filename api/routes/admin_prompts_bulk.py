"""
Admin API routes for bulk prompt operations

This module provides backwards-compatible endpoints for the legacy Colab-based
prompt management system, allowing bulk updates via CSV/pandas workflows.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)
router = APIRouter()


# ==================== SCHEMAS FOR BULK OPERATIONS ====================

class AnalyzerPromptBulkItem(BaseModel):
    """Single analyzer prompt for bulk update"""
    doc_type: str
    base_prompt: str
    customization_prompt: str = ""
    corpus_id: str = ""
    section_title: str = ""
    wisdom_1: str = ""
    wisdom_2: str = ""
    number_of_chunks: Optional[int] = None
    dependencies: str = ""
    customize_prompt_based_on: str = ""
    send_along_customised_prompt: str = ""
    which_chunks: str = ""
    wisdom_received: str = ""
    llm_flow: str = ""
    llm: str = ""
    model: str = ""
    show_on_frontend: str = ""
    label_for_output: str = ""
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4000


class EvaluatorPromptBulkItem(BaseModel):
    """Single evaluator prompt for bulk update"""
    prompt_label: str
    doc_type: str
    base_prompt: str
    customization_prompt: str = ""
    wisdom_1: str = ""
    wisdom_2: str = ""
    organization_id: str = ""
    org_guideline_id: str = ""
    section_title: str = ""
    number_of_chunks: Optional[int] = None
    additional_dependencies: str = ""
    customize_prompt_based_on: str = ""
    send_along_customised_prompt: str = ""
    wisdom_received: str = ""
    llm_flow: str = ""
    llm: str = ""
    model: str = ""
    show_on_frontend: str = ""
    label_for_output: str = ""
    prompt_corpus: str = ""


class SummaryPromptBulkItem(BaseModel):
    """Summary prompt for bulk update"""
    doc_type: str
    summary_prompt: Optional[str] = None
    proposal_prompt: Optional[str] = None
    tor_summary_prompt: Optional[str] = None
    organization_id: Optional[str] = None


class CustomPromptBulkItem(BaseModel):
    """Custom organization prompt for bulk update"""
    doc_type: str
    corpus_id: str = ""
    base_prompt: str
    customization_prompt: str = ""
    organization_id: str
    number_of_chunks: Optional[int] = None


# ==================== ANALYZER PROMPTS (P1-P5) ====================

@router.put("/update_prompts")
async def update_analyzer_prompts(
    prompt_label: str = Query(..., description="Prompt label (P1, P2, P3, P4, P5, etc.)"),
    prompts: List[AnalyzerPromptBulkItem] = ...
):
    """
    Bulk update analyzer prompts for a given prompt label
    
    **Backwards compatible with legacy Colab script**
    
    Updates or inserts prompts for different document types under the same label.
    This endpoint maintains compatibility with the existing CSV-based workflow.
    """
    try:
        logger.info("bulk_update_analyzer_prompts", prompt_label=prompt_label, count=len(prompts))
        
        updated_count = 0
        created_count = 0
        
        with get_db_cursor() as cursor:
            for prompt_item in prompts:
                # Check if prompt exists
                check_query = """
                    SELECT prompt_id FROM analyzer_prompts
                    WHERE prompt_label = %s AND document_type = %s
                      AND organization_id IS NULL
                """
                cursor.execute(check_query, (prompt_label, prompt_item.doc_type))
                existing = cursor.fetchone()
                
                # Convert corpus_id to use_corpus boolean
                use_corpus = bool(prompt_item.corpus_id)
                
                # Build metadata JSON
                metadata = {
                    "section_title": prompt_item.section_title,
                    "wisdom_1": prompt_item.wisdom_1,
                    "wisdom_2": prompt_item.wisdom_2,
                    "dependencies": prompt_item.dependencies,
                    "customize_prompt_based_on": prompt_item.customize_prompt_based_on,
                    "send_along_customised_prompt": prompt_item.send_along_customised_prompt,
                    "which_chunks": prompt_item.which_chunks,
                    "wisdom_received": prompt_item.wisdom_received,
                    "llm_flow": prompt_item.llm_flow,
                    "llm": prompt_item.llm,
                    "model": prompt_item.model,
                    "show_on_frontend": prompt_item.show_on_frontend,
                    "label_for_output": prompt_item.label_for_output
                }
                
                if existing:
                    # Update existing prompt
                    update_query = """
                        UPDATE analyzer_prompts
                        SET base_prompt = %s,
                            customization_prompt = %s,
                            system_prompt = %s,
                            corpus_id = %s,
                            temperature = %s,
                            max_tokens = %s,
                            use_corpus = %s,
                            num_examples = %s,
                            updated_at = NOW()
                        WHERE prompt_id = %s
                    """
                    cursor.execute(update_query, (
                        prompt_item.base_prompt,
                        prompt_item.customization_prompt,
                        prompt_item.system_prompt,
                        prompt_item.corpus_id,
                        prompt_item.temperature,
                        prompt_item.max_tokens,
                        use_corpus,
                        prompt_item.number_of_chunks or 5,
                        existing['prompt_id']
                    ))
                    updated_count += 1
                else:
                    # Insert new prompt
                    insert_query = """
                        INSERT INTO analyzer_prompts
                        (prompt_label, document_type, organization_id, base_prompt,
                         customization_prompt, system_prompt, temperature, max_tokens,
                         use_corpus, corpus_id, num_examples, created_at, updated_at)
                        VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    cursor.execute(insert_query, (
                        prompt_label,
                        prompt_item.doc_type,
                        prompt_item.base_prompt,
                        prompt_item.customization_prompt,
                        prompt_item.system_prompt,
                        prompt_item.temperature,
                        prompt_item.max_tokens,
                        use_corpus,
                        prompt_item.corpus_id,
                        prompt_item.number_of_chunks or 5
                    ))
                    created_count += 1
        
        logger.info(
            "analyzer_prompts_updated",
            prompt_label=prompt_label,
            created=created_count,
            updated=updated_count
        )
        
        return {
            "success": True,
            "message": f"Updated {updated_count} and created {created_count} prompts for {prompt_label}",
            "prompt_label": prompt_label,
            "total_processed": len(prompts),
            "created": created_count,
            "updated": updated_count
        }
        
    except Exception as e:
        logger.error("bulk_update_analyzer_prompts_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update analyzer prompts: {str(e)}"
        )


@router.delete("/delete_prompts")
async def delete_analyzer_prompts(
    prompt_label: str = Query(..., description="Prompt label"),
    doc_type: str = Query(..., description="Document type")
):
    """Delete analyzer prompts for specific label and document type"""
    try:
        with get_db_cursor() as cursor:
            query = """
                DELETE FROM analyzer_prompts
                WHERE prompt_label = %s AND document_type = %s
                  AND organization_id IS NULL
            """
            cursor.execute(query, (prompt_label, doc_type))
            deleted_count = cursor.rowcount
            
            if deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No prompts found for {prompt_label}/{doc_type}"
                )
            
            logger.info("analyzer_prompts_deleted", prompt_label=prompt_label, doc_type=doc_type)
            
            return {
                "success": True,
                "message": f"Deleted {deleted_count} prompts",
                "deleted_count": deleted_count
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_analyzer_prompts_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompts: {str(e)}"
        )


# ==================== EVALUATOR PROMPTS ====================

@router.put("/update_evaluator_prompts")
async def update_evaluator_prompts(
    prompts: List[EvaluatorPromptBulkItem] = ...
):
    """
    Bulk update evaluator prompts (P_Internal, P_External, P_Delta, etc.)
    
    **Backwards compatible with legacy Colab script**
    """
    try:
        logger.info("bulk_update_evaluator_prompts", count=len(prompts))
        
        updated_count = 0
        created_count = 0
        
        with get_db_cursor() as cursor:
            for prompt_item in prompts:
                # Check if exists
                check_query = """
                    SELECT id FROM evaluator_prompts
                    WHERE prompt_label = %s AND document_type = %s
                      AND organization_id = %s
                """
                cursor.execute(check_query, (
                    prompt_item.prompt_label,
                    prompt_item.doc_type,
                    prompt_item.organization_id or ''
                ))
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    update_query = """
                        UPDATE evaluator_prompts
                        SET base_prompt = %s,
                            customization_prompt = %s,
                            system_prompt = '',
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (
                        prompt_item.base_prompt,
                        prompt_item.customization_prompt,
                        existing['id']
                    ))
                    updated_count += 1
                else:
                    # Insert
                    insert_query = """
                        INSERT INTO evaluator_prompts
                        (prompt_label, document_type, organization_id, org_guideline_id,
                         base_prompt, customization_prompt, system_prompt,
                         created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, '', NOW(), NOW())
                    """
                    cursor.execute(insert_query, (
                        prompt_item.prompt_label,
                        prompt_item.doc_type,
                        prompt_item.organization_id or '',
                        prompt_item.org_guideline_id or '',
                        prompt_item.base_prompt,
                        prompt_item.customization_prompt
                    ))
                    created_count += 1
        
        logger.info("evaluator_prompts_updated", created=created_count, updated=updated_count)
        
        return {
            "success": True,
            "message": f"Updated {updated_count} and created {created_count} evaluator prompts",
            "total_processed": len(prompts),
            "created": created_count,
            "updated": updated_count
        }
        
    except Exception as e:
        logger.error("bulk_update_evaluator_prompts_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update evaluator prompts: {str(e)}"
        )


# ==================== SUMMARY PROMPTS ====================

@router.put("/update_analyzer_comments_summary_prompts")
async def update_comments_summary_prompts(
    prompts: List[SummaryPromptBulkItem] = ...
):
    """Update analyzer comments summary prompts (P0)"""
    try:
        logger.info("update_comments_summary_prompts", count=len(prompts))
        
        with get_db_cursor() as cursor:
            for prompt_item in prompts:
                # Upsert into analyzer_prompts with special label
                query = """
                    INSERT INTO analyzer_prompts
                    (prompt_label, document_type, organization_id, base_prompt,
                     customization_prompt, created_at, updated_at)
                    VALUES ('P0', %s, NULL, %s, '', NOW(), NOW())
                    ON CONFLICT (prompt_label, document_type, organization_id)
                    DO UPDATE SET
                        base_prompt = EXCLUDED.base_prompt,
                        updated_at = NOW()
                """
                cursor.execute(query, (
                    prompt_item.doc_type,
                    prompt_item.summary_prompt or ""
                ))
        
        return {"success": True, "message": f"Updated {len(prompts)} summary prompts"}
        
    except Exception as e:
        logger.error("update_summary_prompts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update_analyzer_proposal_summary_prompts")
async def update_proposal_summary_prompts(
    prompts: List[SummaryPromptBulkItem] = ...
):
    """Update proposal summary prompts (P-IS)"""
    try:
        with get_db_cursor() as cursor:
            for prompt_item in prompts:
                query = """
                    INSERT INTO analyzer_prompts
                    (prompt_label, document_type, organization_id, base_prompt,
                     customization_prompt, created_at, updated_at)
                    VALUES ('P-IS', %s, NULL, %s, '', NOW(), NOW())
                    ON CONFLICT (prompt_label, document_type, organization_id)
                    DO UPDATE SET
                        base_prompt = EXCLUDED.base_prompt,
                        updated_at = NOW()
                """
                cursor.execute(query, (
                    prompt_item.doc_type,
                    prompt_item.proposal_prompt or ""
                ))
        
        return {"success": True, "message": f"Updated {len(prompts)} proposal prompts"}
        
    except Exception as e:
        logger.error("update_proposal_prompts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update_tor_summary_prompts")
async def update_tor_summary_prompts(
    prompts: List[SummaryPromptBulkItem] = ...
):
    """Update TOR summary prompts"""
    try:
        with get_db_cursor() as cursor:
            for prompt_item in prompts:
                query = """
                    INSERT INTO analyzer_prompts
                    (prompt_label, document_type, organization_id, base_prompt,
                     customization_prompt, created_at, updated_at)
                    VALUES ('TOR-SUMMARY', %s, %s, %s, '', NOW(), NOW())
                    ON CONFLICT (prompt_label, document_type, organization_id)
                    DO UPDATE SET
                        base_prompt = EXCLUDED.base_prompt,
                        updated_at = NOW()
                """
                cursor.execute(query, (
                    prompt_item.doc_type,
                    prompt_item.organization_id or '',
                    prompt_item.tor_summary_prompt or ""
                ))
        
        return {"success": True, "message": f"Updated {len(prompts)} TOR prompts"}
        
    except Exception as e:
        logger.error("update_tor_prompts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CUSTOM PROMPTS ====================

@router.put("/update_custom_prompts")
async def update_custom_prompts(
    prompts: List[CustomPromptBulkItem] = ...
):
    """Update organization-specific custom prompts (P_Custom)"""
    try:
        logger.info("update_custom_prompts", count=len(prompts))
        
        with get_db_cursor() as cursor:
            for prompt_item in prompts:
                query = """
                    INSERT INTO analyzer_prompts
                    (prompt_label, document_type, organization_id, base_prompt,
                     customization_prompt, corpus_id, num_examples,
                     created_at, updated_at)
                    VALUES ('P_Custom', %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (prompt_label, document_type, organization_id)
                    DO UPDATE SET
                        base_prompt = EXCLUDED.base_prompt,
                        customization_prompt = EXCLUDED.customization_prompt,
                        corpus_id = EXCLUDED.corpus_id,
                        num_examples = EXCLUDED.num_examples,
                        updated_at = NOW()
                """
                cursor.execute(query, (
                    prompt_item.doc_type,
                    prompt_item.organization_id,
                    prompt_item.base_prompt,
                    prompt_item.customization_prompt,
                    prompt_item.corpus_id,
                    prompt_item.number_of_chunks or 5
                ))
        
        return {"success": True, "message": f"Updated {len(prompts)} custom prompts"}
        
    except Exception as e:
        logger.error("update_custom_prompts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete_custom_prompts")
async def delete_custom_prompts(
    organization_id: str = Query(...),
    doc_type: str = Query(...)
):
    """Delete custom prompts for organization"""
    try:
        with get_db_cursor() as cursor:
            query = """
                DELETE FROM analyzer_prompts
                WHERE prompt_label = 'P_Custom'
                  AND document_type = %s
                  AND organization_id = %s
            """
            cursor.execute(query, (doc_type, organization_id))
            deleted_count = cursor.rowcount
            
            return {
                "success": True,
                "message": f"Deleted {deleted_count} custom prompts",
                "deleted_count": deleted_count
            }
            
    except Exception as e:
        logger.error("delete_custom_prompts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
