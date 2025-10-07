"""Core proposal evaluator engine with three-part analysis"""
from typing import Tuple, Dict, Optional
import uuid
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.llm import LLMService
from services.pdf_service import PDFService
from services.logger import get_logger
from db.evaluator_db import EvaluatorDB
from schemas.evaluator import (
    EvaluatorRequest, EvaluatorResponse, EvaluationSection,
    EvaluatorFollowupRequest, EvaluatorFollowupResponse
)
from services.prompts import (
    format_proposal_summary_prompt,
    format_tor_summary_prompt,
    format_p_internal_prompt,
    format_p_external_prompt,
    format_p_delta_prompt,
    format_evaluator_followup_prompt
)

logger = get_logger(__name__)


class ProposalEvaluator:
    """Core proposal evaluator engine"""
    
    def __init__(self):
        """Initialize evaluator engine"""
        self.llm_service = LLMService()
        self.pdf_service = PDFService()
        self.db = EvaluatorDB()
        
        logger.info("evaluator_engine_initialized")
    
    async def process_proposal(self, text_input: Optional[str], file_data: Optional[bytes]) -> Tuple[str, Optional[str]]:
        """
        Process proposal document (text or PDF)
        
        Args:
            text_input: Proposal text
            file_data: Proposal PDF bytes
            
        Returns:
            Tuple of (proposal_text, s3_url)
        """
        try:
            proposal_text = ""
            proposal_url = None
            
            if text_input:
                proposal_text = text_input
                logger.info("proposal_from_text", length=len(text_input))
            elif file_data:
                # Extract text from PDF
                proposal_text = await self.pdf_service.extract_text_from_pdf(file_data)
                
                # Optionally upload to S3
                # proposal_url = await self.s3_service.upload_file(file_data, f"proposals/{uuid.uuid4()}.pdf")
                
                logger.info("proposal_from_pdf", length=len(proposal_text))
            
            return proposal_text, proposal_url
            
        except Exception as e:
            logger.error("process_proposal_failed", error=str(e))
            raise
    
    async def process_tor(self, text_input: Optional[str], file_data: Optional[bytes]) -> Tuple[str, Optional[str]]:
        """
        Process ToR document (text or PDF)
        
        Args:
            text_input: ToR text
            file_data: ToR PDF bytes
            
        Returns:
            Tuple of (tor_text, s3_url)
        """
        try:
            tor_text = ""
            tor_url = None
            
            if text_input:
                tor_text = text_input
                logger.info("tor_from_text", length=len(text_input))
            elif file_data:
                # Extract text from PDF
                tor_text = await self.pdf_service.extract_text_from_pdf(file_data)
                
                # Optionally upload to S3
                # tor_url = await self.s3_service.upload_file(file_data, f"tors/{uuid.uuid4()}.pdf")
                
                logger.info("tor_from_pdf", length=len(tor_text))
            
            return tor_text, tor_url
            
        except Exception as e:
            logger.error("process_tor_failed", error=str(e))
            raise
    
    async def summarize_proposal(self, proposal_text: str) -> str:
        """
        Summarize proposal using LLM
        
        Args:
            proposal_text: Full proposal text
            
        Returns:
            Proposal summary
        """
        try:
            prompt = format_proposal_summary_prompt(proposal_text)
            
            summary = self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.5,
                max_tokens=800
            )
            
            logger.info("proposal_summarized", summary_length=len(summary))
            return summary
            
        except Exception as e:
            logger.error("summarize_proposal_failed", error=str(e))
            return proposal_text[:2000]  # Fallback to truncated text
    
    async def summarize_tor(self, tor_text: str) -> str:
        """
        Summarize ToR using LLM
        
        Args:
            tor_text: Full ToR text
            
        Returns:
            ToR summary
        """
        try:
            prompt = format_tor_summary_prompt(tor_text)
            
            summary = self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.5,
                max_tokens=800
            )
            
            logger.info("tor_summarized", summary_length=len(summary))
            return summary
            
        except Exception as e:
            logger.error("summarize_tor_failed", error=str(e))
            return tor_text[:2000]  # Fallback to truncated text
    
    def parse_analysis_response(self, response: str, section_type: str) -> Dict:
        """
        Parse LLM analysis response into structured format
        
        Args:
            response: LLM response text
            section_type: P_Internal, P_External, or P_Delta
            
        Returns:
            Dict with parsed analysis
        """
        try:
            # Extract score
            score = None
            score_match = re.search(r'\*\*SCORE\*\*:\s*\[?(\d+(?:\.\d+)?)', response, re.IGNORECASE)
            if score_match:
                score = float(score_match.group(1))
            
            # Extract strengths
            strengths = []
            strengths_section = re.search(r'\*\*STRENGTHS\*\*:(.*?)(?:\*\*|$)', response, re.DOTALL | re.IGNORECASE)
            if strengths_section:
                strength_lines = strengths_section.group(1).strip().split('\n')
                strengths = [line.strip('- ').strip() for line in strength_lines if line.strip().startswith('-')]
            
            # Extract gaps/critical gaps/minor gaps
            gaps = []
            gaps_section = re.search(r'\*\*(GAPS|CRITICAL GAPS|MINOR GAPS)\*\*:(.*?)(?:\*\*|$)', response, re.DOTALL | re.IGNORECASE)
            if gaps_section:
                gap_lines = gaps_section.group(2).strip().split('\n')
                gaps = [line.strip('- ').strip() for line in gap_lines if line.strip().startswith('-')]
            
            # Extract recommendations
            recommendations = []
            recs_section = re.search(r'\*\*RECOMMENDATIONS\*\*:(.*?)(?:\*\*|$)', response, re.DOTALL | re.IGNORECASE)
            if recs_section:
                rec_lines = recs_section.group(1).strip().split('\n')
                recommendations = [line.strip('- ').strip() for line in rec_lines if line.strip().startswith('-')]
            
            # Extract detailed analysis
            content = response
            analysis_section = re.search(r'\*\*DETAILED ANALYSIS\*\*:(.*?)$', response, re.DOTALL | re.IGNORECASE)
            if analysis_section:
                content = analysis_section.group(1).strip()
            
            # Determine title based on section type
            titles = {
                'P_Internal': 'Internal Consistency Analysis',
                'P_External': 'ToR Alignment Analysis',
                'P_Delta': 'Gap Analysis'
            }
            title = titles.get(section_type, 'Analysis')
            
            return {
                'section_type': section_type,
                'title': title,
                'content': content,
                'score': score,
                'gaps': gaps,
                'strengths': strengths,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error("parse_analysis_failed", error=str(e), section=section_type)
            # Return minimal structure
            return {
                'section_type': section_type,
                'title': f'{section_type} Analysis',
                'content': response,
                'score': None,
                'gaps': [],
                'strengths': [],
                'recommendations': []
            }
    
    async def run_analysis(
        self,
        analysis_type: str,
        proposal_summary: str,
        tor_summary: str,
        guidelines: str,
        internal_insights: str = "",
        external_insights: str = ""
    ) -> Dict:
        """
        Run a single analysis (P_Internal, P_External, or P_Delta)
        
        Args:
            analysis_type: Type of analysis
            proposal_summary: Proposal summary
            tor_summary: ToR summary
            guidelines: Organization guidelines
            internal_insights: Internal analysis insights (for P_Delta)
            external_insights: External analysis insights (for P_Delta)
            
        Returns:
            Analysis results dict
        """
        try:
            # Format appropriate prompt
            if analysis_type == 'P_Internal':
                prompt = format_p_internal_prompt(proposal_summary, guidelines)
            elif analysis_type == 'P_External':
                prompt = format_p_external_prompt(proposal_summary, tor_summary, guidelines)
            elif analysis_type == 'P_Delta':
                prompt = format_p_delta_prompt(
                    proposal_summary, tor_summary, internal_insights, external_insights
                )
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            # Call LLM
            response = self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse response
            analysis = self.parse_analysis_response(response, analysis_type)
            
            logger.info(f"{analysis_type}_analysis_complete", score=analysis.get('score'))
            return analysis
            
        except Exception as e:
            logger.error(f"{analysis_type}_analysis_failed", error=str(e))
            raise
    
    async def evaluate(self, request: EvaluatorRequest) -> EvaluatorResponse:
        """
        Main evaluation method - runs complete three-part analysis
        
        Args:
            request: Evaluation request
            
        Returns:
            Evaluation response with three analyses
        """
        try:
            start_time = time.time()
            
            # Generate session ID if not provided
            session_id = request.session_id or str(uuid.uuid4())
            
            logger.info(
                "evaluation_request_received",
                user_id=request.user_id,
                session_id=session_id,
                has_organization=bool(request.organization_id)
            )
            
            # Step 1: Process proposal and ToR
            proposal_text, proposal_url = await self.process_proposal(
                request.proposal_text_input,
                request.proposal_file_data
            )
            
            tor_text, tor_url = await self.process_tor(
                request.tor_text_input,
                request.tor_file_data
            )
            
            # Step 2: Create session in database
            self.db.create_session(
                user_id=request.user_id,
                session_id=session_id,
                user_name=request.user_name,
                document_type=request.document_type.value,
                organization_id=request.organization_id,
                guideline_id=request.org_guideline_id,
                proposal_text=proposal_text[:10000],  # Store truncated for reference
                proposal_url=proposal_url,
                tor_text=tor_text[:10000],  # Store truncated for reference
                tor_url=tor_url
            )
            
            # Step 3: Get organization guidelines if provided
            guidelines = ""
            if request.organization_id:
                guidelines_list = self.db.get_organization_guidelines(
                    request.organization_id,
                    request.org_guideline_id
                )
                if guidelines_list:
                    guidelines = "\n\n".join([g['guideline_text'] for g in guidelines_list])
                    logger.info("guidelines_retrieved", count=len(guidelines_list))
            
            # Step 4: Summarize documents
            proposal_summary = await self.summarize_proposal(proposal_text)
            tor_summary = await self.summarize_tor(tor_text)
            
            # Step 5: Run three analyses in parallel
            logger.info("starting_parallel_analyses")
            
            internal_result = None
            external_result = None
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Start first two analyses
                internal_future = executor.submit(
                    lambda: self.run_analysis('P_Internal', proposal_summary, tor_summary, guidelines)
                )
                external_future = executor.submit(
                    lambda: self.run_analysis('P_External', proposal_summary, tor_summary, guidelines)
                )
                
                # Wait for first two to complete
                internal_result = internal_future.result(timeout=180)
                external_result = external_future.result(timeout=180)
            
            # Run delta analysis after getting insights from first two
            internal_insights = internal_result.get('content', '')[:500]
            external_insights = external_result.get('content', '')[:500]
            
            delta_result = await self.run_analysis(
                'P_Delta',
                proposal_summary,
                tor_summary,
                guidelines,
                internal_insights,
                external_insights
            )
            
            # Step 6: Calculate overall score
            scores = [
                internal_result.get('score'),
                external_result.get('score'),
                delta_result.get('score')
            ]
            valid_scores = [s for s in scores if s is not None]
            overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else None
            
            processing_time = time.time() - start_time
            
            # Step 7: Save results to database
            self.db.save_evaluation_results(
                session_id=session_id,
                internal_analysis=internal_result,
                external_analysis=external_result,
                delta_analysis=delta_result,
                overall_score=overall_score,
                processing_time=processing_time
            )
            
            # Step 8: Build response
            response = EvaluatorResponse(
                session_id=session_id,
                user_id=request.user_id,
                internal_analysis=EvaluationSection(**internal_result),
                external_analysis=EvaluationSection(**external_result),
                delta_analysis=EvaluationSection(**delta_result),
                overall_score=overall_score,
                processing_time_seconds=processing_time
            )
            
            logger.info(
                "evaluation_complete",
                session_id=session_id,
                overall_score=overall_score,
                processing_time=processing_time
            )
            
            return response
            
        except Exception as e:
            logger.error("evaluation_failed", error=str(e), exc_info=True)
            raise
    
    async def answer_followup(self, request: EvaluatorFollowupRequest) -> EvaluatorFollowupResponse:
        """
        Answer follow-up question about evaluation
        
        Args:
            request: Followup request
            
        Returns:
            Followup response with answer
        """
        try:
            logger.info(
                "followup_request_received",
                session_id=request.session_id,
                section=request.section
            )
            
            # Get session data
            session = self.db.get_session(request.session_id)
            if not session:
                raise ValueError(f"Session not found: {request.session_id}")
            
            # Build evaluation summary for context
            eval_summary_parts = []
            
            if session.get('internal_analysis'):
                eval_summary_parts.append(f"**Internal Analysis**: {session['internal_analysis'].get('content', '')[:300]}")
            
            if session.get('external_analysis'):
                eval_summary_parts.append(f"**External Analysis**: {session['external_analysis'].get('content', '')[:300]}")
            
            if session.get('delta_analysis'):
                eval_summary_parts.append(f"**Gap Analysis**: {session['delta_analysis'].get('content', '')[:300]}")
            
            evaluation_summary = "\n\n".join(eval_summary_parts)
            
            # Format prompt
            prompt = format_evaluator_followup_prompt(
                evaluation_summary=evaluation_summary,
                question=request.query,
                section=request.section or ""
            )
            
            # Generate answer
            answer = self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.7,
                max_tokens=600
            )
            
            # Save followup
            self.db.save_followup(
                session_id=request.session_id,
                user_id=request.user_id,
                query=request.query,
                answer=answer,
                section=request.section
            )
            
            response = EvaluatorFollowupResponse(
                session_id=request.session_id,
                query=request.query,
                answer=answer,
                section=request.section
            )
            
            logger.info("followup_answered", session_id=request.session_id)
            return response
            
        except Exception as e:
            logger.error("followup_failed", error=str(e), exc_info=True)
            raise

