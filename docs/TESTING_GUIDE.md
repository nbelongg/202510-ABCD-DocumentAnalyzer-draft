# Testing Guide

## Overview

This document describes the comprehensive testing strategy for the Document Analyzer project, including unit tests, integration tests, and end-to-end tests.

## Test Coverage Goals

- **Target**: 80%+ code coverage
- **Unit Tests**: 70%+ coverage
- **Integration Tests**: All API endpoints
- **E2E Tests**: Critical user workflows

## Setup

### Install Dependencies

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Or install individual packages
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Configure Test Database

```bash
# Create test database
mysql -u root -p -e "CREATE DATABASE test_document_analyzer;"

# Set environment variables
export MYSQL_DATABASE=test_document_analyzer
export ENVIRONMENT=testing
```

## Running Tests

### All Tests

```bash
# Run all tests with coverage
pytest -v --cov=. --cov-report=html --cov-report=term-missing

# Open coverage report
open htmlcov/index.html
```

### Unit Tests Only

```bash
# Run only unit tests
pytest tests/unit -v

# With markers
pytest -m unit -v
```

### Integration Tests Only

```bash
# Run only integration tests
pytest tests/integration -v

# With markers
pytest -m integration -v
```

### End-to-End Tests

```bash
# Run E2E tests (requires full system)
pytest tests/e2e -v -m e2e
```

### Specific Test Files

```bash
# Test specific module
pytest tests/unit/test_core_analyzer.py -v

# Test specific function
pytest tests/unit/test_core_analyzer.py::TestDocumentAnalyzer::test_analyze_section -v
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_core_analyzer.py
│   ├── test_core_chatbot.py
│   ├── test_core_evaluator.py
│   └── test_services_llm.py
├── integration/             # Integration tests
│   ├── test_api_analyzer.py
│   ├── test_api_chatbot.py
│   └── test_api_evaluator.py
└── e2e/                     # End-to-end tests
    └── test_complete_workflows.py
```

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from core.analyzer import DocumentAnalyzer

@pytest.mark.unit
class TestDocumentAnalyzer:
    
    @pytest.fixture
    def analyzer(self, mock_llm_service):
        \"\"\"Create analyzer with mocked dependencies\"\"\"
        with patch('core.analyzer.LLMService', return_value=mock_llm_service):
            return DocumentAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_section(self, analyzer):
        \"\"\"Test section analysis\"\"\"
        result = await analyzer.analyze_section(
            section_label="P1",
            document_text="Test document",
            prompt="Analyze this"
        )
        
        assert "content" in result
        assert result["section_label"] == "P1"
```

### Integration Test Example

```python
import pytest
from fastapi import status

@pytest.mark.integration
@pytest.mark.api
class TestAnalyzerAPI:
    
    def test_analyze_document(self, api_client, sample_document_text, clean_database):
        \"\"\"Test document analysis endpoint\"\"\"
        response = api_client.post(
            "/api/v1/analyzer/analyze",
            data={
                "user_id": "test-user",
                "text_input": sample_document_text
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
```

## Test Fixtures

### Available Fixtures (see `conftest.py`)

- `client`: FastAPI test client
- `api_client`: Authenticated API client
- `db_connection`: Database connection
- `db_cursor`: Database cursor
- `clean_database`: Clean database before test
- `mock_llm_service`: Mocked LLM service
- `mock_pinecone_service`: Mocked Pinecone service
- `mock_pdf_service`: Mocked PDF service
- `sample_document_text`: Sample document
- `sample_tor_text`: Sample ToR document

## Mocking External Services

### LLM Service

```python
def test_with_mocked_llm(mock_llm_service):
    mock_llm_service.generate_completion.return_value = "Mocked response"
    # Your test code
```

### Pinecone Service

```python
def test_with_mocked_pinecone(mock_pinecone_service):
    mock_pinecone_service.search_similar.return_value = [
        {"metadata": {"text": "Context", "source": "doc.pdf"}}
    ]
    # Your test code
```

## Continuous Integration

Tests run automatically on every push via GitHub Actions:

```yaml
# .github/workflows/ci.yml
- Unit tests on every push
- Integration tests with MySQL/Redis
- Coverage reporting to Codecov
```

## Test Markers

```python
@pytest.mark.unit         # Unit test
@pytest.mark.integration  # Integration test
@pytest.mark.e2e          # End-to-end test
@pytest.mark.slow         # Slow running test
@pytest.mark.smoke        # Smoke test
@pytest.mark.db           # Requires database
@pytest.mark.api          # API test
```

Run specific markers:
```bash
pytest -m "unit and not slow"
pytest -m "integration or e2e"
```

## Coverage Reports

### Generate HTML Report

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Generate XML Report (for CI)

```bash
pytest --cov=. --cov-report=xml
```

### View Terminal Report

```bash
pytest --cov=. --cov-report=term-missing
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Mock External Services**: Don't make real API calls
3. **Clean Database**: Use `clean_database` fixture
4. **Descriptive Names**: Test names should describe what they test
5. **Arrange-Act-Assert**: Follow AAA pattern
6. **Fast Tests**: Unit tests should be fast (<1s each)
7. **Coverage**: Aim for 80%+ but focus on critical paths

## Troubleshooting

### Tests Failing Due to Database

```bash
# Ensure test database exists
mysql -u root -p -e "CREATE DATABASE test_document_analyzer;"

# Check environment variables
echo $MYSQL_DATABASE
```

### Mock Not Working

```python
# Use patch correctly
with patch('module.where.used.ClassName') as mock:
    # Not where defined, where used!
```

### Async Test Issues

```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result
```

## Performance Testing

### Load Testing with Locust

```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8001
```

## Next Steps

1. Achieve 80%+ coverage
2. Add performance benchmarks
3. Add security testing
4. Add load testing scenarios
5. Implement mutation testing
