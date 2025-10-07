"""Document Analyzer page for Streamlit UI"""
import streamlit as st
import requests
from typing import Optional
import json

def check_api_config():
    """Check if API is configured"""
    if not st.session_state.get('api_key') or not st.session_state.get('api_base_url'):
        st.error("⚠️ Please configure your API key in the sidebar first!")
        return False
    return True

def analyze_document(
    api_base_url: str,
    api_key: str,
    user_id: str,
    document_text: Optional[str] = None,
    document_file: Optional[bytes] = None,
    document_type: str = "Proposal",
    organization_id: Optional[str] = None
):
    """Call the analyzer API"""
    try:
        # Prepare form data
        files = {}
        data = {
            "user_id": user_id,
            "document_type": document_type
        }
        
        if organization_id:
            data["organization_id"] = organization_id
        
        if document_text:
            data["document_text"] = document_text
        
        if document_file:
            files["document_file"] = ("document.pdf", document_file, "application/pdf")
        
        # Make API call
        response = requests.post(
            f"{api_base_url}/analyzer/analyze",
            headers={"X-API-Key": api_key},
            data=data,
            files=files if files else None,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return None, f"Request failed: {str(e)}"

def render():
    """Render the Analyzer page"""
    st.markdown('<div class="main-header">📊 Document Analyzer</div>', unsafe_allow_html=True)
    
    if not check_api_config():
        return
    
    st.markdown("""
    Upload or paste your document for AI-powered analysis and insights extraction.
    """)
    
    # Configuration section
    with st.expander("⚙️ Analysis Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            document_type = st.selectbox(
                "Document Type",
                ["Proposal", "Report", "Research Paper", "Contract", "Other"],
                help="Select the type of document for context-aware analysis"
            )
        
        with col2:
            organization_id = st.text_input(
                "Organization ID (Optional)",
                help="Provide organization ID for custom prompts"
            )
    
    # Input method selection
    input_method = st.radio(
        "Input Method",
        ["📝 Text Input", "📄 File Upload"],
        horizontal=True
    )
    
    document_text = None
    document_file = None
    
    if input_method == "📝 Text Input":
        document_text = st.text_area(
            "Document Text",
            height=300,
            placeholder="Paste your document text here...",
            help="Enter the full text of your document"
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=["pdf", "txt", "docx"],
            help="Upload a PDF, TXT, or DOCX file"
        )
        if uploaded_file:
            document_file = uploaded_file.read()
            st.success(f"✅ File uploaded: {uploaded_file.name} ({len(document_file)} bytes)")
    
    # Analyze button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        analyze_btn = st.button("🚀 Analyze Document", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.rerun()
    
    # Analysis
    if analyze_btn:
        if not document_text and not document_file:
            st.error("❌ Please provide document text or upload a file!")
            return
        
        with st.spinner("🔍 Analyzing document... This may take a minute."):
            result, error = analyze_document(
                api_base_url=st.session_state.api_base_url,
                api_key=st.session_state.api_key,
                user_id=st.session_state.user_id or "anonymous",
                document_text=document_text,
                document_file=document_file,
                document_type=document_type,
                organization_id=organization_id if organization_id else None
            )
        
        if error:
            st.error(f"❌ Analysis failed: {error}")
        elif result:
            # Store result in session state
            st.session_state['last_analysis'] = result
            
            # Display results
            st.success("✅ Analysis complete!")
            
            # Session info
            st.markdown("---")
            st.markdown("### 📋 Analysis Details")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Session ID", result.get('session_id', 'N/A')[:12] + "...")
            with col2:
                st.metric("Document Type", document_type)
            with col3:
                st.metric("Processing Time", f"{result.get('processing_time_seconds', 0):.2f}s")
            
            # Analysis results
            st.markdown("---")
            st.markdown("### 📊 Analysis Results")
            
            # Main analysis content
            if result.get('analysis'):
                st.markdown(result['analysis'])
            
            # Key insights
            if result.get('insights'):
                st.markdown("### 💡 Key Insights")
                for idx, insight in enumerate(result['insights'], 1):
                    st.markdown(f"{idx}. {insight}")
            
            # Recommendations
            if result.get('recommendations'):
                st.markdown("### 🎯 Recommendations")
                for idx, rec in enumerate(result['recommendations'], 1):
                    st.markdown(f"{idx}. {rec}")
            
            # Download options
            st.markdown("---")
            st.markdown("### 💾 Export Results")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download as JSON",
                    data=json.dumps(result, indent=2),
                    file_name="analysis_results.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col2:
                # Create text version
                text_output = f"""
Document Analysis Report
========================

Session ID: {result.get('session_id', 'N/A')}
Document Type: {document_type}
Processing Time: {result.get('processing_time_seconds', 0):.2f}s

Analysis:
{result.get('analysis', 'N/A')}

Key Insights:
{chr(10).join([f"{i}. {insight}" for i, insight in enumerate(result.get('insights', []), 1)])}

Recommendations:
{chr(10).join([f"{i}. {rec}" for i, rec in enumerate(result.get('recommendations', []), 1)])}
"""
                st.download_button(
                    label="📥 Download as Text",
                    data=text_output,
                    file_name="analysis_results.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # Show history
    if st.session_state.get('last_analysis'):
        with st.expander("📜 Last Analysis", expanded=False):
            st.json(st.session_state['last_analysis'])

