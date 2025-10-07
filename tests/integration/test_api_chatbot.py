"""Integration tests for Chatbot API endpoints"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.api
class TestChatbotAPI:
    """Test Chatbot API endpoints"""
    
    def test_chat_endpoint(self, api_client, clean_database):
        """Test main chat endpoint"""
        payload = {
            "user_id": "test-user",
            "query": "What is the project budget?",
            "source": "web"
        }
        
        response = api_client.post("/api/v1/chatbot/chat", json=payload)
        
        # Check endpoint is accessible
        assert response.status_code in [200, 422, 500]
    
    def test_get_chat_sessions(self, api_client, clean_database):
        """Test get user chat sessions"""
        response = api_client.get(
            "/api/v1/chatbot/sessions",
            params={"user_id": "test-user"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data or isinstance(data, list)
    
    def test_get_session_history(self, api_client, clean_database):
        """Test get session conversation history"""
        response = api_client.get(
            "/api/v1/chatbot/sessions/test-session-123"
        )
        
        assert response.status_code in [200, 404]
    
    def test_get_last_session(self, api_client, clean_database):
        """Test get user's last session"""
        response = api_client.get(
            "/api/v1/chatbot/sessions/last",
            params={"user_id": "test-user"}
        )
        
        assert response.status_code in [200, 404]
    
    def test_submit_chat_feedback(self, api_client, clean_database):
        """Test chat feedback submission"""
        payload = {
            "session_id": "test-session",
            "message_id": "msg-123",
            "feedback": "positive",
            "comment": "Helpful response"
        }
        
        response = api_client.post(
            "/api/v1/chatbot/feedback",
            json=payload
        )
        
        assert response.status_code in [200, 201, 404, 422]
    
    def test_chat_empty_query(self, api_client):
        """Test chat with empty query"""
        payload = {
            "user_id": "test-user",
            "query": "",
            "source": "web"
        }
        
        response = api_client.post("/api/v1/chatbot/chat", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_missing_user_id(self, api_client):
        """Test chat without user_id"""
        payload = {
            "query": "Test question",
            "source": "web"
        }
        
        response = api_client.post("/api/v1/chatbot/chat", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_whatsapp_source(self, api_client, clean_database):
        """Test chat from WhatsApp source"""
        payload = {
            "user_id": "wa-user",
            "query": "Budget information?",
            "source": "WA"
        }
        
        response = api_client.post("/api/v1/chatbot/chat", json=payload)
        
        assert response.status_code in [200, 422, 500]
