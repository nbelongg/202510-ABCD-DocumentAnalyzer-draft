# ABCD Document Analyzer - Improved Version

A completely refactored document analysis platform with clean architecture, modern best practices, and production-ready code.

## 🎯 What's New

This is a **complete rewrite** of the original Document Analyzer addressing all architectural and code quality issues:

- ✅ **No hardcoded credentials** - All secrets in environment variables
- ✅ **Clean layered architecture** - Proper separation of concerns
- ✅ **File sizes under 400 lines** - Well-organized, maintainable code
- ✅ **Connection pooling** - Efficient database operations
- ✅ **Structured logging** - Comprehensive observability
- ✅ **Type safety** - Full Pydantic validation
- ✅ **Modern async patterns** - Proper async/await usage
- ✅ **Dependency injection** - Testable, modular code

## 📁 Project Structure

```
202510-ABCD-Document-Analyzer-Improved/
├── api/                    # FastAPI application & routes
│   ├── main.py            # Main app with middleware (167 lines)
│   ├── dependencies.py    # Auth & DI (23 lines)
│   └── routes/            # Clean route modules
│       ├── analyzer.py    # Analyzer endpoints (124 lines)
│       ├── evaluator.py   # Evaluator endpoints (stub)
│       ├── chatbot.py     # Chatbot endpoints (stub)
│       ├── admin.py       # Admin endpoints (stub)
│       ├── admin_guidelines.py  # Guideline access control
│       ├── admin_csv_sync.py    # CSV sync for guidelines
│       └── admin_prompts_bulk.py # Bulk prompt updates (legacy compatible)
├── core/                   # Business logic layer
│   ├── analyzer.py        # Document analysis engine (254 lines)
│   ├── evaluator.py       # Proposal evaluator (to implement)
│   └── chatbot.py         # Chatbot engine (to implement)
├── services/               # External integrations
│   ├── llm.py             # OpenAI & Claude service (234 lines)
│   ├── pinecone_service.py# Vector search (143 lines)
│   ├── pdf_service.py     # Document extraction (147 lines)
│   ├── s3_service.py      # File storage (122 lines)
│   ├── logger.py          # Structured logging (47 lines)
│   └── exceptions.py      # Custom exceptions (72 lines)
├── db/                     # Database layer
│   ├── connection.py      # Connection pooling (102 lines)
│   ├── analyzer_db.py     # Analyzer DB ops (206 lines)
│   ├── evaluator_db.py    # Evaluator DB ops (71 lines)
│   ├── chatbot_db.py      # Chatbot DB ops (93 lines)
│   └── prompts_db.py      # Prompt management (139 lines)
├── schemas/                # Pydantic models
│   ├── common.py          # Common schemas (67 lines)
│   ├── analyzer.py        # Analyzer schemas (144 lines)
│   ├── evaluator.py       # Evaluator schemas (79 lines)
│   └── chatbot.py         # Chatbot schemas (68 lines)
├── config/                 # Configuration
│   └── settings.py        # Environment-based config (107 lines)
├── utils/                  # Utilities
│   └── organization_utils.py # Organization & guideline access utilities
├── scripts/                # Admin scripts
│   ├── update_analyzer_prompts.py       # CLI prompt sync script
│   ├── update_analyzer_prompts_colab.py # Google Colab version
│   └── sync_guidelines_from_csv.py      # CSV guideline sync
├── docs/                   # Documentation
│   ├── PROMPTS_SYNC_WORKFLOW.md    # Prompt sync guide
│   ├── GUIDELINE_ACCESS_CONTROL.md # Guideline access guide
│   └── csv_templates/              # CSV templates
├── migrations/             # Database migrations
├── tests/                  # Test suite (to implement)
├── .env.example           # Example environment file
├── .gitignore             # Git ignore (including .env!)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd "202510-ABCD-Document-Analyzer-Improved"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your actual credentials
# NEVER commit .env to git!
nano .env
```

### 3. Configure Required Services

You need to set up:
- **MySQL Database**: For storing sessions and results
- **OpenAI API**: For LLM completions
- **Pinecone**: For vector search
- **AWS S3**: For file storage
- **LangSmith** (optional): For observability

### 4. Run the Application

```bash
# Development mode with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Production mode
uvicorn api.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### 5. Test the API

```bash
# Health check
curl http://localhost:8001/health

# API documentation
open http://localhost:8001/docs
```

## 📊 Database Setup

### Required Tables

Run these SQL scripts to create the necessary tables:

```sql
-- Analyzer sessions
CREATE TABLE analyzer_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    document_type VARCHAR(100),
    user_role VARCHAR(100),
    organization_id VARCHAR(255),
    sections JSON,
    summary TEXT,
    processing_time FLOAT,
    created_at DATETIME,
    completed_at DATETIME,
    INDEX idx_user_sessions (user_id, created_at)
);

-- Analyzer followups
CREATE TABLE analyzer_followups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    answer TEXT,
    section VARCHAR(100),
    created_at DATETIME,
    INDEX idx_session (session_id)
);

-- Analyzer feedback
CREATE TABLE analyzer_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    section VARCHAR(100),
    feedback BOOLEAN,
    feedback_note TEXT,
    created_at DATETIME,
    INDEX idx_session (session_id)
);

-- Analyzer prompts
CREATE TABLE analyzer_prompts (
    prompt_id INT AUTO_INCREMENT PRIMARY KEY,
    prompt_label VARCHAR(50) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    organization_id VARCHAR(255),
    base_prompt TEXT NOT NULL,
    customization_prompt TEXT,
    system_prompt TEXT,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 4000,
    use_corpus BOOLEAN DEFAULT TRUE,
    corpus_id VARCHAR(100),
    num_examples INT DEFAULT 5,
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE KEY unique_prompt (prompt_label, document_type, organization_id)
);

-- Similar tables for evaluator and chatbot...
```

## 🔑 API Usage

### Authentication

All API endpoints require authentication headers:

```bash
curl -X POST http://localhost:8001/api/v1/analyzer/analyze \
  -H "api-key: your_api_key" \
  -H "api-secret: your_api_secret" \
  -F "user_id=user123" \
  -F "text_input=Your document text here..."
```

### Main Endpoints

#### Analyze Document
```bash
POST /api/v1/analyzer/analyze
- Headers: api-key, api-secret
- Form Data:
  - user_id: string (required)
  - document_type: enum (optional)
  - text_input: string (or pdf_file)
  - prompt_labels: array[string]
```

#### Get Sessions
```bash
GET /api/v1/analyzer/sessions?user_id=user123
- Headers: api-key, api-secret
- Returns: List of analysis sessions
```

#### Follow-up Question
```bash
POST /api/v1/analyzer/followup
- Headers: api-key, api-secret
- Body: {user_id, session_id, query, section}
```

## 👨‍💼 Admin Operations

### Prompts Management

The system includes backwards-compatible tools for managing analyzer and evaluator prompts via CSV files.

**Quick Start**:
```bash
# Update prompts from CSV
python scripts/update_analyzer_prompts.py --csv prompts.csv --all

# Update specific prompt types
python scripts/update_analyzer_prompts.py --csv prompts.csv --p1-p5 --evaluators
```

**Google Colab Version**:
- Use `scripts/update_analyzer_prompts_colab.py` for Colab execution
- Supports Google Sheets integration
- No command-line arguments needed (config-based)

**Documentation**: See `docs/PROMPTS_SYNC_WORKFLOW.md` for complete guide

### Guidelines Access Control

Organization-specific guideline access with three-tier visibility:
1. **Private**: Organization's own guidelines
2. **Shared Public**: Public guidelines mapped to specific organizations
3. **Universal Public**: Available to all organizations

**Quick Start**:
```bash
# Grant access to public guideline
curl -X POST http://localhost:8001/api/v1/admin/guidelines/access/grant \
  -H "api-key: your_key" -H "api-secret: your_secret" \
  -H "Content-Type: application/json" \
  -d '{"guideline_id": "guide_123", "organization_ids": ["org_abc", "org_xyz"]}'

# Sync from CSV
python scripts/sync_guidelines_from_csv.py --preview organizations.csv
python scripts/sync_guidelines_from_csv.py --apply organizations.csv
```

**Documentation**: See `docs/GUIDELINE_ACCESS_CONTROL.md` for complete guide

## 🏗️ Architecture Principles

### Layered Architecture

```
API Layer (FastAPI routes)
    ↓
Core Layer (Business logic)
    ↓
Services Layer (External integrations)
    ↓
Database Layer (Data access)
```

### Key Design Patterns

1. **Dependency Injection**: Services injected via FastAPI dependencies
2. **Repository Pattern**: Database operations isolated in DB layer
3. **Service Pattern**: External API calls wrapped in service classes
4. **Factory Pattern**: Configuration management with settings
5. **Context Manager**: Database connections with proper cleanup

### Code Quality Standards

- **File Size**: Max 400 lines per file
- **Type Safety**: Full type hints with Pydantic
- **Error Handling**: Custom exceptions with proper logging
- **Logging**: Structured logging with context
- **Testing**: Unit tests with >80% coverage (to implement)

## 🔧 Configuration

### Environment Variables

See `.env.example` for all required variables. Key categories:

- **API**: API_KEY, API_SECRET
- **Database**: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD
- **OpenAI**: OPENAI_API_KEY, OPENAI_ORGANIZATION
- **Pinecone**: PINECONE_API_KEY, PINECONE_INDEX_NAME
- **AWS**: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- **LangSmith**: LANGCHAIN_API_KEY (optional)

### Customization

The system is designed for easy customization:

- Add new analysis types: Create new workers in `core/`
- Add new document types: Update `schemas/common.py`
- Add new prompts: Insert into `analyzer_prompts` table
- Add new services: Create in `services/`

## 📈 Monitoring & Observability

### Structured Logging

All operations are logged with context:

```python
logger.info("analysis_started", user_id="user123", session_id="abc123")
logger.error("analysis_failed", error=str(e), session_id="abc123")
```

### LangSmith Tracing

If configured, all LLM calls are traced in LangSmith:
- Open https://smith.langchain.com
- View traces for your project
- Analyze token usage, latency, errors

### Health Checks

```bash
GET /health
```

Returns service status for all components.

## 🔄 Migration from Old System

See `MIGRATION_GUIDE.md` for detailed migration instructions.

### Key Changes

| Old System | New System | Benefit |
|------------|------------|---------|
| Hardcoded secrets | Environment variables | Security |
| 2600-line files | 200-line files | Maintainability |
| Mixed responsibilities | Clean layers | Testability |
| No connection pooling | Proper pooling | Performance |
| Generic exceptions | Typed exceptions | Error handling |
| Print statements | Structured logging | Observability |

### Recent Implementations

**Guideline Access Control** (October 2025):
- Organization-specific guideline visibility
- Three-tier access control (private, shared public, universal)
- CSV-based admin management
- See: `GUIDELINE_ACCESS_IMPLEMENTATION_SUMMARY.md`

**Prompts Sync Integration** (October 2025):
- Backwards-compatible bulk prompt updates
- Google Colab and CLI support
- Legacy workflow compatibility
- See: `PROMPTS_SYNC_INTEGRATION_SUMMARY.md`

## 🧪 Testing

```bash
# Run tests (to implement)
pytest tests/

# With coverage
pytest --cov=. tests/

# Specific test file
pytest tests/test_analyzer.py -v
```

## 📝 Development

### Adding New Features

1. **Define schema** in `schemas/`
2. **Implement business logic** in `core/`
3. **Create service** if external API needed in `services/`
4. **Add database operations** in `db/`
5. **Create API route** in `api/routes/`
6. **Write tests** in `tests/`

### Code Style

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy .
```

## 🤝 Contributing

1. Follow the existing architecture patterns
2. Keep files under 400 lines
3. Add type hints to all functions
4. Write docstrings for public methods
5. Add structured logging
6. Include tests for new features

## 📄 License

[Your License Here]

## 🆘 Support

For issues or questions:
1. Check the logs (structured JSON format)
2. Review LangSmith traces if enabled
3. Consult the migration guide
4. Contact the development team

## 🎓 Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangSmith Documentation](https://docs.smith.langchain.com/)

