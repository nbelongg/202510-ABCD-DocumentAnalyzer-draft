"""End-to-end tests for complete user workflows"""
import pytest
from fastapi import status


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflows:
    """Test complete end-to-end workflows"""
    
    @pytest.mark.skip(reason="Requires full system setup")
    def test_complete_analysis_workflow(self, api_client, sample_document_text, clean_database):
        """Test complete document analysis workflow"""
        # Step 1: Analyze document
        analyze_payload = {
            "user_id": "e2e-user",
            "text_input": sample_document_text,
            "document_type": "Proposal",
            "prompt_labels": ["P1", "P2"]
        }
        
        analyze_response = api_client.post(
            "/api/v1/analyzer/analyze",
            data=analyze_payload
        )
        
        assert analyze_response.status_code == status.HTTP_200_OK
        session_data = analyze_response.json()
        session_id = session_data["session_id"]
        
        # Step 2: Ask follow-up question
        followup_payload = {
            "user_id": "e2e-user",
            "session_id": session_id,
            "query": "Can you elaborate on the technical approach?",
            "section": "P2"
        }
        
        followup_response = api_client.post(
            "/api/v1/analyzer/followup",
            json=followup_payload
        )
        
        assert followup_response.status_code == status.HTTP_200_OK
        
        # Step 3: Submit feedback
        feedback_payload = {
            "session_id": session_id,
            "section": "P1",
            "feedback": True,
            "feedback_note": "Very thorough analysis"
        }
        
        feedback_response = api_client.post(
            "/api/v1/analyzer/feedback",
            json=feedback_payload
        )
        
        assert feedback_response.status_code in [200, 201]
        
        # Step 4: Retrieve session
        get_response = api_client.get(f"/api/v1/analyzer/sessions/{session_id}")
        
        assert get_response.status_code == status.HTTP_200_OK
        retrieved_session = get_response.json()
        assert retrieved_session["session_id"] == session_id
    
    @pytest.mark.skip(reason="Requires full system setup")
    def test_complete_chat_workflow(self, api_client, clean_database):
        """Test complete chat workflow"""
        user_id = "e2e-chat-user"
        
        # Step 1: First chat message
        chat1_payload = {
            "user_id": user_id,
            "query": "What is the project about?",
            "source": "web"
        }
        
        chat1_response = api_client.post("/api/v1/chatbot/chat", json=chat1_payload)
        assert chat1_response.status_code == status.HTTP_200_OK
        
        chat1_data = chat1_response.json()
        session_id = chat1_data["session_id"]
        
        # Step 2: Follow-up in same session
        chat2_payload = {
            "user_id": user_id,
            "session_id": session_id,
            "query": "What is the budget?",
            "source": "web"
        }
        
        chat2_response = api_client.post("/api/v1/chatbot/chat", json=chat2_payload)
        assert chat2_response.status_code == status.HTTP_200_OK
        
        # Step 3: Get session history
        history_response = api_client.get(f"/api/v1/chatbot/sessions/{session_id}")
        assert history_response.status_code == status.HTTP_200_OK
        
        history = history_response.json()
        assert len(history["messages"]) >= 4  # 2 user + 2 assistant
        
        # Step 4: Submit feedback
        feedback_payload = {
            "session_id": session_id,
            "feedback": "positive",
            "comment": "Very helpful"
        }
        
        feedback_response = api_client.post(
            "/api/v1/chatbot/feedback",
            json=feedback_payload
        )
        
        assert feedback_response.status_code in [200, 201]
    
    @pytest.mark.skip(reason="Requires full system setup")
    def test_complete_evaluation_workflow(self, api_client, sample_document_text, sample_tor_text, clean_database):
        """Test complete proposal evaluation workflow"""
        # Step 1: Evaluate proposal
        eval_payload = {
            "user_id": "e2e-eval-user",
            "proposal_text_input": sample_document_text,
            "tor_text_input": sample_tor_text,
            "organization_id": "test-org"
        }
        
        eval_response = api_client.post(
            "/api/v1/evaluator/evaluate",
            data=eval_payload
        )
        
        assert eval_response.status_code == status.HTTP_200_OK
        eval_data = eval_response.json()
        session_id = eval_data["session_id"]
        
        # Verify three-part analysis
        assert "internal_analysis" in eval_data
        assert "external_analysis" in eval_data
        assert "delta_analysis" in eval_data
        assert "overall_score" in eval_data
        
        # Step 2: Ask follow-up
        followup_payload = {
            "user_id": "e2e-eval-user",
            "session_id": session_id,
            "query": "What are the main gaps?",
            "section": "P_Delta"
        }
        
        followup_response = api_client.post(
            "/api/v1/evaluator/followup",
            json=followup_payload
        )
        
        assert followup_response.status_code == status.HTTP_200_OK
        
        # Step 3: Submit feedback
        feedback_payload = {
            "session_id": session_id,
            "section": "P_Internal",
            "feedback": True,
            "feedback_note": "Comprehensive evaluation"
        }
        
        feedback_response = api_client.post(
            "/api/v1/evaluator/feedback",
            json=feedback_payload
        )
        
        assert feedback_response.status_code in [200, 201]
