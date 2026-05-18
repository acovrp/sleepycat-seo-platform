import streamlit as st
import os
import json
import subprocess
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# ==========================================
# SleepyCat SEO Platform (v5.0 - Secure Cloud)
# ==========================================

st.set_page_config(page_title="SleepyCat SEO Engine", page_icon="🐈", layout="wide")

# Paths & Folders
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE_PATH, "agent_memory.json")
HISTORY_PATH = os.path.join(BASE_PATH, "generation_history.json")
VAULT_PATH = os.path.join(BASE_PATH, "outputs")

if not os.path.exists(VAULT_PATH):
    os.makedirs(VAULT_PATH)

# --- Real Google OAuth ---
CLIENT_ID = "487804996561-d6v7lkm2545839ed2atibdkih2vjnp7e.apps.googleusercontent.com"
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://sleepycat-seo1.streamlit.app/"

if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

import urllib.parse

# --- Real Google OAuth (Strict v5.2) ---
CLIENT_ID = "487804996561-d6v7lkm2545839ed2atibdkih2vjnp7e.apps.googleusercontent.com"
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://sleepycat-seo1.streamlit.app" # No trailing slash

if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def login_ui():
    st.title("🐈 SleepyCat SEO Engine (v5.2)")
    st.subheader("Enterprise Login Required")
    st.info("Authorized access for @sleepycat.in domains only.")
    
    if not CLIENT_SECRET:
        st.error("⚠️ GOOGLE_CLIENT_SECRET is missing from Streamlit Secrets.")
        return

    # Manual Auth URL Construction for 100% control
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
        "access_type": "online"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    st.markdown(f'''
        <a href="{auth_url}" target="_self" style="text-decoration: none;">
            <div style="background-color: #4285F4; color: white; padding: 12px 24px; border-radius: 6px; text-align: center; font-weight: bold; font-size: 16px; cursor: pointer;">
                🚀 Sign in with SleepyCat Google Account
            </div>
        </a>
    ''', unsafe_allow_html=True)

    with st.expander("🛠️ Debug Connection"):
        st.write(f"**Redirect URI:** `{REDIRECT_URI}`")
        st.write(f"**Client ID:** `{CLIENT_ID}`")
        if st.checkbox("Show Raw Auth Link"):
            st.code(auth_url)

    # Handle Callback via st.query_params
    query_params = st.query_params
    if "code" in query_params:
        try:
            # Exchange code for token manually to ensure consistency
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": query_params["code"],
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"
            }
            res = requests.post(token_url, data=data)
            tokens = res.json()
            
            if "id_token" in tokens:
                info = id_token.verify_oauth2_token(tokens["id_token"], google_requests.Request(), CLIENT_ID)
                email = info.get('email')
                
                if email and (email.endswith("@sleepycat.in") or email == "admin@sleepycat.in"):
                    st.session_state['user_email'] = email
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"Access Denied: {email} is not authorized.")
            else:
                st.error(f"Token Exchange Failed: {tokens.get('error_description', tokens.get('error', 'Unknown Error'))}")
        except Exception as e:
            st.error(f"Auth System Error: {e}")

if not st.session_state['user_email']:
    login_ui()
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.header("👤 Profile")
    st.write(f"Logged in: **{st.session_state['user_email']}**")
    
    st.markdown("---")
    st.header("🔌 API Connection")
    
    # Company Key Status
    company_claude = os.environ.get("COMPANY_CLAUDE_KEY")
    if company_claude:
        st.success("Claude (Company Mode): Active ✅")
    
    st.markdown("---")
    st.header("🔑 Session Keys")
    gemini_key = st.text_input("Gemini Key", type="password", value=st.session_state.get('GEMINI_KEY', ""))
    claude_key = st.text_input("Claude Key", type="password", value=st.session_state.get('CLAUDE_KEY', ""))
    
    connected_models = []
    if company_claude:
        connected_models.append("anthropic/claude-3-5-sonnet-latest (Company)")
    if gemini_key:
        st.session_state['GEMINI_KEY'] = gemini_key
        connected_models.extend(["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"])
    if claude_key:
        st.session_state['CLAUDE_KEY'] = claude_key
        if "anthropic/claude-3-5-sonnet-latest (Company)" not in connected_models:
            connected_models.append("anthropic/claude-3-5-sonnet-latest")

    st.markdown("---")
    if st.button("Logout"):
        st.session_state['user_email'] = None
        st.rerun()

# --- Main Functions ---
def save_to_vault(keyword, content):
    filename = f"{datetime.now().strftime('%Y%m%d')}_{keyword.replace(' ', '_')}.md"
    safe_filename = "".join([c for c in filename if c.isalnum() or c in ('_', '.')]).rstrip()
    file_path = os.path.join(VAULT_PATH, safe_filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return safe_filename

def get_orchestrator(model):
    try:
        from sleepycat_seo_agent import Orchestrator
        if "(Company)" in model:
            os.environ['ANTHROPIC_API_KEY'] = os.environ.get("COMPANY_CLAUDE_KEY", "")
        elif st.session_state.get('CLAUDE_KEY'):
            os.environ['ANTHROPIC_API_KEY'] = st.session_state['CLAUDE_KEY']
        
        if st.session_state.get('GEMINI_KEY'):
            os.environ['GEMINI_API_KEY'] = st.session_state['GEMINI_KEY']
            
        clean_model = model.split(" (")[0]
        return Orchestrator(model=clean_model)
    except Exception as e:
        st.error(f"Engine Load Failed: {e}")
        return None

def log_generation(keyword, user, content, filename):
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
            "filename": filename,
            "status": "Pending Review"
        })
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)
    except: pass

tab1, tab2, tab3 = st.tabs(["🚀 Generator", "📜 History", "🛠️ Admin"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("New Article")
        keyword = st.text_input("Target Keyword", placeholder="e.g., Best memory foam mattress for back pain")
        display_models = connected_models if connected_models else ["No API Keys Found"]
        model_choice = st.selectbox("Select Engine", display_models)
        generate_btn = st.button("Generate Blog Post", type="primary")

    with col2:
        st.subheader("Knowledge Vault")
        st.write(f"📁 **Storage:** {len(os.listdir(VAULT_PATH))} articles")
        st.info("All generations are auto-archived to the SleepyCat GitHub Vault.")

    if generate_btn and keyword:
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
                    st.write("✍️ Editor: Final pass...")
                    final_content = orchestrator.humanizer.execute_task(optimized_draft, feedback_mem)
                    
                    vault_file = save_to_vault(keyword, final_content)
                    log_generation(keyword, st.session_state['user_email'], final_content, vault_file)
                    
                    status.update(label="Generation Complete!", state="complete")
                    st.markdown(final_content)
                    st.download_button("Download Markdown", final_content, vault_file)
                except Exception as e:
                    st.error(f"Agent Error: {e}")

with tab2:
    st.subheader("Generation History")
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
                for item in history[::-1]:
                    timestamp = item.get('timestamp', 'Unknown')
                    keyword = item.get('keyword', 'Unknown')
                    user = item.get('user', 'Unknown')
                    with st.expander(f"[{timestamp}] {keyword} (by {user})"):
                        st.markdown(item.get('content', 'No content.'))
                        if item.get('filename'):
                            st.caption(f"Vault ID: {item['filename']}")
        except: st.error("History Load Error.")

with tab3:
    st.subheader("Platform Administration")
    admin_code = st.text_input("Admin Passcode", type="password")
    if admin_code == "SleepyCat2026":
        st.success("Admin mode unlocked.")
        
        st.subheader("☁️ GitHub Vault Sync")
        st.write("Push all local articles to the persistent GitHub repository.")
        if st.button("🚀 Sync to Cloud Vault"):
            try:
                # Add all outputs to git
                subprocess.run(["git", "config", "user.email", "admin@sleepycat.in"], check=True)
                subprocess.run(["git", "config", "user.name", "SleepyCat Admin"], check=True)
                subprocess.run(["git", "add", "outputs/*"], check=True)
                subprocess.run(["git", "add", "*.json"], check=True)
                subprocess.run(["git", "commit", "-m", f"Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=True)
                subprocess.run(["git", "push", "origin", "master"], check=True)
                st.success("Successfully synced all articles to GitHub 100GB Vault!")
            except Exception as e:
                st.error(f"Sync Failed: {e}")
                
        st.markdown("---")
        st.subheader("🧐 Memory Review Queue")
        st.caption("Review rejected outputs and update the agent's long-term memory.")
        
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
            
            rejections = [item for item in history if item.get('status') == "Rejected"]
            if rejections:
                for rej in rejections:
                    with st.container(border=True):
                        st.write(f"**Keyword:** {rej.get('keyword')}")
                        st.error(f"**Reason:** {rej.get('feedback')}")
                        if st.button("🧠 Update Agent Memory", key=f"mem_{rej.get('id')}"):
                            new_mem_entry = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "feedback": rej['feedback']
                            }
                            mems = []
                            if os.path.exists(MEMORY_PATH):
                                with open(MEMORY_PATH, "r") as f: mems = json.load(f)
                            mems.append(new_mem_entry)
                            with open(MEMORY_PATH, "w") as f: json.dump(mems, f, indent=2)
                            st.success("Agent memory updated!")
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
