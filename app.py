import streamlit as st
import os
import json
import urllib.parse
import requests
import time
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# ==========================================
# SleepyCat SEO Platform (v5.8 - ULTRA SPEED)
# Optimized for Performance & Reliable Auth
# ==========================================

st.set_page_config(page_title="SleepyCat Engine", page_icon="🐈", layout="wide")

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(BASE_PATH, "generation_history.json")
VAULT_PATH = os.path.join(BASE_PATH, "outputs")
if not os.path.exists(VAULT_PATH): os.makedirs(VAULT_PATH)

# --- Canonical Auth (Native v5.8) ---
CLIENT_ID = "160422986634-5gpernee6sn90rtng8uqphrc7rris4t4.apps.googleusercontent.com"
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://sleepycat-seo1.streamlit.app/"

if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def login_ui():
    st.title("🐈 SleepyCat SEO (v5.8)")
    st.info("Performance Mode Active. Access for @sleepycat.in only.")
    
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "prompt": "select_account",
        "access_type": "online"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    st.markdown(f'''
        <a href="{url}" target="_self" style="text-decoration:none;">
            <div style="background-color:#4285F4;color:white;padding:15px;border-radius:5px;text-align:center;font-weight:bold;font-size:20px;">
                🚀 Login with SleepyCat Google
            </div>
        </a>
    ''', unsafe_allow_html=True)

    # Manual Callback Processor
    qp = st.query_params
    if "code" in qp:
        try:
            res = requests.post("https://oauth2.googleapis.com/token", data={
                "code": qp["code"],
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"
            })
            tokens = res.json()
            if "id_token" in tokens:
                info = id_token.verify_oauth2_token(tokens["id_token"], google_requests.Request(), CLIENT_ID)
                email = info.get('email')
                if email and (email.endswith("@sleepycat.in") or email == "admin@sleepycat.in"):
                    st.session_state['user_email'] = email
                    st.query_params.clear()
                    st.rerun()
                else: st.error(f"Unauthorized: {email}")
            else: st.error("OAuth Exchange Failed.")
        except Exception as e: st.error(f"Auth Error: {e}")

if not st.session_state['user_email']:
    login_ui()
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.header(f"👤 {st.session_state['user_email']}")
    st.markdown("---")
    comp_k = os.environ.get("COMPANY_CLAUDE_KEY")
    if comp_k: st.success("🏢 Company Claude: LIVE")
    
    st.header("🔑 Local Keys")
    g_key = st.text_input("Gemini", type="password", value=st.session_state.get('GEMINI_KEY',""))
    c_key = st.text_input("Claude", type="password", value=st.session_state.get('CLAUDE_KEY',""))
    
    models = []
    if comp_k: models.append("anthropic/claude-3-5-sonnet-latest (Company)")
    if g_key: 
        st.session_state['GEMINI_KEY'] = g_key
        models.extend(["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"])
    if c_key:
        st.session_state['CLAUDE_KEY'] = c_key
        models.append("anthropic/claude-3-5-sonnet-latest")

    if st.button("Logout"):
        st.session_state['user_email'] = None
        st.rerun()

# --- Orchestrator ---
def run_pipeline(kw, model_choice):
    from sleepycat_seo_agent import Orchestrator
    
    # Inject Keys
    if "(Company)" in model_choice:
        os.environ['ANTHROPIC_API_KEY'] = os.environ.get("COMPANY_CLAUDE_KEY","")
    elif st.session_state.get('CLAUDE_KEY'):
        os.environ['ANTHROPIC_API_KEY'] = st.session_state['CLAUDE_KEY']
    
    if st.session_state.get('GEMINI_KEY'):
        os.environ['GEMINI_API_KEY'] = st.session_state['GEMINI_KEY']
        
    engine = Orchestrator(model=model_choice.split(" (")[0])
    
    with st.status("Engine Active...", expanded=True) as s:
        st.write("🕵️ SERP Analysis...")
        serp = engine.serp_agent.execute_task(kw)
        
        st.write("🐈 Injecting Brand DNA...")
        brief = engine.strategist.execute_task(f"KW: {kw}\nSERP: {serp}")
        
        st.write("🧪 Lab Tester Drafting...")
        draft = engine.drafter.execute_task(brief, engine.products)
        
        st.write("🏗️ SEO Architecting...")
        opt = engine.seo_editor.execute_task(draft, kw, engine.products)
        
        st.write("✍️ Final Human Pass...")
        final, dur = engine.run(kw) # This handles steps internally now
        
        s.update(label=f"Done in {dur}s!", state="complete")
        return final

# --- Tabs ---
t1, t2 = st.tabs(["🚀 Generator", "📜 History"])

with t1:
    kw = st.text_input("Target Keyword", placeholder="How to choose a mattress...")
    model = st.selectbox("Engine", models if models else ["No Keys Found"])
    if st.button("Generate", type="primary") and kw:
        content = run_pipeline(kw, model)
        st.markdown(content)
        st.download_button("Download .md", content, f"{kw}.md")

with t2:
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH,"r") as f:
            hist = json.load(f)
            for i in hist[::-1]:
                with st.expander(f"{i.get('timestamp')} - {i.get('keyword')}"):
                    st.markdown(i.get('content'))
