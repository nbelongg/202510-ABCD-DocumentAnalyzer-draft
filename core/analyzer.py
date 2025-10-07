"""Document analyzer core logic"""
from typing import List, Dict, Optional
import uuid
import time
from io import BytesIO
from langsmith import traceable
from services.llm import LLMService
from services.pinecone_service import PineconeService
from services.pdf_service import PDFService
from services.s3_service import S3Service
from services.logger import get_logger
from db.analyzer_db import AnalyzerDB
from db.prompts_db import PromptsDB
from schemas.analyzer import (
    AnalyzerRequest,
    AnalyzerResponse,
    AnalyzerSectionResult,
    AnalyzerFollowupRequest
)

logger = get_logger(__name__)


class DocumentAnalyzer:
    """Core document analysis engine"""
    
    def __init__(self):
        """Initialize analyzer with required services"""
        self.llm_service = LLMService()
        self.pinecone_service = PineconeService()
        self.pdf_service = PDFService()
        self.s3_service = S3Service()
        self.db = AnalyzerDB()
        self.prompts_db = PromptsDB()
    
    @traceable(name="analyze_document", tags=["analyzer", "main"])
    async def analyze(self, request: AnalyzerRequest) -> AnalyzerResponse:
        """
        Analyze a document
        
        Args:
            request: Analysis request
            
        Returns:
            Analysis response with all sections
        """
        start_time = time.time()
        session_id = request.session_id or str(uuid.uuid4())
        
        try:
            logger.info(
                "starting_analysis",
                session_id=session_id,
                user_id=request.user_id,
                document_type=request.document_type
            )
            
            # Step 1: Extract text from document
            document_text = await self._extract_text(request)
            
            # Step 2: Store in S3 if needed
            if request.file_data:
                s3_url = await self._store_file(request, session_id)
                logger.info("file_stored", s3_url=s3_url)
            
            # Step 3: Create session in database
            self.db.create_session(
                user_id=request.user_id,
                session_id=session_id,
                document_type=request.document_type.value,
                user_role=request.user_role.value,
                organization_id=request.organization_id
            )
            
            # Step 4: Get prompt configurations
            prompts = self.prompts_db.get_all_prompts_for_document(
                document_type=request.document_type.value,
                prompt_labels=request.prompt_labels,
                organization_id=request.organization_id
            )
            
            # Step 5: Analyze each section
            sections = []
            for label, prompt_config in prompts.items():
                section_result = await self._analyze_section(
                    document_text=document_text,
                    prompt_config=prompt_config,
                    request=request
                )
                sections.append(section_result)
            
            # Step 6: Generate overall summary
            summary = await self._generate_summary(sections)
            
            # Step 7: Save results
            processing_time = time.time() - start_time
            self.db.save_analysis_results(
                session_id=session_id,
                sections=[s.dict() for s in sections],
                summary=summary,
                processing_time=processing_time
            )
            
            logger.info(
                "analysis_completed",
                session_id=session_id,
                sections_count=len(sections),
                processing_time=processing_time
            )
            
            return AnalyzerResponse(
                session_id=session_id,
                user_id=request.user_id,
                document_type=request.document_type.value,
                sections=sections,
                summary=summary,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            logger.error("analysis_failed", error=str(e), session_id=session_id)
            raise
    
    async def _extract_text(self, request: AnalyzerRequest) -> str:
        """Extract text from request"""
        if request.text_input:
            return request.text_input
        elif request.file_data:
            # Assume filename is provided somehow, or detect from file_data
            file_obj = BytesIO(request.file_data)
            return self.pdf_service.extract_text(file_obj, "document.pdf")
        else:
            raise ValueError("No input provided")
    
    async def _store_file(self, request: AnalyzerRequest, session_id: str) -> str:
        """Store file in S3"""
        file_key = f"analyzer/{request.user_id}/{session_id}/document.pdf"
        file_obj = BytesIO(request.file_data)
        return self.s3_service.upload_file(file_obj, file_key)
    
    @traceable(name="analyze_section", tags=["analyzer", "section"])
    async def _analyze_section(
        self,
        document_text: str,
        prompt_config: Dict,
        request: AnalyzerRequest
    ) -> AnalyzerSectionResult:
        """Analyze a single section"""
        try:
            # Build prompt with document context
            base_prompt = prompt_config.get("base_prompt", "")
            system_prompt = prompt_config.get("system_prompt", "")
            
            # Fill in template variables
            filled_prompt = base_prompt.replace("{document_text}", document_text)
            filled_prompt = filled_prompt.replace("{document_type}", request.document_type.value)
            filled_prompt = filled_prompt.replace("{user_role}", request.user_role.value)
            
            # Fetch relevant examples from Pinecone if configured
            if prompt_config.get("use_corpus"):
                corpus_id = prompt_config.get("corpus_id", "")
                examples = self.pinecone_service.fetch_chunks_by_topic(
                    query=filled_prompt[:500],  # Use first 500 chars as query
                    topic=corpus_id,
                    num_examples=prompt_config.get("num_examples", 5)
                )
                
                # Add examples to prompt
                examples_text = "\n\n".join([
                    f"Example from {ex['sources']}:\n{ex['comment']}"
                    for ex in examples
                ])
                filled_prompt = f"{filled_prompt}\n\nRelevant Examples:\n{examples_text}"
            
            # Generate analysis
            response = self.llm_service.generate_completion(
                prompt=filled_prompt,
                system_prompt=system_prompt,
                temperature=prompt_config.get("temperature", 0.7),
                max_tokens=prompt_config.get("max_tokens", 4000)
            )
            
            return AnalyzerSectionResult(
                section_id=str(uuid.uuid4()),
                label=prompt_config.get("prompt_label"),
                title=f"Analysis: {prompt_config.get('prompt_label')}",
                content=response
            )
            
        except Exception as e:
            logger.error("section_analysis_failed", error=str(e))
            raise
    
    async def _generate_summary(self, sections: List[AnalyzerSectionResult]) -> str:
        """Generate overall summary from sections"""
        combined_text = "\n\n".join([
            f"{s.title}:\n{s.content[:500]}"  # First 500 chars of each
            for s in sections
        ])
        
        return self.llm_service.generate_summary(combined_text, style="concise")
    
    @traceable(name="answer_followup", tags=["analyzer", "followup"])
    async def answer_followup(self, request: AnalyzerFollowupRequest) -> str:
        """Answer follow-up question about analysis"""
        try:
            # Get session data
            session_data = self.db.get_session(request.session_id)
            
            # Build context from session
            context = f"Document Type: {session_data.get('document_type')}\n\n"
            
            if request.section and session_data.get('sections'):
                # Get specific section
                sections = session_data['sections']
                section_data = next(
                    (s for s in sections if s['label'] == request.section),
                    None
                )
                if section_data:
                    context += f"Section: {section_data['title']}\n{section_data['content']}\n\n"
            else:
                # Use summary
                context += f"Summary: {session_data.get('summary', '')}\n\n"
            
            # Answer question
            prompt = f"{context}\nQuestion: {request.query}\n\nProvide a clear, specific answer:"
            answer = self.llm_service.generate_completion(prompt, temperature=0.3)
            
            # Save followup
            self.db.save_followup(
                session_id=request.session_id,
                query=request.query,
                answer=answer,
                section=request.section
            )
            
            return answer
            
        except Exception as e:
            logger.error("followup_failed", error=str(e))
            raise

