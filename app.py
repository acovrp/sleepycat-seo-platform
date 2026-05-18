import streamlit as st
import os
import json
from datetime import datetime

# ==========================================
# SleepyCat SEO Platform (v3.5 - Enterprise)
# Frontend: Streamlit with User Attribution
# ==========================================

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="SleepyCat SEO Engine", page_icon="🐈", layout="wide")

# Force Absolute Path Resolution
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE_PATH, "agent_memory.json")
HISTORY_PATH = os.path.join(BASE_PATH, "generation_history.json")

# --- Authentication Logic ---
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def check_access(email, code):
    # Security: Only allow @sleepycat.in domains
    if "@sleepycat.in" in email.lower() and code == "SleepyRest2026":
        return True
    return False

if not st.session_state['user_email']:
    st.title("🐈 SleepyCat SEO Engine")
    st.subheader("Employee Login")
    with st.form("login_form"):
        email = st.text_input("Work Email", placeholder="yourname@sleepycat.in")
        passcode = st.text_input("Access Code", type="password")
        submit = st.form_submit_button("Enter Platform")
        if submit:
            if check_access(email, passcode):
                st.session_state['user_email'] = email
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Access Denied: Invalid email domain or passcode.")
    st.info("Note: This dashboard is for internal SleepyCat use only.")
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
    
    if gemini_key:
        st.session_state['GEMINI_KEY'] = gemini_key
        st.success("Gemini: Connected ✅")
    else:
        st.warning("Gemini: Disconnected ❌")
        
    if claude_key:
        st.session_state['CLAUDE_KEY'] = claude_key
        st.info("Claude: Connected ✅")

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
            
        return Orchestrator(model=model)
    except Exception as e:
        st.error(f"Engine Load Failed: {e}")
        return None

def log_generation(keyword, user):
    history = []
    try:
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
        
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user": user,
            "keyword": keyword
        })
        
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)
    except:
        pass

tab1, tab2, tab3 = st.tabs(["🚀 Generator", "📜 History", "🛠️ Admin"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("New Article")
        keyword = st.text_input("Target Keyword", placeholder="e.g., Best memory foam mattress for back pain")
        model_choice = st.selectbox("Select Engine", ["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro", "anthropic/claude-3-5-sonnet", "openai/gpt-4o"])
        generate_btn = st.button("Generate Blog Post", type="primary")

    with col2:
        st.subheader("Active Data")
        st.info("✓ 69 Product Database\n✓ Brand Final Formula\n✓ Live SERP Scraping")
        if not st.session_state.get('GEMINI_KEY'):
            st.error("⚠️ ACTION REQUIRED: Add your Gemini API Key in the sidebar profile.")

    if generate_btn and keyword:
        if not st.session_state.get('GEMINI_KEY'):
            st.error("Cannot proceed: No API key for the current session.")
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
                        
                        log_generation(keyword, st.session_state['user_email'])
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
                st.table(history[::-1]) # Newest first
        except:
            st.write("Error loading history.")
    else:
        st.write("No history found yet.")

with tab3:
    st.subheader("Platform Administration")
    admin_code = st.text_input("Admin Passcode", type="password", key="admin_tab_code")
    if admin_code == "SleepyCat2026":
        st.success("Admin mode unlocked.")
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
        
        st.markdown("---")
        st.subheader("Global Memory (RLHF)")
        if os.path.exists(MEMORY_PATH):
            with open(MEMORY_PATH, "r") as f:
                mems = json.load(f)
                st.write(mems)
    elif admin_code:
        st.error("Incorrect Admin Code.")
