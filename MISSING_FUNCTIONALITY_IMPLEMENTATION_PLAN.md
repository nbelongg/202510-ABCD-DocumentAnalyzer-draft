# Missing Functionality Implementation Plan
# Document Analyzer - Complete Feature Parity

**Created:** October 6, 2025  
**Target:** Achieve 100% feature parity with original system (minus Collateral Analyzer)  
**Estimated Total Effort:** 4-6 weeks (1 developer)

---

## 📊 Executive Summary

### Current State
- ✅ **Analyzer**: 100% complete with improved architecture
- ❌ **Chatbot**: 0% complete (stub only)
- ❌ **Evaluator**: 0% complete (stub only)
- ❌ **Admin APIs**: 5% complete (stubs only)
- ❌ **Streamlit UI**: 0% complete (not present)
- ❌ **Utilities**: 10% complete (empty directory)

### Target State
- ✅ All original features implemented
- ✅ Clean architecture maintained
- ✅ Files under 400 lines
- ✅ Full test coverage
- ✅ Production ready

---

## 🎯 Implementation Roadmap

### Phase 1: Core Business Logic (Week 1-2)
1. **Chatbot Implementation** - 5 days
2. **Evaluator Implementation** - 5 days

### Phase 2: Admin & Management (Week 3)
3. **Admin/Prompt Management APIs** - 5 days

### Phase 3: UI & Integration (Week 4)
4. **Streamlit UI** - 3 days
5. **Combined Endpoints** - 1 day
6. **Utilities & Helpers** - 1 day

### Phase 4: Additional Features (Week 5)
7. **PDF Processing Scripts** - 2 days
8. **Additional Analyzer Features** - 3 days

### Phase 5: Testing & Documentation (Week 6)
9. **Comprehensive Tests** - 3 days
10. **Documentation Updates** - 2 days

---

# DETAILED IMPLEMENTATION TASKS

---

## 1️⃣ CHATBOT IMPLEMENTATION

**Priority:** HIGH  
**Estimated Effort:** 5 days  
**Dependencies:** None  
**Files to Create:** 5-6 files  
**Lines of Code:** ~800 lines

### 1.1 Core Business Logic

#### File: `core/chatbot.py` (~250 lines)

**Tasks:**
- [ ] Create `ChatbotEngine` class
- [ ] Implement query refinement logic
  - [ ] Port `query_refiner` from original `gpt_utils.py`
  - [ ] Determine if retrieval is needed
  - [ ] Refine user query for better context
- [ ] Implement context extraction
  - [ ] Integration with PineconeService
  - [ ] Extract unique chunks (top_k with multiplier)
  - [ ] Build context from retrieved documents
- [ ] Implement response generation
  - [ ] Call LLM with conversation history
  - [ ] Include retrieved context if needed
  - [ ] Handle "within knowledge base" detection
- [ ] Implement conversation management
  - [ ] Build conversation string from history
  - [ ] Format messages for LLM
- [ ] Implement WhatsApp-specific formatting
  - [ ] Break responses into paragraphs
  - [ ] Handle character limits

**Code Structure:**
```python
class ChatbotEngine:
    def __init__(self):
        self.llm_service = LLMService()
        self.pinecone = PineconeService()
        self.db = ChatbotDB()
        
    async def query_refiner(self, conversation: str, query: str) -> Tuple[bool, str]:
        """Determine if retrieval needed and refine query"""
        
    async def extract_context(self, query: str, top_k: int = 4) -> Dict:
        """Extract context from Pinecone"""
        
    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Main chat response generation"""
        
    def format_for_whatsapp(self, response: str) -> str:
        """Format response for WhatsApp"""
```

#### File: `schemas/chatbot.py` (expand from 68 lines to ~150 lines)

**Tasks:**
- [ ] Add `ChatRequest` schema
  - [ ] user_id, user_name, user_email
  - [ ] session_id (optional)
  - [ ] question/query
  - [ ] model selection (enum)
  - [ ] source (e.g., "WA" for WhatsApp)
- [ ] Add `ChatResponse` schema
  - [ ] session_id, response_id
  - [ ] response text
  - [ ] contextInfo array
  - [ ] sources array
- [ ] Add `FeedbackRequest` schema
  - [ ] response_id, feedback (bool), feedback_note
- [ ] Add `SessionResponse` schema
- [ ] Add `ConversationMessage` schema
- [ ] Add `ContextInfo` schema
- [ ] Add `SourceInfo` schema
- [ ] Add model enum (GPT-4, GPT-4o, Claude, etc.)

#### File: `db/chatbot_db.py` (expand from 93 lines to ~200 lines)

**Tasks:**
- [ ] Expand `create_session` to handle source parameter
- [ ] Implement `get_user_conversations` - Build conversation string
- [ ] Implement `get_user_data` - Get last session with messages
- [ ] Implement `save_feedback` method
- [ ] Add context storage in messages (JSON field)
- [ ] Add sources storage in messages (JSON field)
- [ ] Update database schema if needed
  - [ ] Add `context_data` JSON column
  - [ ] Add `response_id` column
  - [ ] Add `source` column

#### File: `api/routes/chatbot.py` (expand from 17 lines to ~150 lines)

**Tasks:**
- [ ] Implement `POST /chat` endpoint
  - [ ] Accept ChatRequest
  - [ ] Call ChatbotEngine
  - [ ] Return ChatResponse with context/sources
- [ ] Implement `GET /sessions` endpoint
  - [ ] List user's chat sessions
  - [ ] Include message counts
  - [ ] Sort by last_message_at
- [ ] Implement `GET /sessions/{session_id}` endpoint
  - [ ] Return full conversation history
  - [ ] Include context and sources
- [ ] Implement `GET /sessions/last` endpoint
  - [ ] Get user's most recent session
  - [ ] Support source filtering (e.g., WhatsApp)
- [ ] Implement `POST /feedback` endpoint
  - [ ] Accept FeedbackRequest
  - [ ] Save to database

#### File: `utils/pdf_mappings.py` (~100 lines)

**Tasks:**
- [ ] Port `filemapping_utils.py` functionality
- [ ] Load PDF mappings from CSV or database
- [ ] Provide mapping lookup by PDF name
- [ ] Return structured source info:
  - [ ] sno, title, author_organization
  - [ ] publication_year, link, pdf_title
- [ ] Implement `get_unique_sources` utility

### 1.2 Database Schema Updates

**SQL Script:** Create `migrations/002_chatbot_schema.sql`

```sql
-- Update chatbot_messages table
ALTER TABLE chatbot_messages 
ADD COLUMN response_id VARCHAR(255),
ADD COLUMN context_data JSON,
ADD COLUMN sources JSON,
ADD INDEX idx_response_id (response_id);

-- Update chatbot_sessions table  
ALTER TABLE chatbot_sessions
ADD COLUMN source VARCHAR(50),
ADD INDEX idx_user_source (user_id, source);

-- Create feedback table
CREATE TABLE chatbot_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    response_id VARCHAR(255) NOT NULL,
    feedback BOOLEAN NOT NULL,
    feedback_note TEXT,
    created_at DATETIME,
    INDEX idx_response_id (response_id)
);
```

### 1.3 Integration Tasks

**Tasks:**
- [ ] Update `services/llm.py` with chatbot-specific prompts
- [ ] Add query refinement prompt
- [ ] Add "within knowledge base" detection logic
- [ ] Test Pinecone integration for retrieval
- [ ] Add WhatsApp formatting utilities to `utils/`

### 1.4 Testing

**Create:** `tests/test_chatbot.py`

**Tasks:**
- [ ] Test query refinement
- [ ] Test context extraction
- [ ] Test response generation
- [ ] Test conversation history building
- [ ] Test WhatsApp formatting
- [ ] Test feedback submission
- [ ] Integration test: Full chat flow

---

## 2️⃣ EVALUATOR IMPLEMENTATION

**Priority:** HIGH  
**Estimated Effort:** 5 days  
**Dependencies:** None  
**Files to Create:** 4-5 files  
**Lines of Code:** ~700 lines

### 2.1 Core Business Logic

#### File: `core/evaluator.py` (~280 lines)

**Tasks:**
- [ ] Create `ProposalEvaluator` class
- [ ] Implement proposal document processing
  - [ ] Accept proposal PDF or text
  - [ ] Extract and summarize proposal content
- [ ] Implement ToR document processing
  - [ ] Accept ToR PDF or text
  - [ ] Extract ToR requirements
- [ ] Implement organization guidelines integration
  - [ ] Fetch from database based on org_id + guideline_id
  - [ ] Include in evaluation context
- [ ] Implement three-part analysis:
  - [ ] **P_Internal**: Internal consistency of proposal
  - [ ] **P_External**: Alignment with ToR
  - [ ] **P_Delta**: Gaps between proposal and ToR
- [ ] Implement concurrent analysis
  - [ ] Run three analyses in parallel
  - [ ] Aggregate results
- [ ] Implement follow-up Q&A
  - [ ] Answer questions about specific sections
  - [ ] Use original proposal/ToR context

**Code Structure:**
```python
class ProposalEvaluator:
    def __init__(self):
        self.llm_service = LLMService()
        self.pdf_service = PDFService()
        self.db = EvaluatorDB()
        
    async def process_proposal(self, file_or_text) -> str:
        """Extract and summarize proposal"""
        
    async def process_tor(self, file_or_text) -> str:
        """Extract ToR requirements"""
        
    async def evaluate(self, request: EvaluatorRequest) -> EvaluatorResponse:
        """Main evaluation logic"""
        # 1. Process proposal and ToR
        # 2. Get organization guidelines
        # 3. Run three analyses in parallel
        # 4. Aggregate and return results
        
    async def answer_followup(self, request: EvaluatorFollowupRequest) -> str:
        """Answer follow-up questions"""
```

#### File: `schemas/evaluator.py` (expand from 79 lines to ~180 lines)

**Tasks:**
- [ ] Add `EvaluatorRequest` schema
  - [ ] user_id, user_name, session_id
  - [ ] document_type (enum)
  - [ ] organization_id, org_guideline_id
  - [ ] proposal_text OR proposal_file_data
  - [ ] tor_text OR tor_file_data
- [ ] Add `EvaluatorResponse` schema
  - [ ] session_id
  - [ ] internal_analysis (P_Internal)
  - [ ] external_analysis (P_External)
  - [ ] delta_analysis (P_Delta)
  - [ ] overall_score (optional)
  - [ ] summary
- [ ] Add `EvaluatorFollowupRequest` schema
  - [ ] user_id, session_id
  - [ ] query, section
- [ ] Add `EvaluatorFeedbackRequest` schema
- [ ] Add `EvaluatorSessionResponse` schema
- [ ] Add analysis section schemas

#### File: `db/evaluator_db.py` (expand from 71 lines to ~220 lines)

**Tasks:**
- [ ] Expand `create_session` to store proposal/ToR metadata
- [ ] Implement `save_evaluation_results` - Store all three analyses
- [ ] Implement `get_session` - Retrieve session with analyses
- [ ] Implement `get_user_sessions` - List user's evaluations
- [ ] Implement `save_followup` method
- [ ] Implement `save_feedback` method
- [ ] Implement `update_session_title` method
- [ ] Implement `get_session_by_ids` - Batch retrieval
- [ ] Store proposal and ToR texts/links for followups

#### File: `api/routes/evaluator.py` (expand from 17 lines to ~180 lines)

**Tasks:**
- [ ] Implement `POST /evaluate` endpoint
  - [ ] Accept proposal + ToR (files or text)
  - [ ] Accept organization_id + guideline_id
  - [ ] Call ProposalEvaluator
  - [ ] Return three-part analysis
- [ ] Implement `GET /sessions` endpoint
  - [ ] List user's evaluation sessions
- [ ] Implement `GET /sessions/{session_id}` endpoint
  - [ ] Return full evaluation details
- [ ] Implement `POST /followup` endpoint
  - [ ] Answer questions about evaluation
  - [ ] Support section-specific queries
- [ ] Implement `POST /feedback` endpoint
  - [ ] Save feedback on evaluation sections
- [ ] Implement `PUT /sessions/{session_id}/title` endpoint
  - [ ] Update session title
- [ ] Implement `POST /sessions/batch` endpoint
  - [ ] Retrieve multiple sessions by ID

#### File: `services/prompts.py` (~200 lines)

**Tasks:**
- [ ] Create centralized prompts management
- [ ] Add evaluator prompts:
  - [ ] P_Internal analysis prompt
  - [ ] P_External analysis prompt  
  - [ ] P_Delta analysis prompt
  - [ ] ToR summary prompt
  - [ ] Proposal summary prompt
- [ ] Add prompt templates with placeholders
- [ ] Add prompt formatting utilities

### 2.2 Database Schema Updates

**SQL Script:** Create `migrations/003_evaluator_schema.sql`

```sql
-- Expand evaluator_sessions table
ALTER TABLE evaluator_sessions
ADD COLUMN document_type VARCHAR(100),
ADD COLUMN proposal_text LONGTEXT,
ADD COLUMN proposal_url VARCHAR(500),
ADD COLUMN tor_text LONGTEXT,
ADD COLUMN tor_url VARCHAR(500),
ADD COLUMN session_title VARCHAR(500),
ADD COLUMN processing_time FLOAT;

-- Create evaluator_followups table
CREATE TABLE evaluator_followups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    answer TEXT,
    section VARCHAR(100),
    created_at DATETIME,
    INDEX idx_session (session_id)
);

-- Create evaluator_feedback table
CREATE TABLE evaluator_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    section VARCHAR(100),
    response_id VARCHAR(255),
    feedback BOOLEAN,
    feedback_note TEXT,
    created_at DATETIME,
    INDEX idx_session (session_id)
);

-- Create organization_guidelines table (if not exists)
CREATE TABLE IF NOT EXISTS organization_guidelines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    guideline_id VARCHAR(255) UNIQUE NOT NULL,
    organization_id VARCHAR(255) NOT NULL,
    guideline_name VARCHAR(255),
    guideline_text LONGTEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME,
    INDEX idx_org (organization_id)
);
```

### 2.3 Integration Tasks

**Tasks:**
- [ ] Add ToR summary prompts to `PromptsDB`
- [ ] Implement concurrent execution for three analyses
- [ ] Add evaluation-specific LLM methods
- [ ] Test PDF extraction for proposals and ToRs
- [ ] Add organization guidelines CRUD operations

### 2.4 Testing

**Create:** `tests/test_evaluator.py`

**Tasks:**
- [ ] Test proposal processing
- [ ] Test ToR processing
- [ ] Test three-part analysis
- [ ] Test concurrent execution
- [ ] Test organization guidelines integration
- [ ] Test followup Q&A
- [ ] Integration test: Full evaluation flow

---

## 3️⃣ ADMIN/PROMPT MANAGEMENT APIs

**Priority:** MEDIUM  
**Estimated Effort:** 5 days  
**Dependencies:** Evaluator (for evaluator prompts)  
**Files to Create:** 3-4 files  
**Lines of Code:** ~600 lines

### 3.1 Admin Routes Implementation

#### File: `api/routes/admin.py` (expand from 17 lines to ~400 lines)

**Tasks:**

##### **Analyzer Prompts Endpoints**
- [ ] `GET /prompts/analyzer` - Get analyzer prompts
  - [ ] Filter by prompt_label, document_type
  - [ ] Return base_prompt, customization_prompt
- [ ] `PUT /prompts/analyzer` - Update analyzer prompts
  - [ ] Accept list of updates
  - [ ] Update multiple prompts at once
- [ ] `DELETE /prompts/analyzer` - Delete analyzer prompts
  - [ ] By prompt_label + document_type

##### **Analyzer Summary Prompts**
- [ ] `GET /prompts/analyzer/summary` - Get P0 summary prompts
  - [ ] Filter by document_type
- [ ] `PUT /prompts/analyzer/summary` - Update summary prompts
  - [ ] Update multiple at once

##### **Proposal Summary Prompts**
- [ ] `GET /prompts/analyzer/proposal-summary` - Get proposal summary prompts
- [ ] `PUT /prompts/analyzer/proposal-summary` - Update proposal prompts

##### **Organization Custom Prompts**
- [ ] `POST /prompts/custom` - Get custom prompts
  - [ ] Filter by document_type + organization_id
- [ ] `PUT /prompts/custom` - Update custom prompts
  - [ ] Organization-specific updates
- [ ] `DELETE /prompts/custom` - Delete custom prompts
  - [ ] By document_type + organization_id

##### **Evaluator Prompts**
- [ ] `POST /prompts/evaluator` - Get evaluator prompts
  - [ ] Filter by partition_type, document_type, organization_id
- [ ] `PUT /prompts/evaluator` - Update evaluator prompts
  - [ ] Update P_Internal, P_External, P_Delta prompts
- [ ] `DELETE /prompts/evaluator` - Delete evaluator prompts

##### **ToR Summary Prompts**
- [ ] `POST /prompts/tor-summary` - Get ToR summary prompts
- [ ] `PUT /prompts/tor-summary` - Update ToR prompts

##### **Corpus ID Endpoints**
- [ ] `GET /prompts/corpus-ids/analyzer` - Get analyzer corpus IDs
- [ ] `GET /prompts/corpus-ids/organization` - Get organization corpus IDs

#### File: `schemas/admin.py` (~200 lines)

**Tasks:**
- [ ] Add prompt schemas
  - [ ] `PromptConfigSchema`
  - [ ] `PromptUpdateRequest`
  - [ ] `P0SummaryPromptSchema`
  - [ ] `ProposalSummaryPromptSchema`
  - [ ] `CustomPromptSchema`
  - [ ] `EvaluatorPromptSchema`
  - [ ] `TorPromptSchema`
- [ ] Add request/response wrappers
- [ ] Add enums for prompt types

#### File: `db/prompts_db.py` (expand from 139 lines to ~350 lines)

**Tasks:**
- [ ] Implement CRUD for analyzer prompts
  - [ ] `get_analyzer_prompts`
  - [ ] `update_analyzer_prompts`
  - [ ] `delete_analyzer_prompts`
- [ ] Implement CRUD for summary prompts
  - [ ] `get_summary_prompts`
  - [ ] `update_summary_prompts`
- [ ] Implement CRUD for proposal summary prompts
  - [ ] `get_proposal_summary_prompts`
  - [ ] `update_proposal_summary_prompts`
- [ ] Implement CRUD for custom (organization) prompts
  - [ ] `get_custom_prompts`
  - [ ] `update_custom_prompts`
  - [ ] `delete_custom_prompts`
- [ ] Implement CRUD for evaluator prompts
  - [ ] `get_evaluator_prompts`
  - [ ] `update_evaluator_prompts`
  - [ ] `delete_evaluator_prompts`
- [ ] Implement CRUD for ToR prompts
  - [ ] `get_tor_prompts`
  - [ ] `update_tor_prompts`
- [ ] Implement corpus ID retrieval
  - [ ] `get_analyzer_corpus_ids`
  - [ ] `get_organization_corpus_ids`

### 3.2 Database Schema Updates

**SQL Script:** Create `migrations/004_admin_prompts.sql`

```sql
-- Expand analyzer_prompts table (already exists)
-- Add columns if missing
ALTER TABLE analyzer_prompts
ADD COLUMN IF NOT EXISTS summary_prompt TEXT,
ADD COLUMN IF NOT EXISTS proposal_summary_prompt TEXT;

-- Create evaluator_prompts table
CREATE TABLE IF NOT EXISTS evaluator_prompts (
    prompt_id INT AUTO_INCREMENT PRIMARY KEY,
    partition_type VARCHAR(50) NOT NULL,  -- P_Internal, P_External, P_Delta
    document_type VARCHAR(100) NOT NULL,
    organization_id VARCHAR(255),
    org_guideline_id VARCHAR(255),
    base_prompt TEXT NOT NULL,
    customization_prompt TEXT,
    system_prompt TEXT,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 4000,
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE KEY unique_evaluator_prompt 
        (partition_type, document_type, organization_id, org_guideline_id)
);

-- Create tor_summary_prompts table
CREATE TABLE IF NOT EXISTS tor_summary_prompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    document_type VARCHAR(100) NOT NULL,
    organization_id VARCHAR(255),
    summary_prompt TEXT NOT NULL,
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE KEY unique_tor_prompt (document_type, organization_id)
);
```

### 3.3 Testing

**Create:** `tests/test_admin_apis.py`

**Tasks:**
- [ ] Test all GET endpoints
- [ ] Test all PUT endpoints
- [ ] Test all DELETE endpoints
- [ ] Test filtering logic
- [ ] Test organization-specific prompts
- [ ] Test bulk updates
- [ ] Integration test: Full CRUD cycle

---

## 4️⃣ STREAMLIT UI

**Priority:** MEDIUM  
**Estimated Effort:** 3 days  
**Dependencies:** Chatbot, Evaluator, Admin APIs  
**Files to Create:** 6-8 files  
**Lines of Code:** ~500 lines

### 4.1 Main Streamlit App

#### File: `streamlit_app/main.py` (~150 lines)

**Tasks:**
- [ ] Create main Streamlit entry point
- [ ] Add navigation between modes:
  - [ ] Chatbot
  - [ ] Analyzer
  - [ ] Evaluator
- [ ] Add admin panel (with authentication)
- [ ] Handle query parameters for admin access
- [ ] Load and cache PDF mappings

**Code Structure:**
```python
import streamlit as st
from pages import chatbot, analyzer, evaluator, admin

def main():
    st.set_page_config(page_title="ABCD Document Analyzer")
    
    # Check for admin mode
    params = st.query_params
    is_admin = check_admin_credentials(params)
    
    if is_admin:
        admin.show_admin_panel()
    
    # Main navigation
    mode = st.selectbox("Select Mode", ["Chatbot", "Analyzer", "Evaluator"])
    
    if mode == "Chatbot":
        chatbot.show_chatbot_page()
    elif mode == "Analyzer":
        analyzer.show_analyzer_page()
    elif mode == "Evaluator":
        evaluator.show_evaluator_page()
```

### 4.2 Page Components

#### File: `streamlit_app/pages/chatbot.py` (~120 lines)

**Tasks:**
- [ ] Create chatbot UI
- [ ] Add message history display
- [ ] Add user input box
- [ ] Add session selector
- [ ] Display sources and context
- [ ] Add feedback buttons (thumbs up/down)
- [ ] Call backend API (`POST /api/v1/chatbot/chat`)

#### File: `streamlit_app/pages/analyzer.py` (~140 lines)

**Tasks:**
- [ ] Create analyzer UI
- [ ] Add document upload (PDF or text)
- [ ] Add document type selector
- [ ] Add prompt label selector (P1-P5)
- [ ] Add organization ID input
- [ ] Display analysis results by section
- [ ] Add follow-up question input
- [ ] Add feedback buttons per section
- [ ] Call backend APIs

#### File: `streamlit_app/pages/evaluator.py` (~120 lines)

**Tasks:**
- [ ] Create evaluator UI
- [ ] Add proposal upload/text input
- [ ] Add ToR upload/text input
- [ ] Add organization selector
- [ ] Add guideline selector
- [ ] Display three-part analysis:
  - [ ] Internal consistency
  - [ ] External alignment
  - [ ] Delta/gaps
- [ ] Add follow-up question input
- [ ] Add feedback buttons per section
- [ ] Call backend APIs

#### File: `streamlit_app/pages/admin.py` (~200 lines)

**Tasks:**
- [ ] Create admin panel UI
- [ ] Add task selector (chatbot, analyzer, evaluator)
- [ ] For Analyzer:
  - [ ] Display current prompts
  - [ ] Allow editing base prompts
  - [ ] Allow editing customization prompts
  - [ ] Allow editing summary prompts
  - [ ] Submit updates to backend
- [ ] For Evaluator:
  - [ ] Display evaluator prompts
  - [ ] Allow editing three partition prompts
  - [ ] Submit updates to backend
- [ ] For Chatbot:
  - [ ] Display chatbot config
  - [ ] Temperature slider
  - [ ] Submit updates
- [ ] Success/error messages

### 4.3 Utilities

#### File: `streamlit_app/utils/api_client.py` (~100 lines)

**Tasks:**
- [ ] Create API client class
- [ ] Implement methods for all backend endpoints
- [ ] Handle authentication headers
- [ ] Handle errors gracefully
- [ ] Add retry logic

#### File: `streamlit_app/utils/helpers.py` (~80 lines)

**Tasks:**
- [ ] PDF mapping utilities
- [ ] Source formatting
- [ ] Context display formatting
- [ ] Session management
- [ ] Cache decorators

### 4.4 Deployment

**Tasks:**
- [ ] Create `streamlit_app/requirements.txt`
- [ ] Add Streamlit-specific dependencies
- [ ] Create run script: `run_streamlit.sh`
- [ ] Update documentation with Streamlit usage
- [ ] Test on different browsers

---

## 5️⃣ COMBINED ANALYZER+EVALUATOR ENDPOINT

**Priority:** LOW  
**Estimated Effort:** 1 day  
**Dependencies:** Analyzer, Evaluator  
**Files to Modify:** 1 file  
**Lines of Code:** ~100 lines

### 5.1 Implementation

#### File: `api/routes/combined.py` (new file, ~100 lines)

**Tasks:**
- [ ] Create `POST /analyze-evaluate` endpoint
- [ ] Accept combined parameters:
  - [ ] Analyzer params (user_id, document, prompt_labels, etc.)
  - [ ] Evaluator params (proposal, ToR, org_id, etc.)
  - [ ] Services selection (["analyzer", "evaluator"])
- [ ] Use ThreadPoolExecutor for parallel execution
- [ ] Call both analyzer and evaluator concurrently
- [ ] Return combined response
- [ ] Handle timeout (600 seconds)
- [ ] Proper error handling for partial failures

**Code Structure:**
```python
from concurrent.futures import ThreadPoolExecutor
from core.analyzer import DocumentAnalyzer
from core.evaluator import ProposalEvaluator

@router.post("/analyze-evaluate")
async def analyze_and_evaluate(
    services: List[str] = Form(["analyzer", "evaluator"]),
    # ... analyzer params
    # ... evaluator params
):
    analyzer_result = None
    evaluator_result = None
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        if "analyzer" in services:
            analyzer_future = executor.submit(analyzer.analyze, ...)
        if "evaluator" in services:
            evaluator_future = executor.submit(evaluator.evaluate, ...)
        
        # Wait with timeout
        if analyzer_future:
            analyzer_result = analyzer_future.result(timeout=600)
        if evaluator_future:
            evaluator_result = evaluator_future.result(timeout=600)
    
    return {
        "analyzer_response": analyzer_result,
        "evaluator_response": evaluator_result,
        "session_id": session_id,
        "status": determine_status(analyzer_result, evaluator_result)
    }
```

### 5.2 Integration

**Tasks:**
- [ ] Add combined router to `api/main.py`
- [ ] Add combined schemas to `schemas/common.py`
- [ ] Test concurrent execution
- [ ] Test timeout handling
- [ ] Test partial success scenarios

---

## 6️⃣ UTILITIES & HELPERS

**Priority:** LOW  
**Estimated Effort:** 1 day  
**Dependencies:** As needed  
**Files to Create:** 3-5 files  
**Lines of Code:** ~300 lines

### 6.1 Common Utilities

#### File: `utils/text_processing.py` (~100 lines)

**Tasks:**
- [ ] Port from `common_utils.py`:
  - [ ] `break_into_paragraphs` - For WhatsApp formatting
  - [ ] `get_unique_sources` - Remove duplicate sources
  - [ ] Text cleaning utilities
  - [ ] Token counting utilities

#### File: `utils/validation.py` (~60 lines)

**Tasks:**
- [ ] Port validation logic from `common_utils.py`:
  - [ ] `validate_request` - API key validation
  - [ ] Input validation helpers
  - [ ] File type validation

#### File: `utils/pdf_mappings.py` (~100 lines)

**Tasks:**
- [ ] Port from `filemapping_utils.py`
- [ ] Load PDF metadata mappings
- [ ] CSV or database-based lookup
- [ ] Return structured source information

#### File: `utils/encryption.py` (~80 lines)

**Tasks:**
- [ ] Port from `encrypter.py` if needed
- [ ] Encryption/decryption utilities
- [ ] Password generation if needed

### 6.2 Testing

**Create:** `tests/test_utils.py`

**Tasks:**
- [ ] Test text processing utilities
- [ ] Test validation logic
- [ ] Test PDF mappings
- [ ] Test encryption (if used)

---

## 7️⃣ PDF PROCESSING SCRIPTS

**Priority:** LOW  
**Estimated Effort:** 2 days  
**Dependencies:** None (standalone)  
**Files to Create:** 3-4 files  
**Lines of Code:** ~400 lines

### 7.1 Scripts Implementation

#### File: `scripts/chunk_pdf_files.py` (~150 lines)

**Tasks:**
- [ ] Port from original `PDF_Scripts/chunk_pdf_files.py`
- [ ] Extract text from PDFs
- [ ] Chunk text into smaller segments
- [ ] Configure chunk size and overlap
- [ ] Save chunks to file or database
- [ ] Add CLI interface with argparse

#### File: `scripts/index_pdf_chunks.py` (~150 lines)

**Tasks:**
- [ ] Port from original `PDF_Scripts/index_pdf_chunks.py`
- [ ] Load chunked text
- [ ] Generate embeddings
- [ ] Index to Pinecone
- [ ] Add metadata (source, page, etc.)
- [ ] Add CLI interface
- [ ] Progress tracking

#### File: `scripts/batch_index.py` (~100 lines)

**Tasks:**
- [ ] Batch processing of multiple PDFs
- [ ] Parallel processing
- [ ] Error handling and retry
- [ ] Progress reporting
- [ ] Resume capability

### 7.2 Documentation

#### File: `scripts/README.md`

**Tasks:**
- [ ] Document each script's purpose
- [ ] Usage examples
- [ ] Configuration options
- [ ] Prerequisites
- [ ] Example workflows

### 7.3 Testing

**Tasks:**
- [ ] Test with sample PDFs
- [ ] Verify chunking quality
- [ ] Verify Pinecone indexing
- [ ] Test error handling

---

## 8️⃣ ADDITIONAL ANALYZER FEATURES

**Priority:** MEDIUM  
**Estimated Effort:** 3 days  
**Dependencies:** Analyzer (already complete)  
**Files to Modify:** 2-3 files  
**Lines of Code:** ~200 lines

### 8.1 Batch Session Retrieval

#### Update: `api/routes/analyzer.py`

**Tasks:**
- [ ] Add `POST /sessions/batch` endpoint
  - [ ] Accept user_id (optional)
  - [ ] Accept number_of_sessions (limit)
  - [ ] Accept session_ids array
  - [ ] Return multiple sessions at once
- [ ] Implement in `db/analyzer_db.py`:
  - [ ] `get_sessions_by_ids`
  - [ ] `get_latest_sessions_for_user`

### 8.2 Session Title Management

#### Update: `api/routes/analyzer.py`

**Tasks:**
- [ ] Add `PUT /sessions/{session_id}/title` endpoint
  - [ ] Accept session_title
  - [ ] Update in database
- [ ] Implement in `db/analyzer_db.py`:
  - [ ] `update_session_title`

### 8.3 Enhanced Session Queries

#### Update: `db/analyzer_db.py`

**Tasks:**
- [ ] Add filtering by date range
- [ ] Add filtering by document type
- [ ] Add filtering by organization_id
- [ ] Add sorting options
- [ ] Add pagination metadata

### 8.4 Testing

**Update:** `tests/test_analyzer.py`

**Tasks:**
- [ ] Test batch retrieval
- [ ] Test session title updates
- [ ] Test advanced filtering
- [ ] Test pagination

---

## 9️⃣ COMPREHENSIVE TESTING

**Priority:** HIGH  
**Estimated Effort:** 3 days  
**Dependencies:** All features implemented  
**Files to Create:** 10-15 files  
**Lines of Code:** ~1000 lines

### 9.1 Unit Tests

**Files to Create:**
- `tests/core/test_chatbot.py` (~150 lines)
- `tests/core/test_evaluator.py` (~150 lines)
- `tests/db/test_chatbot_db.py` (~100 lines)
- `tests/db/test_evaluator_db.py` (~100 lines)
- `tests/db/test_prompts_db.py` (~100 lines)
- `tests/services/test_llm.py` (~100 lines)
- `tests/utils/test_text_processing.py` (~80 lines)

**Tasks:**
- [ ] Test all core business logic
- [ ] Test all database operations
- [ ] Test all service integrations
- [ ] Achieve >80% code coverage

### 9.2 Integration Tests

**Files to Create:**
- `tests/integration/test_chatbot_api.py` (~120 lines)
- `tests/integration/test_evaluator_api.py` (~120 lines)
- `tests/integration/test_admin_api.py` (~100 lines)
- `tests/integration/test_combined_api.py` (~80 lines)

**Tasks:**
- [ ] Test full API flows
- [ ] Test error handling
- [ ] Test authentication
- [ ] Test concurrent operations

### 9.3 End-to-End Tests

**File:** `tests/e2e/test_complete_workflows.py` (~150 lines)

**Tasks:**
- [ ] Test complete chat session
- [ ] Test complete analyzer workflow
- [ ] Test complete evaluator workflow
- [ ] Test combined analyzer+evaluator
- [ ] Test admin prompt updates

### 9.4 Test Infrastructure

**Files to Create:**
- `tests/conftest.py` - Pytest fixtures
- `tests/factories.py` - Test data factories
- `tests/mocks.py` - Mock services

**Tasks:**
- [ ] Create database fixtures
- [ ] Create mock LLM responses
- [ ] Create mock Pinecone responses
- [ ] Create test data generators

### 9.5 Performance Tests

**File:** `tests/performance/test_load.py` (~100 lines)

**Tasks:**
- [ ] Test concurrent chat sessions
- [ ] Test large document processing
- [ ] Test database connection pooling
- [ ] Measure API response times

---

## 🔟 DOCUMENTATION UPDATES

**Priority:** MEDIUM  
**Estimated Effort:** 2 days  
**Dependencies:** All features implemented  
**Files to Update/Create:** 5-7 files

### 10.1 API Documentation

**Tasks:**
- [ ] Update `README.md` with all endpoints
- [ ] Document chatbot API
- [ ] Document evaluator API
- [ ] Document admin API
- [ ] Document combined endpoint
- [ ] Add request/response examples
- [ ] Add error codes reference

### 10.2 Architecture Documentation

**File:** `docs/ARCHITECTURE.md` (expand)

**Tasks:**
- [ ] Document chatbot architecture
- [ ] Document evaluator architecture
- [ ] Document admin system architecture
- [ ] Update architecture diagrams
- [ ] Document data flow
- [ ] Document integration points

### 10.3 Development Guide

**File:** `docs/DEVELOPMENT.md` (expand)

**Tasks:**
- [ ] Document how to add new features
- [ ] Document testing strategy
- [ ] Document code style guidelines
- [ ] Document database migrations
- [ ] Document deployment process

### 10.4 Migration Guide Updates

**File:** `MIGRATION_GUIDE.md` (update)

**Tasks:**
- [ ] Update with chatbot migration steps
- [ ] Update with evaluator migration steps
- [ ] Update with admin API migration
- [ ] Update database migration scripts
- [ ] Add troubleshooting section

### 10.5 User Guides

**Files to Create:**
- `docs/USER_GUIDE_CHATBOT.md`
- `docs/USER_GUIDE_EVALUATOR.md`
- `docs/USER_GUIDE_ADMIN.md`
- `docs/USER_GUIDE_STREAMLIT.md`

**Tasks:**
- [ ] Step-by-step usage instructions
- [ ] Screenshots (if applicable)
- [ ] Common use cases
- [ ] FAQ section

### 10.6 API Reference

**File:** Generate from FastAPI

**Tasks:**
- [ ] Ensure all endpoints have proper docstrings
- [ ] Ensure all schemas have descriptions
- [ ] Add examples to all endpoints
- [ ] Export OpenAPI spec
- [ ] Generate API documentation site (Redoc/Swagger)

---

## 📋 PROJECT MANAGEMENT

### 11.1 Tracking

**Create:** `PROJECT_TRACKER.md`

**Tasks:**
- [ ] Set up task tracking system
- [ ] Create weekly milestones
- [ ] Daily standup notes
- [ ] Blocker tracking
- [ ] Progress metrics

### 11.2 Code Review Checklist

**Create:** `CODE_REVIEW_CHECKLIST.md`

**Tasks:**
- [ ] File size < 400 lines
- [ ] Type hints present
- [ ] Docstrings present
- [ ] Tests written
- [ ] Error handling present
- [ ] Logging added
- [ ] No hardcoded credentials

### 11.3 Definition of Done

**For each feature:**
- [ ] Code implemented following architecture patterns
- [ ] Unit tests written with >80% coverage
- [ ] Integration tests written
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Linter passing
- [ ] Type checker passing
- [ ] Manually tested
- [ ] Merged to main branch

---

## 📊 EFFORT SUMMARY

| Phase | Component | Priority | Effort | LOC |
|-------|-----------|----------|--------|-----|
| 1 | Chatbot Implementation | HIGH | 5 days | ~800 |
| 1 | Evaluator Implementation | HIGH | 5 days | ~700 |
| 2 | Admin/Prompt APIs | MEDIUM | 5 days | ~600 |
| 3 | Streamlit UI | MEDIUM | 3 days | ~500 |
| 3 | Combined Endpoint | LOW | 1 day | ~100 |
| 3 | Utilities | LOW | 1 day | ~300 |
| 4 | PDF Scripts | LOW | 2 days | ~400 |
| 4 | Additional Analyzer Features | MEDIUM | 3 days | ~200 |
| 5 | Comprehensive Testing | HIGH | 3 days | ~1000 |
| 5 | Documentation Updates | MEDIUM | 2 days | - |
| **TOTAL** | | | **30 days** | **~4600** |

---

## 🎯 CRITICAL PATH

### Must-Have (MVP) - 15 days
1. ✅ Chatbot Implementation (5 days)
2. ✅ Evaluator Implementation (5 days)
3. ✅ Admin APIs (core CRUD) (3 days)
4. ✅ Basic Testing (2 days)

### Should-Have - 8 days
5. Streamlit UI (3 days)
6. Combined Endpoint (1 day)
7. Additional Analyzer Features (3 days)
8. Documentation Updates (1 day)

### Nice-to-Have - 7 days
9. Utilities (1 day)
10. PDF Scripts (2 days)
11. Comprehensive Testing (3 days)
12. Full Documentation (1 day)

---

## 🚀 GETTING STARTED

### Week 1: Foundation
**Days 1-2:** Chatbot Core Logic + Database
**Days 3-4:** Chatbot API Routes + Testing
**Day 5:** Chatbot Integration Testing

### Week 2: Evaluation
**Days 1-2:** Evaluator Core Logic + Database
**Days 3-4:** Evaluator API Routes + Testing
**Day 5:** Evaluator Integration Testing

### Week 3: Admin & UI
**Days 1-3:** Admin API Implementation
**Days 4-5:** Streamlit UI (Day 1-2)

### Week 4: Polish & Integration
**Days 1-2:** Streamlit UI (continued) + Combined Endpoint
**Days 3-5:** Additional Features + Utilities

### Week 5: Testing
**Days 1-3:** Comprehensive Testing
**Days 4-5:** Bug Fixes + Polish

### Week 6: Documentation & Launch
**Days 1-2:** Documentation
**Days 3-4:** Final Testing + Bug Fixes
**Day 5:** Production Deployment

---

## 📞 SUPPORT & RESOURCES

### Key Files Reference
- **Original System:** `202509-ABCD-Document-Analyzer/`
- **New System:** `202510-ABCD-Document-Analyzer-Improved/`
- **This Plan:** `MISSING_FUNCTIONALITY_IMPLEMENTATION_PLAN.md`

### Development Resources
- FastAPI Documentation
- Pydantic Documentation  
- Streamlit Documentation
- LangChain Documentation

### Questions & Issues
Track all questions and blockers in `PROJECT_TRACKER.md`

---

**Document Version:** 1.0  
**Last Updated:** October 6, 2025  
**Status:** Ready for Implementation

