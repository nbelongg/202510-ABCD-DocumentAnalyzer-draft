"""Chatbot page for Streamlit UI"""
import streamlit as st
import requests
from datetime import datetime

def check_api_config():
    """Check if API is configured"""
    if not st.session_state.get('api_key') or not st.session_state.get('api_base_url'):
        st.error("⚠️ Please configure your API key in the sidebar first!")
        return False
    return True

def send_chat_message(api_base_url: str, api_key: str, user_id: str, question: str, session_id: str = None):
    """Send chat message to API"""
    try:
        payload = {
            "user_id": user_id,
            "question": question,
            "model": "gpt-4o"
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        response = requests.post(
            f"{api_base_url}/chatbot/chat",
            headers={"X-API-Key": api_key},
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return None, f"Request failed: {str(e)}"

def get_sessions(api_base_url: str, api_key: str, user_id: str):
    """Get user's chat sessions"""
    try:
        response = requests.get(
            f"{api_base_url}/chatbot/sessions",
            headers={"X-API-Key": api_key},
            params={"user_id": user_id, "limit": 20},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('sessions', []), None
        else:
            return [], f"Failed to load sessions: {response.status_code}"
            
    except Exception as e:
        return [], f"Request failed: {str(e)}"

def render():
    """Render the Chatbot page"""
    st.markdown('<div class="main-header">💬 AI Chatbot</div>', unsafe_allow_html=True)
    
    if not check_api_config():
        return
    
    st.markdown("""
    Ask questions and get AI-powered answers from our knowledge base.
    """)
    
    # Initialize chat history in session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    
    # Sidebar for sessions
    with st.sidebar:
        st.markdown("### 💬 Chat Sessions")
        
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.current_session_id = None
            st.success("Started new chat!")
            st.rerun()
        
        st.markdown("---")
        
        # Load sessions
        if st.session_state.get('user_id'):
            sessions, error = get_sessions(
                st.session_state.api_base_url,
                st.session_state.api_key,
                st.session_state.user_id
            )
            
            if sessions:
                st.markdown("**Recent Sessions:**")
                for session in sessions[:10]:
                    session_id = session.get('session_id', '')
                    created_at = session.get('created_at', '')
                    msg_count = session.get('message_count', 0)
                    
                    if st.button(
                        f"📅 {session_id[:8]}... ({msg_count} msgs)",
                        key=f"session_{session_id}",
                        use_container_width=True
                    ):
                        st.session_state.current_session_id = session_id
                        st.info(f"Switched to session {session_id[:12]}...")
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.current_session_id:
            st.info(f"📍 Session: {st.session_state.current_session_id[:12]}...")
        else:
            st.info("📍 New Chat Session")
    
    with col2:
        model_choice = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
            label_visibility="collapsed"
        )
    
    # Chat container
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.chat_messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.markdown(content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)
                    
                    # Show sources if available
                    if message.get('sources'):
                        with st.expander("📚 Sources"):
                            for idx, source in enumerate(message['sources'], 1):
                                st.markdown(f"**{idx}. {source.get('title', 'Unknown')}**")
                                if source.get('author_organization'):
                                    st.caption(f"By: {source['author_organization']}")
                                if source.get('link'):
                                    st.markdown(f"[🔗 Link]({source['link']})")
                                st.markdown("---")
                    
                    # Feedback buttons
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button("👍", key=f"like_{message.get('response_id', '')}"):
                            st.success("Thanks for your feedback!")
                        if st.button("👎", key=f"dislike_{message.get('response_id', '')}"):
                            st.info("Feedback noted. We'll improve!")
    
    # Chat input
    st.markdown("---")
    question = st.text_input(
        "Ask a question:",
        placeholder="Type your question here...",
        key="chat_input",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        send_btn = st.button("📤 Send", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.current_session_id = None
            st.rerun()
    
    # Send message
    if send_btn and question:
        # Add user message to chat
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': question
        })
        
        # Call API
        with st.spinner("🤔 Thinking..."):
            result, error = send_chat_message(
                api_base_url=st.session_state.api_base_url,
                api_key=st.session_state.api_key,
                user_id=st.session_state.user_id or "anonymous",
                question=question,
                session_id=st.session_state.current_session_id
            )
        
        if error:
            st.error(f"❌ {error}")
        elif result:
            # Update session ID if new
            if not st.session_state.current_session_id:
                st.session_state.current_session_id = result.get('session_id')
            
            # Add assistant response to chat
            st.session_state.chat_messages.append({
                'role': 'assistant',
                'content': result.get('response', ''),
                'response_id': result.get('response_id'),
                'sources': result.get('sources', []),
                'within_knowledge_base': result.get('within_knowledge_base', True)
            })
            
            # Rerun to update chat
            st.rerun()
    
    # Quick questions
    st.markdown("---")
    st.markdown("### 💡 Quick Questions")
    
    quick_questions = [
        "What is impact evaluation?",
        "How do I design a theory of change?",
        "What are RCT best practices?",
        "Tell me about M&E frameworks"
    ]
    
    cols = st.columns(4)
    for idx, qq in enumerate(quick_questions):
        with cols[idx]:
            if st.button(qq, key=f"qq_{idx}", use_container_width=True):
                # Add to chat and send
                st.session_state.chat_messages.append({
                    'role': 'user',
                    'content': qq
                })
                
                with st.spinner("🤔 Thinking..."):
                    result, error = send_chat_message(
                        api_base_url=st.session_state.api_base_url,
                        api_key=st.session_state.api_key,
                        user_id=st.session_state.user_id or "anonymous",
                        question=qq,
                        session_id=st.session_state.current_session_id
                    )
                
                if result:
                    if not st.session_state.current_session_id:
                        st.session_state.current_session_id = result.get('session_id')
                    
                    st.session_state.chat_messages.append({
                        'role': 'assistant',
                        'content': result.get('response', ''),
                        'response_id': result.get('response_id'),
                        'sources': result.get('sources', [])
                    })
                    
                    st.rerun()

