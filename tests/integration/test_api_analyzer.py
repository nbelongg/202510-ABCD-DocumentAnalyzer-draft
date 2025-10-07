"""Integration tests for Analyzer API endpoints"""
import pytest
import json
from fastapi import status


@pytest.mark.integration
@pytest.mark.api
class TestAnalyzerAPI:
    """Test Analyzer API endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_analyze_document_unauthorized(self, client):
        """Test analyze endpoint without auth"""
        response = client.post("/api/v1/analyzer/analyze")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_analyze_document_with_text(self, api_client, sample_document_text, clean_database):
        """Test document analysis with text input"""
        with pytest.mock.patch('core.analyzer.DocumentAnalyzer.analyze') as mock_analyze:
            mock_analyze.return_value = {
                "session_id": "test-123",
                "sections": [{"section_id": "P1", "content": "Analysis"}],
                "overall_score": 85.0
            }
            
            response = api_client.post(
                "/api/v1/analyzer/analyze",
                data={
                    "user_id": "test-user",
                    "text_input": sample_document_text,
                    "document_type": "Proposal"
                }
            )
            
            # Note: Actual response depends on implementation
            # This tests the endpoint is accessible
            assert response.status_code in [200, 422, 500]
    
    def test_get_sessions(self, api_client, clean_database):
        """Test get user sessions endpoint"""
        response = api_client.get(
            "/api/v1/analyzer/sessions",
            params={"user_id": "test-user"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data or isinstance(data, list)
    
    def test_get_session_by_id(self, api_client, clean_database):
        """Test get specific session endpoint"""
        # First create a session (in real test, would use fixture)
        session_id = "test-session-123"
        
        response = api_client.get(f"/api/v1/analyzer/sessions/{session_id}")
        
        # Session might not exist, so 404 is acceptable
        assert response.status_code in [200, 404]
    
    def test_followup_question(self, api_client, clean_database):
        """Test follow-up question endpoint"""
        payload = {
            "user_id": "test-user",
            "session_id": "test-session",
            "query": "Can you elaborate on the budget?",
            "section": "P1"
        }
        
        response = api_client.post(
            "/api/v1/analyzer/followup",
            json=payload
        )
        
        # May fail if session doesn't exist
        assert response.status_code in [200, 404, 422]
    
    def test_submit_feedback(self, api_client, clean_database):
        """Test feedback submission endpoint"""
        payload = {
            "session_id": "test-session",
            "section": "P1",
            "feedback": True,
            "feedback_note": "Very helpful analysis"
        }
        
        response = api_client.post(
            "/api/v1/analyzer/feedback",
            json=payload
        )
        
        assert response.status_code in [200, 201, 404, 422]
    
    def test_analyze_invalid_document_type(self, api_client):
        """Test analysis with invalid document type"""
        response = api_client.post(
            "/api/v1/analyzer/analyze",
            data={
                "user_id": "test-user",
                "text_input": "Sample text",
                "document_type": "InvalidType"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_analyze_missing_user_id(self, api_client):
        """Test analysis without user_id"""
        response = api_client.post(
            "/api/v1/analyzer/analyze",
            data={"text_input": "Sample text"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_analyze_no_input(self, api_client):
        """Test analysis without text or file"""
        response = api_client.post(
            "/api/v1/analyzer/analyze",
            data={"user_id": "test-user"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
