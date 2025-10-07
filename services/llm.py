"""LLM Service for OpenAI and Claude interactions"""
from typing import Optional, Dict, List
import openai
from anthropic import Anthropic
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable
from config.settings import settings
from services.logger import get_logger
from services.exceptions import LLMServiceError

logger = get_logger(__name__)


class LLMService:
    """Service for LLM interactions with OpenAI and Claude"""
    
    def __init__(self):
        """Initialize LLM clients"""
        self.openai_client = openai.Client(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORGANIZATION
        )
        
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )
        else:
            self.anthropic_client = None
    
    @traceable(name="generate_completion", tags=["llm", "openai"])
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion using OpenAI
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            model: Model to use (defaults to settings)
            temperature: Temperature (defaults to settings)
            max_tokens: Max tokens (defaults to settings)
            
        Returns:
            Generated text response
        """
        try:
            model = model or settings.OPENAI_MODEL
            temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
            max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            logger.info(
                "generating_openai_completion",
                model=model,
                temperature=temperature,
                prompt_length=len(prompt)
            )
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            
            logger.info(
                "openai_completion_success",
                model=model,
                tokens_used=response.usage.total_tokens
            )
            
            return result
            
        except Exception as e:
            logger.error("openai_completion_failed", error=str(e))
            raise LLMServiceError(f"OpenAI completion failed: {str(e)}")
    
    @traceable(name="generate_with_langchain", tags=["llm", "langchain"])
    def generate_with_langchain(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_claude: bool = False,
    ) -> str:
        """
        Generate completion using LangChain
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            use_claude: Use Claude instead of OpenAI
            
        Returns:
            Generated text response
        """
        try:
            if use_claude and self.anthropic_client:
                llm = ChatAnthropic(
                    model=settings.ANTHROPIC_MODEL,
                    anthropic_api_key=settings.ANTHROPIC_API_KEY
                )
            else:
                llm = ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    organization=settings.OPENAI_ORGANIZATION,
                    temperature=settings.OPENAI_TEMPERATURE
                )
            
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("user", "{input}"))
            
            prompt_template = ChatPromptTemplate.from_messages(messages)
            chain = prompt_template | llm | StrOutputParser()
            
            result = chain.invoke({"input": prompt})
            
            return result
            
        except Exception as e:
            logger.error("langchain_completion_failed", error=str(e))
            raise LLMServiceError(f"LangChain completion failed: {str(e)}")
    
    @traceable(name="refine_query", tags=["llm", "query_refinement"])
    def refine_query(self, conversation_history: str, query: str) -> Dict[str, any]:
        """
        Refine user query based on conversation history
        
        Args:
            conversation_history: Previous conversation context
            query: Current user query
            
        Returns:
            Dict with refined_query and requires_kb (knowledge base lookup)
        """
        try:
            system_prompt = """Given the conversation log and query, formulate a refined question.
            Return a JSON with: "refined_query" and "requires_knowledge_base" (boolean).
            Set requires_knowledge_base to true if the query needs factual information."""
            
            user_prompt = f"""Conversation Log:\n{conversation_history}\n\nQuery: {query}"""
            
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                "refined_query": result.get("refined_query", query),
                "requires_kb": result.get("requires_knowledge_base", True)
            }
            
        except Exception as e:
            logger.error("query_refinement_failed", error=str(e))
            # Return original query on failure
            return {"refined_query": query, "requires_kb": True}
    
    @traceable(name="generate_summary", tags=["llm", "summarization"])
    def generate_summary(
        self,
        text: str,
        max_length: int = 500,
        style: str = "concise"
    ) -> str:
        """
        Generate a summary of text
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            style: Summary style (concise, detailed, bullet)
            
        Returns:
            Summary text
        """
        try:
            style_prompts = {
                "concise": "Provide a concise summary in 2-3 sentences.",
                "detailed": "Provide a detailed summary covering main points.",
                "bullet": "Provide a bullet-point summary of key points."
            }
            
            system_prompt = f"""Summarize the following text. {style_prompts.get(style, style_prompts['concise'])}
            Keep it under {max_length} characters."""
            
            return self.generate_completion(
                prompt=text,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=min(max_length * 2, 2000)
            )
            
        except Exception as e:
            logger.error("summarization_failed", error=str(e))
            raise LLMServiceError(f"Summarization failed: {str(e)}")

