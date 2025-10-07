"""
Pytest fixtures and configuration for test suite
"""
import pytest
import os
import sys
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch
from datetime import datetime
import psycopg2
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app
from config.settings import Settings
from db.connection import initialize_pool
from services.llm import LLMService
from services.pinecone_service import PineconeService
from services.pdf_service import PDFService
from services.s3_service import S3Service


# ==================== Test Settings ====================

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings with overrides"""
    os.environ.update({
        "ENVIRONMENT": "testing",
        "DEBUG": "true",
        "POSTGRES_DATABASE": "test_document_analyzer",
        "API_KEY": "test-api-key",
        "API_SECRET": "test-api-secret",
    })
    return Settings()


# ==================== Database Fixtures ====================

@pytest.fixture(scope="session")
def db_connection():
    """Create test database connection"""
    try:
        initialize_pool()
        yield
    finally:
        # Cleanup handled by connection pool
        pass


@pytest.fixture
def db_cursor(db_connection):
    """Provide database cursor for tests"""
    from db.connection import get_db_cursor
    with get_db_cursor() as cursor:
        yield cursor


@pytest.fixture
def clean_database(db_cursor):
    """Clean database before each test"""
    # Clean all test tables
    tables = [
        "analyzer_sessions",
        "analyzer_followups",
        "analyzer_feedback",
        "chatbot_sessions",
        "chatbot_messages",
        "chatbot_feedback",
        "evaluator_sessions",
        "evaluator_followups",
        "evaluator_feedback",
        "prompts",
        "organizations",
        "guidelines",
        "users",
        "api_keys"
    ]
    
    for table in tables:
        try:
            db_cursor.execute(f"DELETE FROM {table}")
        except psycopg2.Error:
            # Table might not exist in test DB
            pass
    
    yield
    
    # Cleanup after test
    for table in tables:
        try:
            db_cursor.execute(f"DELETE FROM {table}")
        except psycopg2.Error:
            pass


# ==================== API Client Fixtures ====================

@pytest.fixture
def client() -> TestClient:
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Authentication headers for API requests"""
    return {
        "api-key": "test-api-key",
        "api-secret": "test-api-secret"
    }


@pytest.fixture
def api_client(client, auth_headers):
    """Authenticated API client"""
    class AuthenticatedClient:
        def __init__(self, client: TestClient, headers: Dict[str, str]):
            self._client = client
            self._headers = headers
        
        def get(self, url: str, **kwargs):
            return self._client.get(url, headers=self._headers, **kwargs)
        
        def post(self, url: str, **kwargs):
            return self._client.post(url, headers=self._headers, **kwargs)
        
        def put(self, url: str, **kwargs):
            return self._client.put(url, headers=self._headers, **kwargs)
        
        def delete(self, url: str, **kwargs):
            return self._client.delete(url, headers=self._headers, **kwargs)
    
    return AuthenticatedClient(client, auth_headers)


# ==================== Mock Service Fixtures ====================

@pytest.fixture
def mock_llm_service():
    """Mock LLM service"""
    with patch('services.llm.LLMService') as mock:
        mock_instance = MagicMock()
        mock_instance.generate_completion.return_value = "Mock LLM response"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_pinecone_service():
    """Mock Pinecone service"""
    with patch('services.pinecone_service.PineconeService') as mock:
        mock_instance = MagicMock()
        mock_instance.search_similar.return_value = [
            {
                "id": "doc1",
                "score": 0.95,
                "metadata": {"text": "Mock context", "source": "test.pdf"}
            }
        ]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_pdf_service():
    """Mock PDF service"""
    with patch('services.pdf_service.PDFService') as mock:
        mock_instance = MagicMock()
        mock_instance.extract_text_from_pdf.return_value = "Mock PDF text content"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_s3_service():
    """Mock S3 service"""
    with patch('services.s3_service.S3Service') as mock:
        mock_instance = MagicMock()
        mock_instance.upload_file.return_value = "https://s3.example.com/test-file.pdf"
        mock_instance.download_file.return_value = b"Mock file content"
        mock.return_value = mock_instance
        yield mock_instance


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Sample user data"""
    return {
        "user_id": "test-user-123",
        "user_name": "Test User",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_document_text() -> str:
    """Sample document text"""
    return """
    Project Proposal: Educational Technology Initiative
    
    Executive Summary:
    This proposal outlines a comprehensive educational technology initiative
    aimed at improving learning outcomes through innovative digital tools.
    
    Objectives:
    1. Develop interactive learning platform
    2. Implement AI-powered tutoring
    3. Create assessment and analytics dashboard
    
    Budget: $500,000
    Timeline: 12 months
    """


@pytest.fixture
def sample_tor_text() -> str:
    """Sample Terms of Reference"""
    return """
    Terms of Reference: Educational Technology Project
    
    Scope:
    - Development of digital learning platform
    - Integration with existing systems
    - Training for educators
    - Performance monitoring
    
    Requirements:
    - Scalable architecture
    - User-friendly interface
    - Data security compliance
    - Regular reporting
    """


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Sample PDF file bytes"""
    # Minimal valid PDF
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"


@pytest.fixture
def sample_session_data() -> Dict[str, Any]:
    """Sample session data"""
    return {
        "session_id": "test-session-123",
        "user_id": "test-user-123",
        "document_type": "Proposal",
        "created_at": datetime.now()
    }


@pytest.fixture
def sample_analysis_result() -> Dict[str, Any]:
    """Sample analysis result"""
    return {
        "session_id": "test-session-123",
        "sections": [
            {
                "section_id": "P1",
                "title": "Executive Summary",
                "content": "Analysis of executive summary...",
                "score": 85.0
            },
            {
                "section_id": "P2",
                "title": "Technical Approach",
                "content": "Analysis of technical approach...",
                "score": 90.0
            }
        ],
        "overall_score": 87.5,
        "processing_time": 5.2
    }


@pytest.fixture
def sample_chat_message() -> Dict[str, Any]:
    """Sample chat message"""
    return {
        "user_id": "test-user-123",
        "session_id": "chat-session-123",
        "query": "What is the project budget?",
        "context": ["The budget is $500,000"],
        "source": "web"
    }


@pytest.fixture
def sample_evaluation_data() -> Dict[str, Any]:
    """Sample evaluation data"""
    return {
        "user_id": "test-user-123",
        "proposal_text": "Our proposal aims to achieve...",
        "tor_text": "The project requires...",
        "organization_id": "org-123",
        "internal_analysis": {
            "score": 85.0,
            "strengths": ["Clear objectives", "Strong team"],
            "gaps": ["Missing timeline details"]
        },
        "external_analysis": {
            "score": 80.0,
            "strengths": ["Aligns with ToR"],
            "gaps": ["Budget not detailed"]
        },
        "delta_analysis": {
            "score": 82.5,
            "strengths": ["Good overall alignment"],
            "gaps": ["Some minor gaps identified"]
        }
    }


# ==================== Utility Fixtures ====================

@pytest.fixture
def freeze_time():
    """Freeze time for testing"""
    frozen_time = datetime(2024, 1, 1, 12, 0, 0)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = frozen_time
        mock_datetime.utcnow.return_value = frozen_time
        yield frozen_time


@pytest.fixture
def capture_logs():
    """Capture log output"""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger()
    logger.addHandler(handler)
    
    yield log_capture
    
    logger.removeHandler(handler)


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test location
    for item in items:
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
