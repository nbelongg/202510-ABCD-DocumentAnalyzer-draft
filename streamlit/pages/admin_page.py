"""Admin page for Streamlit UI"""
import streamlit as st
import requests
import json

def check_api_config():
    """Check if API is configured"""
    if not st.session_state.get('api_key') or not st.session_state.get('api_base_url'):
        st.error("⚠️ Please configure your API key in the sidebar first!")
        return False
    return True

def render():
    """Render the Admin page"""
    st.markdown('<div class="main-header">⚙️ System Administration</div>', unsafe_allow_html=True)
    
    if not check_api_config():
        return
    
    st.markdown("""
    Manage prompts, organizations, guidelines, users, and API keys.
    """)
    
    # Admin tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Prompts",
        "🏢 Organizations",
        "📋 Guidelines",
        "👥 Users",
        "🔑 API Keys"
    ])
    
    # TAB 1: PROMPTS
    with tab1:
        st.markdown("### 📝 Prompt Management")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("Create, view, and manage system prompts")
        with col2:
            if st.button("➕ Create New Prompt", use_container_width=True):
                st.session_state['show_create_prompt'] = True
        
        # Create prompt form
        if st.session_state.get('show_create_prompt'):
            with st.form("create_prompt_form"):
                st.markdown("#### Create New Prompt")
                
                prompt_type = st.selectbox(
                    "Prompt Type",
                    ["analyzer", "evaluator", "chatbot", "summary", "custom"]
                )
                
                prompt_name = st.text_input("Prompt Name", placeholder="e.g., detailed_evaluation_v2")
                prompt_text = st.text_area("Prompt Text", height=200, placeholder="Enter prompt template...")
                description = st.text_area("Description", height=100, placeholder="Brief description...")
                version = st.text_input("Version", value="1.0")
                is_active = st.checkbox("Active", value=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Create", type="primary", use_container_width=True):
                        try:
                            response = requests.post(
                                f"{st.session_state.api_base_url}/admin/prompts",
                                headers={"X-API-Key": st.session_state.api_key},
                                json={
                                    "prompt_type": prompt_type,
                                    "prompt_name": prompt_name,
                                    "prompt_text": prompt_text,
                                    "description": description,
                                    "version": version,
                                    "is_active": is_active
                                }
                            )
                            if response.status_code == 201:
                                st.success("✅ Prompt created successfully!")
                                st.session_state['show_create_prompt'] = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                with col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state['show_create_prompt'] = False
                        st.rerun()
        
        # List prompts
        st.markdown("---")
        st.markdown("#### Existing Prompts")
        
        try:
            response = requests.get(
                f"{st.session_state.api_base_url}/admin/prompts",
                headers={"X-API-Key": st.session_state.api_key},
                params={"limit": 50}
            )
            
            if response.status_code == 200:
                data = response.json()
                prompts = data.get('prompts', [])
                
                if prompts:
                    for prompt in prompts:
                        with st.expander(f"📝 {prompt['prompt_name']} (v{prompt['version']})"):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.markdown(f"**Type:** {prompt['prompt_type']}")
                                st.markdown(f"**ID:** `{prompt['prompt_id']}`")
                            with col2:
                                st.markdown(f"**Active:** {'✅ Yes' if prompt['is_active'] else '❌ No'}")
                            with col3:
                                if st.button("🗑️ Delete", key=f"del_prompt_{prompt['prompt_id']}"):
                                    requests.delete(
                                        f"{st.session_state.api_base_url}/admin/prompts/{prompt['prompt_id']}",
                                        headers={"X-API-Key": st.session_state.api_key}
                                    )
                                    st.success("Deleted!")
                                    st.rerun()
                            
                            st.markdown("**Description:**")
                            st.text(prompt.get('description', 'N/A'))
                            
                            st.markdown("**Prompt Text:**")
                            st.code(prompt['prompt_text'][:500] + "..." if len(prompt['prompt_text']) > 500 else prompt['prompt_text'])
                else:
                    st.info("No prompts found")
            else:
                st.error(f"Failed to load prompts: {response.status_code}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # TAB 2: ORGANIZATIONS
    with tab2:
        st.markdown("### 🏢 Organization Management")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("Manage organizations and their settings")
        with col2:
            if st.button("➕ Create Organization", use_container_width=True):
                st.session_state['show_create_org'] = True
        
        # Create organization form
        if st.session_state.get('show_create_org'):
            with st.form("create_org_form"):
                st.markdown("#### Create New Organization")
                
                org_id = st.text_input("Organization ID", placeholder="e.g., org-unicef")
                org_name = st.text_input("Organization Name", placeholder="e.g., UNICEF")
                description = st.text_area("Description", height=100)
                is_active = st.checkbox("Active", value=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Create", type="primary", use_container_width=True):
                        try:
                            response = requests.post(
                                f"{st.session_state.api_base_url}/admin/organizations",
                                headers={"X-API-Key": st.session_state.api_key},
                                json={
                                    "organization_id": org_id,
                                    "organization_name": org_name,
                                    "description": description,
                                    "is_active": is_active
                                }
                            )
                            if response.status_code == 201:
                                st.success("✅ Organization created!")
                                st.session_state['show_create_org'] = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                with col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state['show_create_org'] = False
                        st.rerun()
        
        # List organizations
        st.markdown("---")
        st.markdown("#### Existing Organizations")
        
        try:
            response = requests.get(
                f"{st.session_state.api_base_url}/admin/organizations",
                headers={"X-API-Key": st.session_state.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                orgs = data.get('organizations', [])
                
                if orgs:
                    for org in orgs:
                        with st.expander(f"🏢 {org['organization_name']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**ID:** `{org['organization_id']}`")
                                st.markdown(f"**Active:** {'✅ Yes' if org['is_active'] else '❌ No'}")
                            with col2:
                                st.markdown(f"**Guidelines:** {org.get('guidelines_count', 0)}")
                                if st.button("🗑️ Delete", key=f"del_org_{org['organization_id']}"):
                                    requests.delete(
                                        f"{st.session_state.api_base_url}/admin/organizations/{org['organization_id']}",
                                        headers={"X-API-Key": st.session_state.api_key}
                                    )
                                    st.success("Deleted!")
                                    st.rerun()
                            
                            st.markdown("**Description:**")
                            st.text(org.get('description', 'N/A'))
                else:
                    st.info("No organizations found")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # TAB 3: GUIDELINES
    with tab3:
        st.markdown("### 📋 Guidelines Management")
        
        st.markdown("Manage organization-specific evaluation guidelines")
        
        # Select organization
        org_id_for_guidelines = st.text_input(
            "Organization ID",
            placeholder="Enter organization ID to view guidelines",
            key="guideline_org_id"
        )
        
        if org_id_for_guidelines:
            try:
                response = requests.get(
                    f"{st.session_state.api_base_url}/admin/organizations/{org_id_for_guidelines}/guidelines",
                    headers={"X-API-Key": st.session_state.api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    guidelines = data.get('guidelines', [])
                    
                    st.success(f"Found {len(guidelines)} guidelines")
                    
                    for guideline in guidelines:
                        with st.expander(f"📋 {guideline['guideline_name']}"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**ID:** `{guideline['guideline_id']}`")
                                st.markdown(f"**Active:** {'✅ Yes' if guideline['is_active'] else '❌ No'}")
                            with col2:
                                if st.button("🗑️ Delete", key=f"del_guide_{guideline['guideline_id']}"):
                                    requests.delete(
                                        f"{st.session_state.api_base_url}/admin/guidelines/{guideline['guideline_id']}",
                                        headers={"X-API-Key": st.session_state.api_key}
                                    )
                                    st.success("Deleted!")
                                    st.rerun()
                            
                            st.markdown("**Description:**")
                            st.text(guideline.get('description', 'N/A'))
                            
                            st.markdown("**Guideline Text:**")
                            st.text_area(
                                "Text",
                                value=guideline['guideline_text'],
                                height=200,
                                disabled=True,
                                key=f"text_{guideline['guideline_id']}"
                            )
                else:
                    st.error(f"Failed to load guidelines: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # TAB 4: USERS
    with tab4:
        st.markdown("### 👥 User Management")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("Manage system users")
        with col2:
            if st.button("➕ Create User", use_container_width=True):
                st.session_state['show_create_user'] = True
        
        # Create user form
        if st.session_state.get('show_create_user'):
            with st.form("create_user_form"):
                st.markdown("#### Create New User")
                
                user_id = st.text_input("User ID", placeholder="e.g., user-john")
                user_name = st.text_input("User Name", placeholder="e.g., John Doe")
                user_email = st.text_input("Email", placeholder="e.g., john@example.com")
                org_id = st.text_input("Organization ID (Optional)")
                role = st.selectbox("Role", ["user", "admin", "analyst", "reviewer"])
                is_active = st.checkbox("Active", value=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Create", type="primary", use_container_width=True):
                        try:
                            response = requests.post(
                                f"{st.session_state.api_base_url}/admin/users",
                                headers={"X-API-Key": st.session_state.api_key},
                                json={
                                    "user_id": user_id,
                                    "user_name": user_name,
                                    "user_email": user_email,
                                    "organization_id": org_id if org_id else None,
                                    "role": role,
                                    "is_active": is_active
                                }
                            )
                            if response.status_code == 201:
                                st.success("✅ User created!")
                                st.session_state['show_create_user'] = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                with col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state['show_create_user'] = False
                        st.rerun()
        
        # List users
        st.markdown("---")
        st.markdown("#### Existing Users")
        
        try:
            response = requests.get(
                f"{st.session_state.api_base_url}/admin/users",
                headers={"X-API-Key": st.session_state.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                
                if users:
                    for user in users:
                        with st.expander(f"👤 {user['user_name']} ({user['user_email']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**ID:** `{user['user_id']}`")
                                st.markdown(f"**Role:** {user['role']}")
                            with col2:
                                st.markdown(f"**Active:** {'✅ Yes' if user['is_active'] else '❌ No'}")
                                if st.button("🗑️ Delete", key=f"del_user_{user['user_id']}"):
                                    requests.delete(
                                        f"{st.session_state.api_base_url}/admin/users/{user['user_id']}",
                                        headers={"X-API-Key": st.session_state.api_key}
                                    )
                                    st.success("Deleted!")
                                    st.rerun()
                else:
                    st.info("No users found")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # TAB 5: API KEYS
    with tab5:
        st.markdown("### 🔑 API Key Management")
        
        st.warning("⚠️ API keys are sensitive. Store them securely!")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("Generate and manage API keys")
        with col2:
            if st.button("➕ Generate API Key", use_container_width=True):
                st.session_state['show_create_key'] = True
        
        # Create API key form
        if st.session_state.get('show_create_key'):
            with st.form("create_key_form"):
                st.markdown("#### Generate New API Key")
                
                user_id = st.text_input("User ID")
                key_name = st.text_input("Key Name", placeholder="e.g., Production Key")
                org_id = st.text_input("Organization ID (Optional)")
                permissions = st.multiselect(
                    "Permissions",
                    ["analyzer", "chatbot", "evaluator", "admin"],
                    default=["analyzer", "chatbot", "evaluator"]
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Generate", type="primary", use_container_width=True):
                        try:
                            response = requests.post(
                                f"{st.session_state.api_base_url}/admin/api-keys",
                                headers={"X-API-Key": st.session_state.api_key},
                                json={
                                    "user_id": user_id,
                                    "key_name": key_name,
                                    "organization_id": org_id if org_id else None,
                                    "permissions": permissions
                                }
                            )
                            if response.status_code == 201:
                                data = response.json()
                                st.success("✅ API Key generated!")
                                st.code(data.get('api_key'), language="text")
                                st.warning("⚠️ Copy this key now! It won't be shown again.")
                                st.session_state['show_create_key'] = False
                            else:
                                st.error(f"❌ Failed: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                with col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state['show_create_key'] = False
                        st.rerun()
        
        # List API keys
        st.markdown("---")
        st.markdown("#### Existing API Keys")
        
        try:
            response = requests.get(
                f"{st.session_state.api_base_url}/admin/api-keys",
                headers={"X-API-Key": st.session_state.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                keys = data.get('api_keys', [])
                
                if keys:
                    for key in keys:
                        with st.expander(f"🔑 {key['key_name']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**User ID:** `{key['user_id']}`")
                                st.markdown(f"**Key ID:** `{key['key_id']}`")
                                st.markdown(f"**Permissions:** {', '.join(key.get('permissions', []))}")
                            with col2:
                                st.markdown(f"**Active:** {'✅ Yes' if key['is_active'] else '❌ No'}")
                                if st.button("🗑️ Revoke", key=f"del_key_{key['key_id']}"):
                                    requests.delete(
                                        f"{st.session_state.api_base_url}/admin/api-keys/{key['key_id']}",
                                        headers={"X-API-Key": st.session_state.api_key}
                                    )
                                    st.success("Revoked!")
                                    st.rerun()
                else:
                    st.info("No API keys found")
        except Exception as e:
            st.error(f"Error: {str(e)}")

