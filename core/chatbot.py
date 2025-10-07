"""Core chatbot engine with query refinement and context retrieval"""
from typing import Tuple, Dict, List, Optional
import uuid
from services.llm import LLMService
from services.pinecone_service import PineconeService
from services.logger import get_logger
from db.chatbot_db import ChatbotDB
from schemas.chatbot import (
    ChatRequest, ChatResponse, ContextInfo, SourceInfo, LLMModel
)
from utils.pdf_mappings import get_pdf_mappings, get_unique_sources
from utils.text_processing import break_into_paragraphs

logger = get_logger(__name__)


QUERY_REFINEMENT_PROMPT = """You are a query classification and refinement assistant.

Given a conversation history and the user's current question, determine:
1. Whether the question requires retrieval from a knowledge base (True/False)
2. A refined/expanded version of the question for better search results

Consider these guidelines:
- General greetings, thank you messages, or simple acknowledgments do NOT need retrieval
- Questions about specific topics, asking for information, or requesting explanations DO need retrieval
- If the question references "this", "that", or "it", use conversation context to make the refined query standalone
- Make the refined query clear and specific

Conversation History:
{conversation_history}

Current Question: {question}

Respond in exactly this format:
REQUIRES_RETRIEVAL: [True/False]
REFINED_QUERY: [the refined query]
"""


RESPONSE_GENERATION_PROMPT = """You are a helpful AI assistant specializing in impact evaluation, development, and social programs.

Your task is to answer the user's question based on the provided context from the knowledge base.

IMPORTANT RULES:
1. If the context contains relevant information, use it to answer the question
2. If the context is not relevant or insufficient, politely say you don't have that information in your knowledge base
3. Always cite your sources when using information from the context
4. Be concise but thorough
5. Use clear, professional language

Context from Knowledge Base:
{context}

Conversation History:
{conversation_history}

User Question: {question}

Please provide a helpful answer. If you use information from the context, mention which sources you're referencing.
"""


class ChatbotEngine:
    """Core chatbot engine"""
    
    def __init__(self):
        """Initialize chatbot engine"""
        self.llm_service = LLMService()
        self.pinecone = PineconeService()
        self.db = ChatbotDB()
        self.pdf_mappings = get_pdf_mappings()
        
        logger.info("chatbot_engine_initialized")
    
    async def query_refiner(self, conversation: str, query: str) -> Tuple[bool, str]:
        """
        Determine if retrieval is needed and refine the query
        
        Args:
            conversation: Conversation history
            query: User's question
            
        Returns:
            Tuple of (requires_retrieval, refined_query)
        """
        try:
            # Format prompt
            prompt = QUERY_REFINEMENT_PROMPT.format(
                conversation_history=conversation if conversation else "No previous conversation",
                question=query
            )
            
            # Call LLM
            response = self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse response
            requires_retrieval = False
            refined_query = query
            
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith('REQUIRES_RETRIEVAL:'):
                    value = line.split(':', 1)[1].strip().lower()
                    requires_retrieval = value == 'true'
                elif line.startswith('REFINED_QUERY:'):
                    refined_query = line.split(':', 1)[1].strip()
            
            logger.info(
                "query_refined",
                requires_retrieval=requires_retrieval,
                original_query=query[:50],
                refined_query=refined_query[:50]
            )
            
            return requires_retrieval, refined_query
            
        except Exception as e:
            logger.error("query_refinement_failed", error=str(e))
            # Default to requiring retrieval and using original query
            return True, query
    
    async def extract_context(self, query: str, top_k: int = 4, multiplier: int = 2) -> Dict:
        """
        Extract context from Pinecone knowledge base
        
        Args:
            query: Search query
            top_k: Number of unique results to return
            multiplier: Multiplier for initial retrieval to ensure uniqueness
            
        Returns:
            Dictionary with context info and sources
        """
        try:
            # Query Pinecone with multiplier for deduplication
            results = self.pinecone.query(query, top_k=top_k * multiplier)
            
            # Extract unique chunks
            seen_pdfs = set()
            unique_contexts = []
            all_context_parts = []
            
            for result in results:
                metadata = result.get('metadata', {})
                pdf_name = metadata.get('pdf_name', metadata.get('source', 'Unknown'))
                text = metadata.get('text', result.get('text', ''))
                score = result.get('score', 0.0)
                
                # Deduplicate by PDF name
                if pdf_name not in seen_pdfs and len(unique_contexts) < top_k:
                    seen_pdfs.add(pdf_name)
                    
                    context_info = {
                        'pdf_name': pdf_name,
                        'pdf_context': text,
                        'score': score
                    }
                    unique_contexts.append(context_info)
                    all_context_parts.append(text)
            
            # Get PDF mappings for sources
            sources_info = []
            for context in unique_contexts:
                pdf_name = context['pdf_name']
                pdf_info = self.pdf_mappings.get(pdf_name)
                sources_info.append(pdf_info)
            
            # Remove duplicate sources
            sources_info = get_unique_sources(sources_info)
            
            # Combine all context
            all_context = '\n\n---\n\n'.join(all_context_parts)
            
            result = {
                'context_info': unique_contexts,
                'sources_info': sources_info,
                'all_context': all_context
            }
            
            logger.info(
                "context_extracted",
                num_contexts=len(unique_contexts),
                num_sources=len(sources_info)
            )
            
            return result
            
        except Exception as e:
            logger.error("context_extraction_failed", error=str(e))
            return {
                'context_info': [],
                'sources_info': [],
                'all_context': ''
            }
    
    async def generate_response(
        self,
        question: str,
        conversation: str,
        context: str,
        model: str = "gpt-4o",
        source: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Generate response using LLM
        
        Args:
            question: User's question
            conversation: Conversation history
            context: Retrieved context
            model: LLM model to use
            source: Source platform (e.g., 'WA')
            
        Returns:
            Tuple of (response, within_knowledge_base)
        """
        try:
            # Format prompt
            prompt = RESPONSE_GENERATION_PROMPT.format(
                context=context if context else "No relevant context found",
                conversation_history=conversation if conversation else "No previous conversation",
                question=question
            )
            
            # Call LLM
            response = self.llm_service.generate_completion(
                prompt=prompt,
                model=model,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Determine if answer is from knowledge base
            within_knowledge_base = bool(context)
            
            # Check if response indicates lack of information
            response_lower = response.lower()
            if any(phrase in response_lower for phrase in [
                "don't have that information",
                "not in my knowledge base",
                "cannot find",
                "no relevant information"
            ]):
                within_knowledge_base = False
            
            # Format for WhatsApp if needed
            if source == "WA":
                response = break_into_paragraphs(response, max_length=1000)
            
            logger.info(
                "response_generated",
                within_kb=within_knowledge_base,
                response_length=len(response)
            )
            
            return response, within_knowledge_base
            
        except Exception as e:
            logger.error("response_generation_failed", error=str(e))
            return "I apologize, but I encountered an error generating a response. Please try again.", False
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Main chat method
        
        Args:
            request: Chat request
            
        Returns:
            Chat response
        """
        try:
            # Generate session ID if not provided
            session_id = request.session_id or str(uuid.uuid4())
            response_id = str(uuid.uuid4())
            
            logger.info(
                "chat_request_received",
                user_id=request.user_id,
                session_id=session_id,
                question=request.question[:50]
            )
            
            # Check if session exists, if not create it
            try:
                self.db.create_session(
                    user_id=request.user_id,
                    session_id=session_id,
                    user_name=request.user_name,
                    user_email=request.user_email,
                    source=request.source
                )
            except:
                # Session already exists, that's fine
                pass
            
            # Get conversation history
            conversation_string = ""
            if session_id:
                conversation_string = self.db.get_user_conversations(
                    request.user_id,
                    session_id
                )
            
            # Save user message
            self.db.save_message(session_id, "user", request.question)
            
            # Step 1: Query refinement
            requires_retrieval, refined_query = await self.query_refiner(
                conversation_string,
                request.question
            )
            
            # Step 2: Extract context if needed
            context_info = []
            sources_info = []
            context = ""
            
            if requires_retrieval:
                context_data = await self.extract_context(refined_query, top_k=4)
                context_info = context_data['context_info']
                sources_info = context_data['sources_info']
                context = context_data['all_context']
            
            # Step 3: Generate response
            response_text, within_knowledge_base = await self.generate_response(
                request.question,
                conversation_string,
                context,
                model=request.model.value,
                source=request.source
            )
            
            # If not within knowledge base, clear context
            if not within_knowledge_base:
                context_info = []
                sources_info = []
            
            # Save assistant message with context
            context_data_dict = {
                'contextInfo': [c for c in context_info],
                'sources': sources_info
            }
            
            self.db.save_message(
                session_id=session_id,
                role="assistant",
                content=response_text,
                response_id=response_id,
                context_data=context_data_dict,
                sources=sources_info
            )
            
            # Build response
            response = ChatResponse(
                user_id=request.user_id,
                session_id=session_id,
                response=response_text,
                response_id=response_id,
                contextInfo=[ContextInfo(**c) for c in context_info],
                sources=[SourceInfo(**s) for s in sources_info],
                within_knowledge_base=within_knowledge_base
            )
            
            logger.info(
                "chat_response_sent",
                session_id=session_id,
                response_id=response_id,
                within_kb=within_knowledge_base
            )
            
            return response
            
        except Exception as e:
            logger.error("chat_failed", error=str(e), exc_info=True)
            raise

