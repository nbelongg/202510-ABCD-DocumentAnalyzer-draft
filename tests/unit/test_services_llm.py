"""Unit tests for LLM Service"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.llm import LLMService
from services.exceptions import LLMServiceError


@pytest.mark.unit
class TestLLMService:
    """Test LLM Service"""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance"""
        with patch('services.llm.openai.Client'), \
             patch('services.llm.Anthropic'):
            return LLMService()
    
    def test_generate_completion_success(self, llm_service):
        """Test successful completion generation"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated response"))]
        mock_response.usage = Mock(total_tokens=100)
        
        llm_service.openai_client.chat.completions.create = Mock(return_value=mock_response)
        
        result = llm_service.generate_completion(
            prompt="Test prompt",
            system_prompt="System instruction"
        )
        
        assert result == "Generated response"
        llm_service.openai_client.chat.completions.create.assert_called_once()
    
    def test_generate_completion_with_parameters(self, llm_service):
        """Test completion with custom parameters"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(total_tokens=50)
        
        llm_service.openai_client.chat.completions.create = Mock(return_value=mock_response)
        
        result = llm_service.generate_completion(
            prompt="Test",
            temperature=0.5,
            max_tokens=500,
            model="gpt-4"
        )
        
        assert result == "Response"
        call_kwargs = llm_service.openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["model"] == "gpt-4"
    
    def test_generate_completion_error_handling(self, llm_service):
        """Test error handling in completion generation"""
        llm_service.openai_client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(LLMServiceError, match="OpenAI completion failed"):
            llm_service.generate_completion(prompt="Test")
    
    @pytest.mark.skipif(True, reason="Requires actual API key")
    def test_real_api_call(self):
        """Test real API call (skip in CI)"""
        # This would test actual API integration
        pass
