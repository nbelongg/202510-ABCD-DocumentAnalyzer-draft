"""Main Streamlit application for Document Analyzer"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import pages
from streamlit.pages import analyzer_page, chatbot_page, evaluator_page, admin_page

# Page configuration
st.set_page_config(
    page_title="Document Analyzer Platform",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin-bottom: 1rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Sidebar
with st.sidebar:
    st.markdown('<div class="main-header">📄 Document Analyzer</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # API Configuration
    with st.expander("⚙️ API Configuration", expanded=not st.session_state.api_key):
        api_key = st.text_input(
            "API Key",
            value=st.session_state.api_key,
            type="password",
            help="Enter your API key to access the services"
        )
        
        user_id = st.text_input(
            "User ID",
            value=st.session_state.user_id,
            help="Enter your user ID"
        )
        
        api_base_url = st.text_input(
            "API Base URL",
            value="http://localhost:8000/api/v1",
            help="Base URL for API endpoints"
        )
        
        if st.button("💾 Save Configuration"):
            st.session_state.api_key = api_key
            st.session_state.user_id = user_id
            st.session_state.api_base_url = api_base_url
            st.success("✅ Configuration saved!")
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### 🧭 Navigation")
    
    pages = {
        "🏠 Home": "Home",
        "📊 Analyzer": "Analyzer",
        "💬 Chatbot": "Chatbot",
        "📋 Evaluator": "Evaluator",
        "⚙️ Admin": "Admin"
    }
    
    for label, page in pages.items():
        if st.button(label, key=f"nav_{page}"):
            st.session_state.current_page = page
            st.rerun()
    
    st.markdown("---")
    
    # Status
    st.markdown("### 📊 Status")
    if st.session_state.api_key:
        st.success("✅ Configured")
    else:
        st.warning("⚠️ No API Key")
    
    st.markdown("---")
    
    # Info
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Version:** 1.0.0  
    **Environment:** Production  
    
    This platform provides:
    - Document Analysis
    - AI Chatbot
    - Proposal Evaluation
    - System Administration
    """)

# Main content area
if st.session_state.current_page == "Home":
    st.markdown('<div class="main-header">Welcome to Document Analyzer Platform</div>', unsafe_allow_html=True)
    
    st.markdown("""
    A comprehensive platform for document analysis, AI-powered chatbot assistance, 
    and proposal evaluation with organizational guidelines support.
    """)
    
    # Features grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h2>📊</h2>
            <h3>Analyzer</h3>
            <p>Document analysis and insights extraction</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h2>💬</h2>
            <h3>Chatbot</h3>
            <p>AI-powered Q&A with knowledge base</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h2>📋</h2>
            <h3>Evaluator</h3>
            <p>Proposal evaluation against ToR & guidelines</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h2>⚙️</h2>
            <h3>Admin</h3>
            <p>System configuration and management</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Start
    st.markdown('<div class="sub-header">🚀 Quick Start</div>', unsafe_allow_html=True)
    
    st.markdown("""
    1. **Configure API Key**: Enter your API key in the sidebar
    2. **Choose a Service**: Select from Analyzer, Chatbot, or Evaluator
    3. **Upload Documents**: Provide text or upload files
    4. **Get Results**: Receive AI-powered analysis and insights
    """)
    
    # Recent Activity (placeholder)
    st.markdown('<div class="sub-header">📈 System Overview</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Sessions", "156", delta="12")
    
    with col2:
        st.metric("Documents Analyzed", "89", delta="5")
    
    with col3:
        st.metric("Evaluations", "34", delta="3")

elif st.session_state.current_page == "Analyzer":
    analyzer_page.render()

elif st.session_state.current_page == "Chatbot":
    chatbot_page.render()

elif st.session_state.current_page == "Evaluator":
    evaluator_page.render()

elif st.session_state.current_page == "Admin":
    admin_page.render()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    Document Analyzer Platform v1.0.0 | © 2025 | Built with Streamlit & FastAPI
</div>
""", unsafe_allow_html=True)

