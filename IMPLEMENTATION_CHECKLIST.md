# Implementation Checklist - Quick Reference

**Status:** 🔴 Not Started  
**Target Completion:** 30 days (6 weeks)  
**Current Feature Parity:** 20% (Analyzer only)  
**Target Feature Parity:** 100%

---

## 📊 OVERALL PROGRESS

- [ ] **Phase 1: Core Business Logic** (10 days) - 0%
  - [ ] Chatbot - 0%
  - [ ] Evaluator - 0%
- [ ] **Phase 2: Admin & Management** (5 days) - 0%
- [ ] **Phase 3: UI & Integration** (5 days) - 0%
- [ ] **Phase 4: Additional Features** (5 days) - 0%
- [ ] **Phase 5: Testing & Docs** (5 days) - 0%

---

## 🎯 CRITICAL PATH ITEMS (Must Complete)

### 1️⃣ CHATBOT - 5 Days
- [ ] Core logic: `core/chatbot.py` (~250 lines)
- [ ] Schemas: Expand `schemas/chatbot.py` (~150 lines)
- [ ] Database: Expand `db/chatbot_db.py` (~200 lines)
- [ ] API routes: Expand `api/routes/chatbot.py` (~150 lines)
- [ ] Utilities: `utils/pdf_mappings.py` (~100 lines)
- [ ] Database migration: `migrations/002_chatbot_schema.sql`
- [ ] Tests: `tests/test_chatbot.py`

### 2️⃣ EVALUATOR - 5 Days
- [ ] Core logic: `core/evaluator.py` (~280 lines)
- [ ] Schemas: Expand `schemas/evaluator.py` (~180 lines)
- [ ] Database: Expand `db/evaluator_db.py` (~220 lines)
- [ ] API routes: Expand `api/routes/evaluator.py` (~180 lines)
- [ ] Prompts: `services/prompts.py` (~200 lines)
- [ ] Database migration: `migrations/003_evaluator_schema.sql`
- [ ] Tests: `tests/test_evaluator.py`

### 3️⃣ ADMIN APIs - 5 Days
- [ ] API routes: Expand `api/routes/admin.py` (~400 lines)
- [ ] Schemas: `schemas/admin.py` (~200 lines)
- [ ] Database: Expand `db/prompts_db.py` (~350 lines)
- [ ] Database migration: `migrations/004_admin_prompts.sql`
- [ ] Tests: `tests/test_admin_apis.py`

---

## 📋 DETAILED TASK BREAKDOWN

### CHATBOT IMPLEMENTATION
**Files:** 6 files, ~850 lines

#### Core (`core/chatbot.py`)
- [ ] `ChatbotEngine` class
- [ ] `query_refiner()` method - Determine retrieval need
- [ ] `extract_context()` method - Pinecone retrieval
- [ ] `generate_response()` method - Main chat logic
- [ ] `format_for_whatsapp()` method

#### Schemas (`schemas/chatbot.py`)
- [ ] `ChatRequest` schema
- [ ] `ChatResponse` schema
- [ ] `FeedbackRequest` schema
- [ ] `SessionResponse` schema
- [ ] `ContextInfo` schema
- [ ] `SourceInfo` schema
- [ ] Model enum

#### Database (`db/chatbot_db.py`)
- [ ] `get_user_conversations()` - Build conversation string
- [ ] `get_user_data()` - Last session with messages
- [ ] `save_feedback()` method
- [ ] Schema update: Add context_data, response_id, source columns

#### API Routes (`api/routes/chatbot.py`)
- [ ] `POST /chat` - Main chat endpoint
- [ ] `GET /sessions` - List sessions
- [ ] `GET /sessions/{session_id}` - Get conversation
- [ ] `GET /sessions/last` - Get last session
- [ ] `POST /feedback` - Submit feedback

#### Utilities (`utils/pdf_mappings.py`)
- [ ] Load PDF mappings
- [ ] Lookup by PDF name
- [ ] Return structured source info
- [ ] `get_unique_sources()` utility

#### Database Migration
```sql
ALTER TABLE chatbot_messages ADD COLUMN response_id, context_data, sources;
ALTER TABLE chatbot_sessions ADD COLUMN source;
CREATE TABLE chatbot_feedback;
```

---

### EVALUATOR IMPLEMENTATION
**Files:** 5 files, ~1060 lines

#### Core (`core/evaluator.py`)
- [ ] `ProposalEvaluator` class
- [ ] `process_proposal()` method
- [ ] `process_tor()` method
- [ ] `evaluate()` method - Main evaluation
- [ ] Three-part analysis (P_Internal, P_External, P_Delta)
- [ ] `answer_followup()` method

#### Schemas (`schemas/evaluator.py`)
- [ ] `EvaluatorRequest` schema
- [ ] `EvaluatorResponse` schema
- [ ] `EvaluatorFollowupRequest` schema
- [ ] `EvaluatorFeedbackRequest` schema
- [ ] `EvaluatorSessionResponse` schema
- [ ] Analysis section schemas

#### Database (`db/evaluator_db.py`)
- [ ] Expand `create_session()` - Store proposal/ToR
- [ ] `save_evaluation_results()` - Store three analyses
- [ ] `get_session()` - Retrieve with analyses
- [ ] `get_user_sessions()` - List evaluations
- [ ] `save_followup()` method
- [ ] `save_feedback()` method
- [ ] `update_session_title()` method
- [ ] `get_session_by_ids()` - Batch retrieval

#### API Routes (`api/routes/evaluator.py`)
- [ ] `POST /evaluate` - Main evaluation endpoint
- [ ] `GET /sessions` - List sessions
- [ ] `GET /sessions/{session_id}` - Get details
- [ ] `POST /followup` - Follow-up Q&A
- [ ] `POST /feedback` - Submit feedback
- [ ] `PUT /sessions/{session_id}/title` - Update title
- [ ] `POST /sessions/batch` - Batch retrieval

#### Prompts (`services/prompts.py`)
- [ ] P_Internal analysis prompt
- [ ] P_External analysis prompt
- [ ] P_Delta analysis prompt
- [ ] ToR summary prompt
- [ ] Proposal summary prompt
- [ ] Prompt templates
- [ ] Formatting utilities

#### Database Migration
```sql
ALTER TABLE evaluator_sessions ADD COLUMNS for proposal, ToR, title;
CREATE TABLE evaluator_followups;
CREATE TABLE evaluator_feedback;
CREATE TABLE organization_guidelines;
```

---

### ADMIN/PROMPT MANAGEMENT
**Files:** 3 files, ~950 lines

#### API Routes (`api/routes/admin.py`)
- [ ] **Analyzer Prompts**
  - [ ] `GET /prompts/analyzer`
  - [ ] `PUT /prompts/analyzer`
  - [ ] `DELETE /prompts/analyzer`
- [ ] **Analyzer Summary Prompts**
  - [ ] `GET /prompts/analyzer/summary`
  - [ ] `PUT /prompts/analyzer/summary`
- [ ] **Proposal Summary Prompts**
  - [ ] `GET /prompts/analyzer/proposal-summary`
  - [ ] `PUT /prompts/analyzer/proposal-summary`
- [ ] **Custom Prompts**
  - [ ] `POST /prompts/custom`
  - [ ] `PUT /prompts/custom`
  - [ ] `DELETE /prompts/custom`
- [ ] **Evaluator Prompts**
  - [ ] `POST /prompts/evaluator`
  - [ ] `PUT /prompts/evaluator`
  - [ ] `DELETE /prompts/evaluator`
- [ ] **ToR Summary Prompts**
  - [ ] `POST /prompts/tor-summary`
  - [ ] `PUT /prompts/tor-summary`
- [ ] **Corpus IDs**
  - [ ] `GET /prompts/corpus-ids/analyzer`
  - [ ] `GET /prompts/corpus-ids/organization`

#### Schemas (`schemas/admin.py`)
- [ ] `PromptConfigSchema`
- [ ] `PromptUpdateRequest`
- [ ] `P0SummaryPromptSchema`
- [ ] `ProposalSummaryPromptSchema`
- [ ] `CustomPromptSchema`
- [ ] `EvaluatorPromptSchema`
- [ ] `TorPromptSchema`
- [ ] Prompt type enums

#### Database (`db/prompts_db.py`)
- [ ] `get_analyzer_prompts()`
- [ ] `update_analyzer_prompts()`
- [ ] `delete_analyzer_prompts()`
- [ ] `get_summary_prompts()`
- [ ] `update_summary_prompts()`
- [ ] `get_proposal_summary_prompts()`
- [ ] `update_proposal_summary_prompts()`
- [ ] `get_custom_prompts()`
- [ ] `update_custom_prompts()`
- [ ] `delete_custom_prompts()`
- [ ] `get_evaluator_prompts()`
- [ ] `update_evaluator_prompts()`
- [ ] `delete_evaluator_prompts()`
- [ ] `get_tor_prompts()`
- [ ] `update_tor_prompts()`
- [ ] `get_analyzer_corpus_ids()`
- [ ] `get_organization_corpus_ids()`

#### Database Migration
```sql
CREATE TABLE evaluator_prompts;
CREATE TABLE tor_summary_prompts;
ALTER TABLE analyzer_prompts ADD summary_prompt, proposal_summary_prompt;
```

---

## 🎨 STREAMLIT UI

**Files:** 8 files, ~770 lines

### Main App
- [ ] `streamlit_app/main.py` (~150 lines)
  - [ ] Navigation between modes
  - [ ] Admin panel with auth
  - [ ] PDF mappings cache

### Pages
- [ ] `streamlit_app/pages/chatbot.py` (~120 lines)
  - [ ] Message history display
  - [ ] User input
  - [ ] Session selector
  - [ ] Sources display
  - [ ] Feedback buttons
- [ ] `streamlit_app/pages/analyzer.py` (~140 lines)
  - [ ] Document upload
  - [ ] Type/label selectors
  - [ ] Results display
  - [ ] Follow-up input
  - [ ] Feedback per section
- [ ] `streamlit_app/pages/evaluator.py` (~120 lines)
  - [ ] Proposal/ToR upload
  - [ ] Organization selector
  - [ ] Three-part analysis display
  - [ ] Follow-up input
  - [ ] Feedback per section
- [ ] `streamlit_app/pages/admin.py` (~200 lines)
  - [ ] Task selector
  - [ ] Prompt editor
  - [ ] Submit updates
  - [ ] Success messages

### Utilities
- [ ] `streamlit_app/utils/api_client.py` (~100 lines)
  - [ ] API client class
  - [ ] All endpoint methods
  - [ ] Auth handling
  - [ ] Error handling
- [ ] `streamlit_app/utils/helpers.py` (~80 lines)
  - [ ] Formatting utilities
  - [ ] Session management
  - [ ] Cache decorators

---

## 🔗 COMBINED & ADDITIONAL FEATURES

### Combined Analyzer+Evaluator
- [ ] `api/routes/combined.py` (~100 lines)
  - [ ] `POST /analyze-evaluate` endpoint
  - [ ] Parallel execution with ThreadPoolExecutor
  - [ ] Combined response format
  - [ ] Timeout handling (600s)

### Additional Analyzer Features
- [ ] `POST /sessions/batch` - Batch retrieval
- [ ] `PUT /sessions/{session_id}/title` - Update title
- [ ] Enhanced filtering in session queries
- [ ] Pagination metadata

### Utilities
- [ ] `utils/text_processing.py` (~100 lines)
  - [ ] `break_into_paragraphs()`
  - [ ] `get_unique_sources()`
  - [ ] Text cleaning
  - [ ] Token counting
- [ ] `utils/validation.py` (~60 lines)
  - [ ] `validate_request()`
  - [ ] Input validation
  - [ ] File type validation
- [ ] `utils/pdf_mappings.py` (~100 lines)
  - [ ] Load mappings
  - [ ] Lookup utilities
  - [ ] Source formatting
- [ ] `utils/encryption.py` (~80 lines)
  - [ ] Encryption/decryption
  - [ ] Password generation

### PDF Processing Scripts
- [ ] `scripts/chunk_pdf_files.py` (~150 lines)
- [ ] `scripts/index_pdf_chunks.py` (~150 lines)
- [ ] `scripts/batch_index.py` (~100 lines)
- [ ] `scripts/README.md` - Documentation

---

## 🧪 COMPREHENSIVE TESTING

### Unit Tests (~1000 lines)
- [ ] `tests/core/test_chatbot.py` (~150 lines)
- [ ] `tests/core/test_evaluator.py` (~150 lines)
- [ ] `tests/db/test_chatbot_db.py` (~100 lines)
- [ ] `tests/db/test_evaluator_db.py` (~100 lines)
- [ ] `tests/db/test_prompts_db.py` (~100 lines)
- [ ] `tests/services/test_llm.py` (~100 lines)
- [ ] `tests/utils/test_text_processing.py` (~80 lines)

### Integration Tests (~420 lines)
- [ ] `tests/integration/test_chatbot_api.py` (~120 lines)
- [ ] `tests/integration/test_evaluator_api.py` (~120 lines)
- [ ] `tests/integration/test_admin_api.py` (~100 lines)
- [ ] `tests/integration/test_combined_api.py` (~80 lines)

### E2E Tests
- [ ] `tests/e2e/test_complete_workflows.py` (~150 lines)

### Test Infrastructure
- [ ] `tests/conftest.py` - Fixtures
- [ ] `tests/factories.py` - Test data
- [ ] `tests/mocks.py` - Mock services

### Performance Tests
- [ ] `tests/performance/test_load.py` (~100 lines)

### Coverage Target
- [ ] >80% overall code coverage
- [ ] 100% coverage for critical paths

---

## 📚 DOCUMENTATION UPDATES

### API Documentation
- [ ] Update `README.md` with all endpoints
- [ ] Document chatbot API
- [ ] Document evaluator API
- [ ] Document admin API
- [ ] Request/response examples
- [ ] Error codes reference

### Architecture Documentation
- [ ] Expand `docs/ARCHITECTURE.md`
- [ ] Chatbot architecture
- [ ] Evaluator architecture
- [ ] Admin system architecture
- [ ] Data flow diagrams
- [ ] Integration points

### Development Guide
- [ ] Expand `docs/DEVELOPMENT.md`
- [ ] Adding new features
- [ ] Testing strategy
- [ ] Code style guidelines
- [ ] Database migrations
- [ ] Deployment process

### Migration Guide
- [ ] Update `MIGRATION_GUIDE.md`
- [ ] Chatbot migration steps
- [ ] Evaluator migration steps
- [ ] Admin API migration
- [ ] Database migrations
- [ ] Troubleshooting

### User Guides
- [ ] `docs/USER_GUIDE_CHATBOT.md`
- [ ] `docs/USER_GUIDE_EVALUATOR.md`
- [ ] `docs/USER_GUIDE_ADMIN.md`
- [ ] `docs/USER_GUIDE_STREAMLIT.md`

### API Reference
- [ ] Ensure all endpoints have docstrings
- [ ] Ensure all schemas have descriptions
- [ ] Add examples to endpoints
- [ ] Export OpenAPI spec
- [ ] Generate API docs site

---

## 📈 PROGRESS TRACKING

### Week 1: Chatbot Foundation ⏳
- [ ] Day 1-2: Core logic + Database
- [ ] Day 3-4: API routes + Testing
- [ ] Day 5: Integration testing

### Week 2: Evaluator ⏳
- [ ] Day 1-2: Core logic + Database
- [ ] Day 3-4: API routes + Testing
- [ ] Day 5: Integration testing

### Week 3: Admin & UI ⏳
- [ ] Day 1-3: Admin API
- [ ] Day 4-5: Streamlit UI (start)

### Week 4: Integration ⏳
- [ ] Day 1-2: Streamlit UI (finish)
- [ ] Day 3-5: Additional features + Utilities

### Week 5: Testing ⏳
- [ ] Day 1-3: Comprehensive testing
- [ ] Day 4-5: Bug fixes + Polish

### Week 6: Launch ⏳
- [ ] Day 1-2: Documentation
- [ ] Day 3-4: Final testing
- [ ] Day 5: Production deployment

---

## 🎯 DEFINITION OF DONE

For each feature to be considered complete:
- [ ] Code implemented following architecture patterns
- [ ] File sizes < 400 lines
- [ ] Type hints present
- [ ] Docstrings present
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests written
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Linter passing
- [ ] Type checker passing
- [ ] Manually tested
- [ ] No hardcoded credentials
- [ ] Error handling present
- [ ] Structured logging added
- [ ] Merged to main branch

---

## 📊 METRICS DASHBOARD

### Code Coverage
- **Current:** 0%
- **Target:** >80%
- **Critical Path Target:** 100%

### Feature Parity
- **Current:** 20% (Analyzer only)
- **Target:** 100%

### File Count
- **Current:** 30 files
- **Expected:** ~50 files
- **Target:** All files < 400 lines

### Lines of Code
- **Current:** ~2,621 lines
- **Expected Addition:** ~4,600 lines
- **Total Expected:** ~7,200 lines
- **Improvement vs Original:** Still -52% (original was 15,116)

### Test Coverage
- **Unit Tests:** 0 / ~15 files
- **Integration Tests:** 0 / ~5 files
- **E2E Tests:** 0 / ~2 files
- **Performance Tests:** 0 / ~1 file

---

## 🚨 BLOCKERS & RISKS

### Current Blockers
- None yet

### Potential Risks
1. **Complexity Risk:** Chatbot query refinement logic may be complex
2. **Integration Risk:** Evaluator needs org guidelines table
3. **Performance Risk:** Combined endpoint timeout needs tuning
4. **Testing Risk:** Need mock data for Pinecone/LLM services

### Mitigation Strategies
1. Port logic incrementally with tests
2. Create guidelines table early
3. Use ThreadPoolExecutor with proper timeout
4. Create comprehensive mock fixtures

---

## 📞 QUICK REFERENCE

### Key Documents
- **Full Plan:** `MISSING_FUNCTIONALITY_IMPLEMENTATION_PLAN.md`
- **This Checklist:** `IMPLEMENTATION_CHECKLIST.md`
- **Original Code:** `202509-ABCD-Document-Analyzer/`
- **New Code:** `202510-ABCD-Document-Analyzer-Improved/`

### File Locations to Port From
- Chatbot: `chatbot_handlers.py`, `gpt_utils.py:query_refiner`
- Evaluator: `custom_analyzer_handlers.py:generate_evaluator_comments`
- Admin: `admin_apis/abcd_admin_prompts_fastapi.py`
- Streamlit: `abcd_streamlit_main.py`, `streamlit_utils/*`

### Quick Commands
```bash
# Run tests
pytest tests/ -v --cov

# Run specific test
pytest tests/test_chatbot.py -v

# Check coverage
pytest --cov=. --cov-report=html

# Start FastAPI
uvicorn api.main:app --reload --port 8001

# Start Streamlit
streamlit run streamlit_app/main.py --server.port 8501

# Format code
black .

# Lint
ruff check .

# Type check
mypy .
```

---

**Document Version:** 1.0  
**Last Updated:** October 6, 2025  
**Next Review:** End of Week 1  

**Ready to start implementation! 🚀**

