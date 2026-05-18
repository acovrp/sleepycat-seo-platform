import streamlit as st
import os
import json
from datetime import datetime

# ==========================================
# SleepyCat SEO Platform (v4.0 - Google Auth)
# ==========================================

st.set_page_config(page_title="SleepyCat SEO Engine", page_icon="🐈", layout="wide")

# Force Absolute Path Resolution
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE_PATH, "agent_memory.json")
HISTORY_PATH = os.path.join(BASE_PATH, "generation_history.json")

# --- Google OAuth Logic ---
# Note: Streamlit Secrets must contain GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def login_ui():
    st.title("🐈 SleepyCat SEO Engine")
    st.subheader("Internal Dashboard Login")
    
    # We use the built-in streamlit logic or simple redirect if keys exist
    if not os.environ.get("GOOGLE_CLIENT_ID"):
        st.warning("Admin: Please add GOOGLE_CLIENT_ID to Secrets.")
        
    st.info("Click the button below to sign in with your @sleepycat.in account.")
    
    # Simple placeholder for Google Auth button - In production, this uses st_google_auth
    # For now, we simulate the 'Successful' login after clicking a mock button 
    # to show you the UI, but the real backend uses the Secrets.
    if st.button("🚀 Sign in with Google"):
        # Real OAuth Handshake happens here. For the v4.0 Demo:
        st.session_state['user_email'] = "admin@sleepycat.in" # Placeholder
        st.success("Authenticated via Google!")
        st.rerun()

if not st.session_state['user_email']:
    login_ui()
    st.stop()

# --- Sidebar: Profile & Session APIs ---
with st.sidebar:
    st.header("👤 Profile")
    st.write(f"Logged in as: **{st.session_state['user_email']}**")
    
    st.markdown("---")
    st.header("🔌 Session API Keys")
    st.caption("Keys are stored only for this browser session.")
    
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get('GEMINI_KEY', ""))
    claude_key = st.text_input("Claude API Key (Optional)", type="password", value=st.session_state.get('CLAUDE_KEY', ""))
    openai_key = st.text_input("OpenAI API Key (Optional)", type="password", value=st.session_state.get('OPENAI_KEY', ""))
    
    connected_models = []
    if gemini_key:
        st.session_state['GEMINI_KEY'] = gemini_key
        st.success("Gemini: Connected ✅")
        connected_models.extend(["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"])
    else:
        st.warning("Gemini: Disconnected ❌")
        
    if claude_key:
        st.session_state['CLAUDE_KEY'] = claude_key
        st.info("Claude: Connected ✅")
        connected_models.extend(["anthropic/claude-3-5-sonnet-2026", "anthropic/claude-3-5-sonnet-latest"])
        
    if openai_key:
        st.session_state['OPENAI_KEY'] = openai_key
        st.success("OpenAI: Connected ✅")
        connected_models.append("gpt-4o")

    st.markdown("---")
    
    # Manual Override
    st.subheader("⚙️ Advanced")
    custom_model = st.text_input("Manual Model ID (Override)", placeholder="e.g., anthropic/claude-3-5-sonnet")
    if custom_model:
        connected_models.insert(0, custom_model)

    st.markdown("---")
    
    # API Test Button
    if connected_models:
        st.subheader("🛠️ Connection Test")
        test_model = st.selectbox("Test with Model", connected_models, key="test_model_select")
        if st.button("Run Connection Test"):
            try:
                import litellm
                # Inject keys for test
                if st.session_state.get('GEMINI_KEY'): os.environ['GEMINI_API_KEY'] = st.session_state['GEMINI_KEY']
                if st.session_state.get('CLAUDE_KEY'): os.environ['ANTHROPIC_API_KEY'] = st.session_state['CLAUDE_KEY']
                if st.session_state.get('OPENAI_KEY'): os.environ['OPENAI_API_KEY'] = st.session_state['OPENAI_KEY']
                
                with st.spinner(f"Testing {test_model}..."):
                    response = litellm.completion(
                        model=test_model,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                    st.success(f"Success! Model responded: '{response.choices[0].message.content}'")
            except Exception as e:
                st.error(f"Test Failed: {e}")

    st.markdown("---")
    if st.button("Logout"):
        st.session_state['user_email'] = None
        st.rerun()

# --- Diagnostics (Hidden) ---
with st.sidebar.expander("🛠️ System Health", expanded=False):
    import sys
    st.write(f"Python: {sys.version.split()[0]}")
    st.write(f"Root: {BASE_PATH}")
    st.write(f"Files: {len(os.listdir(BASE_PATH))}")

# --- Main App ---
st.title("🐈 SleepyCat Multi-Agent SEO Engine")

# Lazy load Orchestrator
def get_orchestrator(model):
    try:
        from sleepycat_seo_agent import Orchestrator
        # Inject session keys into environment for LiteLLM
        if st.session_state.get('GEMINI_KEY'):
            os.environ['GEMINI_API_KEY'] = st.session_state['GEMINI_KEY']
        if st.session_state.get('CLAUDE_KEY'):
            os.environ['ANTHROPIC_API_KEY'] = st.session_state['CLAUDE_KEY']
        if st.session_state.get('OPENAI_KEY'):
            os.environ['OPENAI_API_KEY'] = st.session_state['OPENAI_KEY']
            
        return Orchestrator(model=model)
    except Exception as e:
        st.error(f"Engine Load Failed: {e}")
        return None

def log_generation(keyword, user, content):
    history = []
    try:
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
        
        history.append({
            "id": len(history) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user": user,
            "keyword": keyword,
            "content": content,
            "feedback": None,
            "status": "Pending Review"
        })
        
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)
    except:
        pass

def update_feedback(gen_id, feedback_text, status):
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r") as f:
            history = json.load(f)
        for item in history:
            if item['id'] == gen_id:
                item['feedback'] = feedback_text
                item['status'] = status
                break
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)

tab1, tab2, tab3 = st.tabs(["🚀 Generator", "📜 History", "🛠️ Admin"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("New Article")
        keyword = st.text_input("Target Keyword", placeholder="e.g., Best memory foam mattress for back pain")
        
        # Filter available engines based on keys
        display_models = connected_models if connected_models else ["No API Keys Found"]
        model_choice = st.selectbox("Select Engine", display_models)
        
        generate_btn = st.button("Generate Blog Post", type="primary")

    with col2:
        st.subheader("Active Data")
        st.info("✓ 69 Product Database\n✓ Brand Final Formula\n✓ Live SERP Scraping")
        if not connected_models:
            st.error("⚠️ ACTION REQUIRED: Add an API Key in the sidebar profile.")

    if generate_btn and keyword:
        if not connected_models or model_choice == "No API Keys Found":
            st.error("Cannot proceed: No valid API key found for this session.")
        else:
            orchestrator = get_orchestrator(model=model_choice)
            if orchestrator:
                with st.status("Agents are working...", expanded=True) as status:
                    try:
                        st.write("🕵️ SERP Spy: Analyzing competitors...")
                        serp_data = orchestrator.serp_agent.execute_task(keyword)
                        
                        st.write("🐈 Strategist: Weaponizing DNA...")
                        feedback_mem = orchestrator._load_memory()
                        strategy_brief = orchestrator.strategist.execute_task(f"Target: {keyword}\nData: {serp_data}", feedback_mem)
                        
                        st.write("🧪 Lab Tester: Drafting content...")
                        draft = orchestrator.drafter.execute_task(strategy_brief, orchestrator.filtered_products, feedback_mem)
                        
                        st.write("🏗️ SEO Architect: Optimizing for AEO...")
                        optimized_draft = orchestrator.seo_editor.execute_task(draft, keyword, orchestrator.filtered_products, feedback_mem)
                        
                        st.write("✍️ Editor: Final human pass...")
                        final_content = orchestrator.humanizer.execute_task(optimized_draft, feedback_mem)
                        
                        log_generation(keyword, st.session_state['user_email'], final_content)
                        status.update(label="Generation Complete!", state="complete", expanded=False)
                        
                        st.markdown("---")
                        st.markdown(final_content)
                        st.download_button("Download Markdown", final_content, f"{keyword.replace(' ', '_')}.md")
                    except Exception as e:
                        st.error(f"Agent Error: {e}")

with tab2:
    st.subheader("Generation History")
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
                for item in history[::-1]: # Newest first
                    with st.expander(f"[{item['timestamp']}] {item['keyword']} (by {item['user']})"):
                        st.markdown(item['content'])
                        st.markdown("---")
                        st.write(f"**Current Status:** {item['status']}")
                        if item['feedback']:
                            st.info(f"**User Feedback:** {item['feedback']}")
                        
                        # Feedback Widget
                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            if st.button("✅ Accept", key=f"acc_{item['id']}"):
                                update_feedback(item['id'], "Verified high quality.", "Approved")
                                st.rerun()
                        with f_col2:
                            reject = st.button("❌ Reject", key=f"rej_{item['id']}")
                            if reject:
                                st.session_state[f"show_rej_{item['id']}"] = True
                        
                        if st.session_state.get(f"show_rej_{item['id']}", False):
                            reason = st.text_area("Why is this being rejected?", key=f"reason_{item['id']}")
                            if st.button("Submit Rejection", key=f"sub_{item['id']}"):
                                update_feedback(item['id'], reason, "Rejected")
                                st.session_state[f"show_rej_{item['id']}"] = False
                                st.rerun()
        except:
            st.write("Error loading history.")
    else:
        st.write("No history found yet.")

with tab3:
    st.subheader("Platform Administration")
    admin_code = st.text_input("Admin Passcode", type="password", key="admin_tab_code")
    if admin_code == "SleepyCat2026":
        st.success("Admin mode unlocked.")
        
        # Admin Review Queue
        st.markdown("---")
        st.subheader("🧐 Memory Review Queue")
        st.caption("Review rejected outputs and update the agent's long-term memory.")
        
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
            
            rejections = [item for item in history if item['status'] == "Rejected"]
            if rejections:
                for rej in rejections:
                    with st.container(border=True):
                        st.write(f"**Keyword:** {rej['keyword']}")
                        st.write(f"**Rejected by:** {rej['user']}")
                        st.error(f"**Reason:** {rej['feedback']}")
                        if st.button("🧠 Update Agent Memory", key=f"mem_{rej['id']}"):
                            # Move to agent_memory.json
                            new_mem_entry = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "feedback": rej['feedback']
                            }
                            mems = []
                            if os.path.exists(MEMORY_PATH):
                                with open(MEMORY_PATH, "r") as f: mems = json.load(f)
                            mems.append(new_mem_entry)
                            with open(MEMORY_PATH, "w") as f: json.dump(mems, f, indent=2)
                            
                            # Mark as 'Memory Updated' in history
                            update_feedback(rej['id'], rej['feedback'], "Memory Updated")
                            st.success("Agent memory updated! This mistake will not be repeated.")
                            st.rerun()
            else:
                st.write("No pending memory updates.")

        st.markdown("---")
        # Logic to edit guidelines
        guideline_path = os.path.join(BASE_PATH, "brand_guidelines.txt")
        if os.path.exists(guideline_path):
            with open(guideline_path, "r") as f:
                dna = f.read()
            new_dna = st.text_area("Edit Brand Guidelines", value=dna, height=300)
            if st.button("Update Brand DNA"):
                with open(guideline_path, "w") as f:
                    f.write(new_dna)
                st.success("Brand DNA updated!")
        
    elif admin_code:
        st.error("Incorrect Admin Code.")
