"""Evaluator page for Streamlit UI"""
import streamlit as st
import requests
import json

def check_api_config():
    """Check if API is configured"""
    if not st.session_state.get('api_key') or not st.session_state.get('api_base_url'):
        st.error("⚠️ Please configure your API key in the sidebar first!")
        return False
    return True

def evaluate_proposal(
    api_base_url: str,
    api_key: str,
    user_id: str,
    proposal_text: str = None,
    proposal_file: bytes = None,
    tor_text: str = None,
    tor_file: bytes = None,
    organization_id: str = None,
    org_guideline_id: str = None
):
    """Call the evaluator API"""
    try:
        files = {}
        data = {"user_id": user_id}
        
        if proposal_text:
            data["proposal_text_input"] = proposal_text
        if proposal_file:
            files["proposal_pdf_file"] = ("proposal.pdf", proposal_file, "application/pdf")
        
        if tor_text:
            data["tor_text_input"] = tor_text
        if tor_file:
            files["tor_pdf_file"] = ("tor.pdf", tor_file, "application/pdf")
        
        if organization_id:
            data["organization_id"] = organization_id
        if org_guideline_id:
            data["org_guideline_id"] = org_guideline_id
        
        response = requests.post(
            f"{api_base_url}/evaluator/evaluate",
            headers={"X-API-Key": api_key},
            data=data,
            files=files if files else None,
            timeout=180
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return None, f"Request failed: {str(e)}"

def render():
    """Render the Evaluator page"""
    st.markdown('<div class="main-header">📋 Proposal Evaluator</div>', unsafe_allow_html=True)
    
    if not check_api_config():
        return
    
    st.markdown("""
    Evaluate proposals against Terms of Reference (ToR) and organizational guidelines 
    with comprehensive three-part analysis.
    """)
    
    # Configuration
    with st.expander("⚙️ Evaluation Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            organization_id = st.text_input(
                "Organization ID (Optional)",
                help="Provide organization ID for custom guidelines"
            )
        
        with col2:
            org_guideline_id = st.text_input(
                "Guideline ID (Optional)",
                help="Specific guideline to use for evaluation"
            )
    
    # Proposal input
    st.markdown("### 📄 Proposal Document")
    proposal_method = st.radio(
        "Input Method",
        ["📝 Text", "📄 File Upload"],
        key="proposal_method",
        horizontal=True
    )
    
    proposal_text = None
    proposal_file = None
    
    if proposal_method == "📝 Text":
        proposal_text = st.text_area(
            "Proposal Text",
            height=200,
            placeholder="Paste your proposal text here...",
            key="proposal_text"
        )
    else:
        uploaded_proposal = st.file_uploader(
            "Upload Proposal",
            type=["pdf"],
            key="proposal_file"
        )
        if uploaded_proposal:
            proposal_file = uploaded_proposal.read()
            st.success(f"✅ Proposal uploaded: {uploaded_proposal.name}")
    
    st.markdown("---")
    
    # ToR input
    st.markdown("### 📋 Terms of Reference (ToR)")
    tor_method = st.radio(
        "Input Method",
        ["📝 Text", "📄 File Upload"],
        key="tor_method",
        horizontal=True
    )
    
    tor_text = None
    tor_file = None
    
    if tor_method == "📝 Text":
        tor_text = st.text_area(
            "ToR Text",
            height=200,
            placeholder="Paste your ToR text here...",
            key="tor_text"
        )
    else:
        uploaded_tor = st.file_uploader(
            "Upload ToR",
            type=["pdf"],
            key="tor_file"
        )
        if uploaded_tor:
            tor_file = uploaded_tor.read()
            st.success(f"✅ ToR uploaded: {uploaded_tor.name}")
    
    st.markdown("---")
    
    # Evaluate button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        evaluate_btn = st.button("🚀 Evaluate", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.rerun()
    
    # Evaluation
    if evaluate_btn:
        if not (proposal_text or proposal_file):
            st.error("❌ Please provide proposal text or upload a file!")
            return
        if not (tor_text or tor_file):
            st.error("❌ Please provide ToR text or upload a file!")
            return
        
        with st.spinner("🔍 Evaluating proposal... This may take 1-2 minutes."):
            result, error = evaluate_proposal(
                api_base_url=st.session_state.api_base_url,
                api_key=st.session_state.api_key,
                user_id=st.session_state.user_id or "anonymous",
                proposal_text=proposal_text,
                proposal_file=proposal_file,
                tor_text=tor_text,
                tor_file=tor_file,
                organization_id=organization_id if organization_id else None,
                org_guideline_id=org_guideline_id if org_guideline_id else None
            )
        
        if error:
            st.error(f"❌ Evaluation failed: {error}")
        elif result:
            # Store result
            st.session_state['last_evaluation'] = result
            
            st.success("✅ Evaluation complete!")
            
            # Overall metrics
            st.markdown("---")
            st.markdown("### 📊 Overall Assessment")
            
            col1, col2, col3, col4 = st.columns(4)
            
            overall_score = result.get('overall_score', 0)
            internal_score = result.get('internal_analysis', {}).get('score', 0)
            external_score = result.get('external_analysis', {}).get('score', 0)
            delta_score = result.get('delta_analysis', {}).get('score', 0)
            
            with col1:
                st.metric("Overall Score", f"{overall_score:.1f}/100" if overall_score else "N/A")
            with col2:
                st.metric("Internal", f"{internal_score:.1f}" if internal_score else "N/A")
            with col3:
                st.metric("External", f"{external_score:.1f}" if external_score else "N/A")
            with col4:
                st.metric("Gap Analysis", f"{delta_score:.1f}" if delta_score else "N/A")
            
            # Progress bar for overall score
            if overall_score:
                st.progress(overall_score / 100)
            
            # Detailed analyses
            st.markdown("---")
            
            # P_Internal
            with st.expander("🔍 P_Internal: Internal Consistency Analysis", expanded=True):
                internal = result.get('internal_analysis', {})
                
                st.markdown(f"**Score:** {internal.get('score', 'N/A')}/100")
                st.markdown(f"**{internal.get('title', 'Internal Analysis')}**")
                
                st.markdown("#### Analysis")
                st.markdown(internal.get('content', 'No analysis available'))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if internal.get('strengths'):
                        st.markdown("#### ✅ Strengths")
                        for strength in internal['strengths']:
                            st.markdown(f"- {strength}")
                
                with col2:
                    if internal.get('gaps'):
                        st.markdown("#### ⚠️ Gaps")
                        for gap in internal['gaps']:
                            st.markdown(f"- {gap}")
                
                if internal.get('recommendations'):
                    st.markdown("#### 💡 Recommendations")
                    for rec in internal['recommendations']:
                        st.markdown(f"- {rec}")
            
            # P_External
            with st.expander("🎯 P_External: ToR Alignment Analysis", expanded=True):
                external = result.get('external_analysis', {})
                
                st.markdown(f"**Score:** {external.get('score', 'N/A')}/100")
                st.markdown(f"**{external.get('title', 'External Analysis')}**")
                
                st.markdown("#### Analysis")
                st.markdown(external.get('content', 'No analysis available'))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if external.get('strengths'):
                        st.markdown("#### ✅ Strengths")
                        for strength in external['strengths']:
                            st.markdown(f"- {strength}")
                
                with col2:
                    if external.get('gaps'):
                        st.markdown("#### ⚠️ Gaps")
                        for gap in external['gaps']:
                            st.markdown(f"- {gap}")
                
                if external.get('recommendations'):
                    st.markdown("#### 💡 Recommendations")
                    for rec in external['recommendations']:
                        st.markdown(f"- {rec}")
            
            # P_Delta
            with st.expander("📊 P_Delta: Gap Analysis", expanded=True):
                delta = result.get('delta_analysis', {})
                
                st.markdown(f"**Score:** {delta.get('score', 'N/A')}/100")
                st.markdown(f"**{delta.get('title', 'Gap Analysis')}**")
                
                st.markdown("#### Analysis")
                st.markdown(delta.get('content', 'No analysis available'))
                
                if delta.get('gaps'):
                    st.markdown("#### 🔴 Critical Gaps")
                    for gap in delta['gaps']:
                        st.markdown(f"- {gap}")
                
                if delta.get('recommendations'):
                    st.markdown("#### 💡 Recommendations")
                    for rec in delta['recommendations']:
                        st.markdown(f"- {rec}")
            
            # Download results
            st.markdown("---")
            st.markdown("### 💾 Export Results")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Full Report (JSON)",
                    data=json.dumps(result, indent=2),
                    file_name="evaluation_report.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # Create summary text
                summary_text = f"""
Proposal Evaluation Report
===========================

Overall Score: {overall_score:.1f}/100

Internal Analysis Score: {internal_score:.1f}/100
External Analysis Score: {external_score:.1f}/100
Gap Analysis Score: {delta_score:.1f}/100

Processing Time: {result.get('processing_time_seconds', 0):.2f}s
Session ID: {result.get('session_id', 'N/A')}

=== P_INTERNAL: INTERNAL CONSISTENCY ===
{internal.get('content', 'N/A')}

=== P_EXTERNAL: TOR ALIGNMENT ===
{external.get('content', 'N/A')}

=== P_DELTA: GAP ANALYSIS ===
{delta.get('content', 'N/A')}
"""
                st.download_button(
                    label="📥 Download Summary (TXT)",
                    data=summary_text,
                    file_name="evaluation_summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # Show last evaluation
    if st.session_state.get('last_evaluation'):
        with st.expander("📜 Last Evaluation Details", expanded=False):
            st.json(st.session_state['last_evaluation'])

