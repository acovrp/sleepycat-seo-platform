import streamlit as st
import os
import json
import urllib.parse
import requests
import time
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

st.set_page_config(page_title="SleepyCat Engine", page_icon="🐈", layout="wide")

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(BASE_PATH, "generation_history.json")
VAULT_PATH = os.path.join(BASE_PATH, "outputs")
if not os.path.exists(VAULT_PATH): os.makedirs(VAULT_PATH)

CLIENT_ID = "160422986634-5gpernee6sn90rtng8uqphrc7rris4t4.apps.googleusercontent.com"
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://sleepycat-seo1.streamlit.app/"

if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def login_ui():
    st.title("🐈 SleepyCat SEO Engine")
    st.info("Access restricted to @sleepycat.in accounts.")

    if not CLIENT_SECRET:
        st.error("⚠️ GOOGLE_CLIENT_SECRET missing from Streamlit Secrets.")
        return

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
        "access_type": "online"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    st.link_button("🚀 Sign in with Google", auth_url, use_container_width=True, type="primary")

    # OAuth callback handler
    qp = st.query_params
    if "code" in qp:
        with st.spinner("Authenticating..."):
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
                    email = info.get("email")
                    if email and email.endswith("@sleepycat.in"):
                        st.session_state["user_email"] = email
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(f"Access denied: {email} is not a @sleepycat.in account.")
                else:
                    st.error(f"Token exchange failed: {tokens.get('error_description', str(tokens))}")
            except Exception as e:
                st.error(f"Auth error: {e}")

if not st.session_state["user_email"]:
    login_ui()
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.header(f"👤 {st.session_state['user_email']}")
    st.markdown("---")
    comp_k = st.secrets.get("COMPANY_CLAUDE_KEY") or os.environ.get("COMPANY_CLAUDE_KEY")
    if comp_k: st.success("🏢 Company Claude: LIVE")

    st.header("🔑 Keys")
    g_key   = st.text_input("Gemini",  type="password", value=st.session_state.get("GEMINI_KEY", ""))
    c_key   = st.text_input("Claude",  type="password", value=st.session_state.get("CLAUDE_KEY", ""))
    oai_key = st.text_input("OpenAI",  type="password", value=st.session_state.get("OPENAI_KEY", ""))
    kimi_key= st.text_input("Kimi",    type="password", value=st.session_state.get("KIMI_KEY", ""))

    models = []
    if comp_k: models.append("anthropic/claude-3-5-sonnet-20241022 (Company)")
    if g_key:
        st.session_state["GEMINI_KEY"] = g_key
        models.extend(["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"])
    if c_key:
        st.session_state["CLAUDE_KEY"] = c_key
        models.append("anthropic/claude-3-5-sonnet-20241022")
    if oai_key:
        st.session_state["OPENAI_KEY"] = oai_key
        models.extend(["gpt-4o", "gpt-4o-mini"])
    if kimi_key:
        st.session_state["KIMI_KEY"] = kimi_key
        models.extend(["moonshot/moonshot-v1-8k", "moonshot/moonshot-v1-128k"])

    if st.button("Logout"):
        st.session_state["user_email"] = None
        st.rerun()

# --- Pipeline ---
def run_pipeline(kw, model_choice):
    from sleepycat_seo_agent import Orchestrator
    if "(Company)" in model_choice:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets.get("COMPANY_CLAUDE_KEY") or os.environ.get("COMPANY_CLAUDE_KEY", "")
    elif st.session_state.get("CLAUDE_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = st.session_state["CLAUDE_KEY"]
    if st.session_state.get("GEMINI_KEY"):
        os.environ["GEMINI_API_KEY"] = st.session_state["GEMINI_KEY"]
    if st.session_state.get("OPENAI_KEY"):
        os.environ["OPENAI_API_KEY"] = st.session_state["OPENAI_KEY"]
    if st.session_state.get("KIMI_KEY"):
        os.environ["MOONSHOT_API_KEY"] = st.session_state["KIMI_KEY"]

    engine = Orchestrator(model=model_choice.split(" (")[0])
    with st.status("Engine running...", expanded=True) as s:
        st.write("🕵️ SERP analysis → brand strategy → draft → SEO edit → humanize...")
        final, dur = engine.run(kw)
        s.update(label=f"Done in {dur}s!", state="complete")
    return final

def is_good_content(content):
    if not content or len(content) < 400:
        return False
    if "Agent " in content and " failed" in content:
        return False
    return True

def save_history(kw, content):
    if not is_good_content(content):
        return
    hist = []
    try:
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f: hist = json.load(f)
    except: pass
    hist.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user": st.session_state["user_email"],
        "keyword": kw,
        "content": content
    })
    with open(HISTORY_PATH, "w") as f: json.dump(hist, f, indent=2)

# --- Tabs ---
t1, t2 = st.tabs(["🚀 Generator", "📜 History"])

with t1:
    kw = st.text_input("Target Keyword", placeholder="e.g. Best mattress for back pain India")
    model = st.selectbox("Engine", models if models else ["No API Keys — add in sidebar"])
    if st.button("Generate", type="primary") and kw:
        content = run_pipeline(kw, model)
        if content:
            save_history(kw, content)
            st.markdown(content)
            st.download_button("Download .md", content, f"{kw.replace(' ','_')}.md")

with t2:
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r") as f:
                hist = json.load(f)
            for i in hist[::-1]:
                if not is_good_content(i.get("content", "")):
                    continue
                with st.expander(f"{i.get('timestamp')} — {i.get('keyword')}"):
                    st.markdown(i.get("content", ""))
        except:
            st.error("History load error.")
