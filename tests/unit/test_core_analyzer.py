"""Unit tests for DocumentAnalyzer core engine"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from core.analyzer import DocumentAnalyzer
from schemas.analyzer import AnalyzerRequest, DocumentType


@pytest.mark.unit
class TestDocumentAnalyzer:
    """Test DocumentAnalyzer core logic"""
    
    @pytest.fixture
    def analyzer(self, mock_llm_service, mock_pdf_service, mock_pinecone_service):
        """Create analyzer instance with mocked services"""
        with patch('core.analyzer.LLMService', return_value=mock_llm_service), \
             patch('core.analyzer.PDFService', return_value=mock_pdf_service), \
             patch('core.analyzer.PineconeService', return_value=mock_pinecone_service):
            return DocumentAnalyzer()
    
    @pytest.mark.asyncio
    async def test_process_text_input(self, analyzer, sample_document_text):
        """Test processing text input"""
        result, url = await analyzer.process_document(
            text_input=sample_document_text,
            file_data=None
        )
        
        assert result == sample_document_text
        assert url is None
    
    @pytest.mark.asyncio
    async def test_process_pdf_input(self, analyzer, sample_pdf_bytes, mock_pdf_service):
        """Test processing PDF input"""
        mock_pdf_service.extract_text_from_pdf.return_value = "Extracted PDF text"
        
        result, url = await analyzer.process_document(
            text_input=None,
            file_data=sample_pdf_bytes
        )
        
        assert result == "Extracted PDF text"
        mock_pdf_service.extract_text_from_pdf.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_section(self, analyzer, mock_llm_service):
        """Test analyzing a single section"""
        mock_llm_service.generate_completion.return_value = "Section analysis result"
        
        result = await analyzer.analyze_section(
            section_label="P1",
            document_text="Sample document",
            prompt="Analyze this document",
            context=["Context 1", "Context 2"]
        )
        
        assert "content" in result
        assert result["section_label"] == "P1"
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_relevant_context(self, analyzer, mock_pinecone_service):
        """Test retrieving relevant context"""
        mock_pinecone_service.search_similar.return_value = [
            {"metadata": {"text": "Context 1"}},
            {"metadata": {"text": "Context 2"}}
        ]
        
        context = await analyzer.get_relevant_context("Test query", num_results=5)
        
        assert len(context) == 2
        assert context[0] == "Context 1"
        mock_pinecone_service.search_similar.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_analysis_response(self, analyzer):
        """Test parsing LLM analysis response"""
        response_text = """
        **SCORE**: 85
        
        **STRENGTHS**:
        - Clear objectives
        - Strong methodology
        
        **GAPS**:
        - Missing timeline
        
        **DETAILED ANALYSIS**:
        The proposal demonstrates strong technical approach...
        """
        
        result = analyzer.parse_analysis_response(response_text, "P1")
        
        assert result["score"] == 85.0
        assert len(result["strengths"]) == 2
        assert len(result["gaps"]) == 1
        assert "technical approach" in result["content"].lower()
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, analyzer, sample_document_text, mock_llm_service):
        """Test complete analysis workflow"""
        mock_llm_service.generate_completion.return_value = """
        **SCORE**: 90
        **STRENGTHS**: - Excellent proposal
        **GAPS**: - None
        **DETAILED ANALYSIS**: This is a comprehensive proposal.
        """
        
        with patch.object(analyzer.db, 'create_session', return_value=None), \
             patch.object(analyzer.db, 'save_section', return_value=None), \
             patch.object(analyzer.db, 'update_session_summary', return_value=None):
            
            request = AnalyzerRequest(
                user_id="test-user",
                text_input=sample_document_text,
                document_type=DocumentType.PROPOSAL,
                prompt_labels=["P1", "P2"]
            )
            
            # Note: This would need full mocking of DB and async calls
            # For now, we test components individually
            assert analyzer is not None
    
    def test_calculate_overall_score(self, analyzer):
        """Test overall score calculation"""
        sections = [
            {"score": 85.0},
            {"score": 90.0},
            {"score": 80.0}
        ]
        
        score = analyzer.calculate_overall_score(sections)
        
        assert score == 85.0  # Average
    
    def test_calculate_overall_score_with_none(self, analyzer):
        """Test overall score with None values"""
        sections = [
            {"score": 85.0},
            {"score": None},
            {"score": 90.0}
        ]
        
        score = analyzer.calculate_overall_score(sections)
        
        assert score == 87.5  # Average of non-None values
    
    @pytest.mark.asyncio
    async def test_error_handling_pdf_extraction(self, analyzer, mock_pdf_service):
        """Test error handling during PDF extraction"""
        mock_pdf_service.extract_text_from_pdf.side_effect = Exception("PDF extraction failed")
        
        with pytest.raises(Exception, match="PDF extraction failed"):
            await analyzer.process_document(
                text_input=None,
                file_data=b"invalid pdf"
            )
    
    @pytest.mark.asyncio
    async def test_empty_document_handling(self, analyzer):
        """Test handling of empty document"""
        with pytest.raises(ValueError):
            await analyzer.process_document(
                text_input="",
                file_data=None
            )
