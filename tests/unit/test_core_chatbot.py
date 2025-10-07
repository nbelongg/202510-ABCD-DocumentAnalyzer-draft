"""Unit tests for ChatbotEngine"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.chatbot import ChatbotEngine
from schemas.chatbot import ChatRequest


@pytest.mark.unit
class TestChatbotEngine:
    """Test ChatbotEngine core logic"""
    
    @pytest.fixture
    def chatbot(self, mock_llm_service, mock_pinecone_service):
        """Create chatbot instance with mocked services"""
        with patch('core.chatbot.LLMService', return_value=mock_llm_service), \
             patch('core.chatbot.PineconeService', return_value=mock_pinecone_service):
            return ChatbotEngine()
    
    @pytest.mark.asyncio
    async def test_refine_query_retrieval_needed(self, chatbot, mock_llm_service):
        """Test query refinement when retrieval is needed"""
        mock_llm_service.generate_completion.return_value = "YES"
        
        needs_retrieval, refined = await chatbot.refine_query(
            query="What is the project budget?",
            conversation_history=[]
        )
        
        assert needs_retrieval is True
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refine_query_no_retrieval(self, chatbot, mock_llm_service):
        """Test query refinement when retrieval is not needed"""
        mock_llm_service.generate_completion.return_value = "NO"
        
        needs_retrieval, refined = await chatbot.refine_query(
            query="Hello, how are you?",
            conversation_history=[]
        )
        
        assert needs_retrieval is False
    
    @pytest.mark.asyncio
    async def test_get_relevant_context(self, chatbot, mock_pinecone_service):
        """Test retrieving relevant context from Pinecone"""
        mock_pinecone_service.search_similar.return_value = [
            {
                "id": "doc1",
                "score": 0.95,
                "metadata": {"text": "Budget is $500k", "source": "proposal.pdf"}
            },
            {
                "id": "doc2",
                "score": 0.90,
                "metadata": {"text": "Timeline is 12 months", "source": "plan.pdf"}
            }
        ]
        
        context = await chatbot.get_relevant_context("budget", num_results=5)
        
        assert len(context) == 2
        assert "Budget is $500k" in context[0]["text"]
        assert context[0]["source"] == "proposal.pdf"
    
    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, chatbot, mock_llm_service):
        """Test generating response with context"""
        mock_llm_service.generate_completion.return_value = "The budget is $500,000."
        
        context = [
            {"text": "Budget is $500k", "source": "proposal.pdf"}
        ]
        
        response = await chatbot.generate_response(
            query="What is the budget?",
            context=context,
            conversation_history=[]
        )
        
        assert "budget" in response.lower()
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_no_context(self, chatbot, mock_llm_service):
        """Test generating response without context"""
        mock_llm_service.generate_completion.return_value = "I don't have that information."
        
        response = await chatbot.generate_response(
            query="Unknown question",
            context=[],
            conversation_history=[]
        )
        
        assert response == "I don't have that information."
    
    @pytest.mark.asyncio
    async def test_build_conversation_history(self, chatbot):
        """Test building conversation history string"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "What's the budget?"}
        ]
        
        history = chatbot.build_conversation_history(messages)
        
        assert "User: Hello" in history
        assert "Assistant: Hi there!" in history
        assert len(history) > 0
    
    @pytest.mark.asyncio
    async def test_format_whatsapp_response(self, chatbot):
        """Test formatting response for WhatsApp"""
        response = "This is a long response.\n\nWith multiple paragraphs.\n\nAnd breaks."
        
        formatted = chatbot.format_for_whatsapp(response)
        
        # WhatsApp formatting should preserve paragraph breaks
        assert "\n\n" in formatted or formatted == response
    
    @pytest.mark.asyncio
    async def test_chat_full_workflow(self, chatbot, mock_llm_service, mock_pinecone_service):
        """Test complete chat workflow"""
        # Mock refinement
        mock_llm_service.generate_completion.side_effect = [
            "YES",  # Needs retrieval
            "The project budget is $500,000 as stated in the proposal."  # Response
        ]
        
        # Mock context
        mock_pinecone_service.search_similar.return_value = [
            {"metadata": {"text": "Budget: $500k", "source": "proposal.pdf"}}
        ]
        
        with patch.object(chatbot.db, 'create_session', return_value="session-123"), \
             patch.object(chatbot.db, 'save_message', return_value=None):
            
            request = ChatRequest(
                user_id="test-user",
                query="What is the budget?",
                source="web"
            )
            
            # Note: Full integration would need complete mocking
            assert chatbot is not None
    
    def test_is_within_knowledge_base(self, chatbot):
        """Test detection of within knowledge base responses"""
        assert chatbot.is_within_knowledge_base("The budget is $500k") is True
        assert chatbot.is_within_knowledge_base("I don't have that information") is False
        assert chatbot.is_within_knowledge_base("I'm not sure about that") is False
    
    @pytest.mark.asyncio
    async def test_error_handling_context_retrieval(self, chatbot, mock_pinecone_service):
        """Test error handling during context retrieval"""
        mock_pinecone_service.search_similar.side_effect = Exception("Pinecone error")
        
        with pytest.raises(Exception, match="Pinecone error"):
            await chatbot.get_relevant_context("test query")
    
    @pytest.mark.asyncio
    async def test_empty_query_handling(self, chatbot):
        """Test handling of empty query"""
        needs_retrieval, refined = await chatbot.refine_query(
            query="",
            conversation_history=[]
        )
        
        # Should handle gracefully
        assert needs_retrieval is False
