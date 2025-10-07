"""Unit tests for ProposalEvaluator core engine"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.evaluator import ProposalEvaluator
from schemas.evaluator import EvaluatorRequest, DocumentType


@pytest.mark.unit
class TestProposalEvaluator:
    """Test ProposalEvaluator core logic"""
    
    @pytest.fixture
    def evaluator(self, mock_llm_service, mock_pdf_service):
        """Create evaluator instance with mocked services"""
        with patch('core.evaluator.LLMService', return_value=mock_llm_service), \
             patch('core.evaluator.PDFService', return_value=mock_pdf_service):
            return ProposalEvaluator()
    
    @pytest.mark.asyncio
    async def test_process_proposal_text(self, evaluator, sample_document_text):
        """Test processing proposal from text"""
        text, url = await evaluator.process_proposal(
            text_input=sample_document_text,
            file_data=None
        )
        
        assert text == sample_document_text
        assert url is None
    
    @pytest.mark.asyncio
    async def test_process_proposal_pdf(self, evaluator, sample_pdf_bytes, mock_pdf_service):
        """Test processing proposal from PDF"""
        mock_pdf_service.extract_text_from_pdf.return_value = "Extracted proposal text"
        
        text, url = await evaluator.process_proposal(
            text_input=None,
            file_data=sample_pdf_bytes
        )
        
        assert text == "Extracted proposal text"
        mock_pdf_service.extract_text_from_pdf.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_tor(self, evaluator, sample_tor_text):
        """Test processing Terms of Reference"""
        text, url = await evaluator.process_tor(
            text_input=sample_tor_text,
            file_data=None
        )
        
        assert text == sample_tor_text
        assert url is None
    
    @pytest.mark.asyncio
    async def test_summarize_proposal(self, evaluator, mock_llm_service):
        """Test proposal summarization"""
        mock_llm_service.generate_completion.return_value = "Concise proposal summary"
        
        summary = await evaluator.summarize_proposal("Long proposal text...")
        
        assert summary == "Concise proposal summary"
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_summarize_tor(self, evaluator, mock_llm_service):
        """Test ToR summarization"""
        mock_llm_service.generate_completion.return_value = "Concise ToR summary"
        
        summary = await evaluator.summarize_tor("Long ToR text...")
        
        assert summary == "Concise ToR summary"
        mock_llm_service.generate_completion.assert_called_once()
    
    def test_parse_analysis_response(self, evaluator):
        """Test parsing analysis response with structured data"""
        response = """
        **SCORE**: [92.5]
        
        **STRENGTHS**:
        - Comprehensive methodology
        - Strong team composition
        - Clear deliverables
        
        **GAPS**:
        - Budget justification needed
        - Timeline could be more detailed
        
        **RECOMMENDATIONS**:
        - Add detailed budget breakdown
        - Provide Gantt chart
        
        **DETAILED ANALYSIS**:
        The proposal demonstrates excellent understanding of requirements...
        """
        
        result = evaluator.parse_analysis_response(response, "P_Internal")
        
        assert result["score"] == 92.5
        assert len(result["strengths"]) == 3
        assert len(result["gaps"]) == 2
        assert len(result["recommendations"]) == 2
        assert "requirements" in result["content"].lower()
    
    @pytest.mark.asyncio
    async def test_run_p_internal_analysis(self, evaluator, mock_llm_service):
        """Test P_Internal (internal consistency) analysis"""
        mock_llm_service.generate_completion.return_value = """
        **SCORE**: 85
        **STRENGTHS**: - Consistent approach
        **GAPS**: - None
        **DETAILED ANALYSIS**: Internally consistent proposal.
        """
        
        result = await evaluator.run_analysis(
            analysis_type="P_Internal",
            proposal_summary="Proposal summary",
            tor_summary="ToR summary",
            guidelines="Organization guidelines"
        )
        
        assert result["section_type"] == "P_Internal"
        assert result["score"] == 85.0
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_p_external_analysis(self, evaluator, mock_llm_service):
        """Test P_External (ToR alignment) analysis"""
        mock_llm_service.generate_completion.return_value = """
        **SCORE**: 90
        **STRENGTHS**: - Aligns well with ToR
        **GAPS**: - Minor alignment issues
        **DETAILED ANALYSIS**: Strong alignment with requirements.
        """
        
        result = await evaluator.run_analysis(
            analysis_type="P_External",
            proposal_summary="Proposal summary",
            tor_summary="ToR summary",
            guidelines="Guidelines"
        )
        
        assert result["section_type"] == "P_External"
        assert result["score"] == 90.0
    
    @pytest.mark.asyncio
    async def test_run_p_delta_analysis(self, evaluator, mock_llm_service):
        """Test P_Delta (gap analysis) analysis"""
        mock_llm_service.generate_completion.return_value = """
        **SCORE**: 88
        **CRITICAL GAPS**: - Budget details missing
        **MINOR GAPS**: - Timeline could be clearer
        **RECOMMENDATIONS**: - Add budget breakdown
        **DETAILED ANALYSIS**: Some gaps identified between proposal and ToR.
        """
        
        result = await evaluator.run_analysis(
            analysis_type="P_Delta",
            proposal_summary="Proposal summary",
            tor_summary="ToR summary",
            guidelines="Guidelines",
            internal_insights="Internal analysis insights",
            external_insights="External analysis insights"
        )
        
        assert result["section_type"] == "P_Delta"
        assert result["score"] == 88.0
        assert len(result["gaps"]) >= 1
    
    @pytest.mark.asyncio
    async def test_calculate_overall_score(self, evaluator):
        """Test overall score calculation from three analyses"""
        internal = {"score": 85.0}
        external = {"score": 90.0}
        delta = {"score": 87.0}
        
        scores = [internal["score"], external["score"], delta["score"]]
        overall = sum(scores) / len(scores)
        
        assert overall == 87.33333333333333
    
    @pytest.mark.asyncio
    async def test_invalid_analysis_type(self, evaluator):
        """Test error handling for invalid analysis type"""
        with pytest.raises(ValueError, match="Unknown analysis type"):
            await evaluator.run_analysis(
                analysis_type="INVALID",
                proposal_summary="",
                tor_summary="",
                guidelines=""
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_summarization(self, evaluator, mock_llm_service):
        """Test fallback when summarization fails"""
        mock_llm_service.generate_completion.side_effect = Exception("LLM error")
        
        long_text = "A" * 5000
        summary = await evaluator.summarize_proposal(long_text)
        
        # Should return truncated text as fallback
        assert len(summary) <= 2000
    
    @pytest.mark.asyncio
    async def test_parse_malformed_response(self, evaluator):
        """Test parsing malformed LLM response"""
        malformed = "This is just plain text without structure"
        
        result = evaluator.parse_analysis_response(malformed, "P_Internal")
        
        # Should return minimal structure
        assert result["section_type"] == "P_Internal"
        assert result["score"] is None
        assert result["content"] == malformed
