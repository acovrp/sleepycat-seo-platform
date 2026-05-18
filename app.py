import streamlit as st
import os
import json
import urllib.parse
import requests
import time
import subprocess
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# ==========================================
# SleepyCat SEO Platform (v6.5)
# Live session checkpoint: resume pipeline after any agent failure
# ==========================================

st.set_page_config(page_title="SleepyCat Engine", page_icon="🐈", layout="wide")

# (input $/1M tokens, output $/1M tokens) — May 2026 pricing
PRICING = {
    "anthropic/claude-sonnet-4-6": (3.0,   15.0),
    "anthropic/claude-opus-4-7":   (15.0,  75.0),
    "gemini/gemini-2.5-flash":     (0.075,  0.30),
    "gemini/gemini-2.5-pro":       (1.25,  10.0),
    "gpt-4o":                      (2.50,  10.0),
    "gpt-4o-mini":                 (0.15,   0.60),
    "moonshot/moonshot-v1-8k":     (0.8,    2.4),
    "groq/llama-3.3-70b-versatile":(0.0,    0.0),
    "groq/llama-3.1-8b-instant":   (0.0,    0.0),
    "groq/mixtral-8x7b-32768":     (0.0,    0.0),
}
USD_TO_INR = 84  # update periodically

def _calc_cost(litellm_model, in_tok, out_tok):
    pr = PRICING.get(litellm_model, (2.0, 8.0))
    usd = (in_tok * pr[0] + out_tok * pr[1]) / 1_000_000
    return usd * USD_TO_INR  # returns INR

MODEL_MAP = {
    "Claude Sonnet (Company)": "anthropic/claude-sonnet-4-6",
    "Claude Opus (Company)":   "anthropic/claude-opus-4-7",
    "Claude Sonnet":           "anthropic/claude-sonnet-4-6",
    "Claude Opus":             "anthropic/claude-opus-4-7",
    "Gemini Flash":            "gemini/gemini-2.5-flash",
    "Gemini Pro":              "gemini/gemini-2.5-pro",
    "GPT-4o":                  "gpt-4o",
    "GPT-4o Mini":             "gpt-4o-mini",
    "Kimi 8K":                 "moonshot/moonshot-v1-8k",
    "Groq Llama 70B (Free)":  "groq/llama-3.3-70b-versatile",
    "Groq Llama 8B (Free)":   "groq/llama-3.1-8b-instant",
    "Groq Mixtral (Free)":    "groq/mixtral-8x7b-32768",
}

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(BASE_PATH, "generation_history.json")
VAULT_PATH = os.path.join(BASE_PATH, "outputs")
MEMORY_PATH = os.path.join(BASE_PATH, "agent_memory.json")
if not os.path.exists(VAULT_PATH): os.makedirs(VAULT_PATH)

# --- Canonical Auth (Strict v6.1) ---
CLIENT_ID = "160422986634-5gpernee6sn90rtng8uqphrc7rris4t4.apps.googleusercontent.com"
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://sleepycat-seo1.streamlit.app/"

if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

def login_ui():
    st.title("🐈 SleepyCat SEO Engine (v6.1)")
    st.info("Authorized access for @sleepycat.in domains only.")

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

    st.link_button("🚀 Sign in with SleepyCat Google", auth_url, use_container_width=True, type="primary")

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
                    if email and (email.endswith("@sleepycat.in") or email == "admin@sleepycat.in"):
                        st.session_state["user_email"] = email
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(f"Access denied: {email} is not authorized.")
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
    if comp_k: st.success("🏢 Company Claude: Active")

    st.header("🔑 Session Keys")
    st.caption("Personal keys for individual quotas.")
    g_key   = st.text_input("Gemini",  type="password", value=st.session_state.get("GEMINI_KEY", ""))
    c_key   = st.text_input("Claude",  type="password", value=st.session_state.get("CLAUDE_KEY", ""))
    oai_key = st.text_input("OpenAI",  type="password", value=st.session_state.get("OPENAI_KEY", ""))
    k_key   = st.text_input("Kimi",    type="password", value=st.session_state.get("KIMI_KEY", ""))
    gr_key  = st.text_input("Groq 🆓", type="password", value=st.session_state.get("GROQ_KEY", ""))

    models = []
    if comp_k: models.extend(["Claude Sonnet (Company)", "Claude Opus (Company)"])
    if g_key:
        st.session_state["GEMINI_KEY"] = g_key
        models.extend(["Gemini Flash", "Gemini Pro"])
    if c_key:
        st.session_state["CLAUDE_KEY"] = c_key
        models.extend(["Claude Sonnet", "Claude Opus"])
    if oai_key:
        st.session_state["OPENAI_KEY"] = oai_key
        models.extend(["GPT-4o", "GPT-4o Mini"])
    if k_key:
        st.session_state["KIMI_KEY"] = k_key
        models.append("Kimi 8K")
    if gr_key:
        st.session_state["GROQ_KEY"] = gr_key
        models.extend(["Groq Llama 70B (Free)", "Groq Llama 8B (Free)", "Groq Mixtral (Free)"])

    if st.button("Logout"):
        st.session_state["user_email"] = None
        st.rerun()

# --- Functions ---
def save_to_vault(keyword, content):
    filename = f"{datetime.now().strftime('%Y%m%d')}_{keyword.replace(' ', '_')}.md"
    safe_filename = "".join([c for c in filename if c.isalnum() or c in ('_', '.')]).rstrip()
    file_path = os.path.join(VAULT_PATH, safe_filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return safe_filename

def _stream_agent(label, stream_gen):
    """Streams an agent generator, returns final text."""
    st.write(label)
    ph = st.empty()
    text = ""
    for text in stream_gen:
        preview = text[-500:] if len(text) > 500 else text
        ph.markdown(f"```\n{preview}\n```\n_{len(text.split())} words_")
    ph.empty()
    return text

def _inject_keys(model_choice):
    if "Company" in model_choice:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets.get("COMPANY_CLAUDE_KEY") or os.environ.get("COMPANY_CLAUDE_KEY", "")
    elif "Claude" in model_choice and st.session_state.get("CLAUDE_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = st.session_state["CLAUDE_KEY"]
    if st.session_state.get("GEMINI_KEY"):
        os.environ["GEMINI_API_KEY"] = st.session_state["GEMINI_KEY"]
    if st.session_state.get("OPENAI_KEY"):
        os.environ["OPENAI_API_KEY"] = st.session_state["OPENAI_KEY"]
    if st.session_state.get("KIMI_KEY"):
        os.environ["MOONSHOT_API_KEY"] = st.session_state["KIMI_KEY"]
    groq_k = st.session_state.get("GROQ_KEY") or st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY", "")
    if groq_k:
        os.environ["GROQ_API_KEY"] = groq_k

def run_pipeline(kw, model_choice, resume=False, special_instructions=""):
    from sleepycat_seo_agent import Orchestrator, _is_error
    _inject_keys(model_choice)

    saved_cp = st.session_state.get("pipeline_checkpoint", {})
    cp = saved_cp if (resume and saved_cp.get("keyword") == kw) else {}
    checkpoint = {"keyword": kw, "serp": cp.get("serp"), "brief": cp.get("brief"),
                  "draft": cp.get("draft"), "opt": cp.get("opt"), "failed_at": None}

    litellm_model = MODEL_MAP.get(model_choice, model_choice)
    engine = Orchestrator(model=litellm_model)

    # Inject special instructions into every agent before any call
    if special_instructions:
        for agent in [engine.strategist, engine.drafter, engine.seo_editor, engine.humanizer]:
            agent.special_instructions = special_instructions

    # Token tracking (populated inside the status block below)
    tok = {"in": 0, "out": 0}

    with st.status("Super-Agent Active...", expanded=True) as s:
        cost_ph = st.empty()

        def _track(context_str, output_str):
            tok["in"]  += len(context_str) // 4
            tok["out"] += len(output_str)  // 4
            disp_inr    = _calc_cost(litellm_model, tok["in"], tok["out"])
            total_inr   = disp_inr * 2
            is_free     = PRICING.get(litellm_model, (1, 1))[0] == 0.0
            cost_str    = "FREE (Groq)" if is_free else f"₹{disp_inr:.3f} display · ~₹{total_inr:.3f} total"
            cost_ph.caption(f"🔢 ~{tok['in']+tok['out']:,} tokens so far · {cost_str}")

        def fail(stage, msg):
            checkpoint["failed_at"] = stage
            st.session_state["pipeline_checkpoint"] = checkpoint
            s.update(label=f"❌ {stage.title()} failed — switch key & Resume", state="error")
            st.error(msg)
        # Agent 1 — SERP Spy
        if checkpoint["serp"]:
            serp = checkpoint["serp"]
            url_count = serp.count("URL:") if serp else 0
            with st.expander(f"⚡ SERP — loaded from checkpoint ({url_count} page(s))"):
                st.code(serp, language=None)
        else:
            st.write("🕵️ **SERP Spy** scanning top results...")
            serp = engine.serp_agent.execute_task(kw)
            checkpoint["serp"] = serp
            serp_is_real = serp and "URL:" in serp
            if serp_is_real:
                url_count = serp.count("URL:")
                with st.expander(f"✅ SERP — {url_count} page(s) scraped (click to verify)"):
                    st.code(serp, language=None)
            else:
                st.warning(f"⚠️ SERP scraping returned no live data — proceeding without competitor context.\n\n`{serp[:200]}`")

        # Agent 2 — Strategist
        strat_ctx = f"KW: {kw}\nSERP: {serp}"
        if checkpoint["brief"]:
            st.success(f"⚡ Brief — loaded from checkpoint ({len(checkpoint['brief'].split())} words)")
            brief = checkpoint["brief"]
        else:
            brief = _stream_agent("🐈 **Strategist** writing content brief...",
                                  engine.strategist.stream_task(strat_ctx))
            if _is_error(brief): fail("strategist", brief); return None
            checkpoint["brief"] = brief
            st.success(f"✅ Brief — {len(brief.split())} words")
        _track(strat_ctx, brief)

        # Agent 3 — Drafter
        import json as _json
        draft_ctx = f"STRATEGY BRIEF:\n{brief}\n\nPRODUCT DB:\n{_json.dumps(engine.drafter_products, indent=1)}"
        if checkpoint["draft"]:
            st.success(f"⚡ Draft — loaded from checkpoint ({len(checkpoint['draft'].split())} words)")
            draft = checkpoint["draft"]
        else:
            draft = _stream_agent("🧪 **Drafter** writing 1000-1500 word article...",
                                  engine.drafter.stream_task(brief, engine.drafter_products))
            if _is_error(draft): fail("drafter", draft); return None
            checkpoint["draft"] = draft
            st.success(f"✅ Draft — {len(draft.split())} words")
        _track(draft_ctx, draft)

        # Agent 4 — SEO Architect
        seo_ctx = f"TARGET: {kw}\n\nDRAFT:\n{draft}"
        if checkpoint["opt"]:
            st.success(f"⚡ SEO pass — loaded from checkpoint ({len(checkpoint['opt'].split())} words)")
            opt = checkpoint["opt"]
        else:
            opt = _stream_agent("🏗️ **SEO Architect** adding AEO snippet & comparison table...",
                                engine.seo_editor.stream_task(draft, kw, engine.seo_arch_products))
            if _is_error(opt): fail("seo_architect", opt); return None
            checkpoint["opt"] = opt
            st.success(f"✅ SEO pass — {len(opt.split())} words")
        _track(seo_ctx, opt)

        # Agent 5 — Humanizer + full quality pass
        st.write("✍️ **Senior Editor** final brand polish...")
        final, dur = engine.run(kw, checkpoint=checkpoint)
        if _is_error(final): fail("humanizer", final); return None
        _track(opt, final)  # account for humanizer pass

        # Final cost card
        total_inr  = _calc_cost(litellm_model, tok["in"], tok["out"]) * 2
        is_free    = PRICING.get(litellm_model, (1, 1))[0] == 0.0
        if is_free:
            cost_ph.info(f"🔢 **~{(tok['in']+tok['out'])*2:,} tokens total** · **FREE (Groq)** 🎉")
        else:
            cost_ph.info(f"🔢 **~{(tok['in']+tok['out'])*2:,} tokens total** · **~₹{total_inr:.2f}** per blog ({model_choice})")

        st.session_state.pop("pipeline_checkpoint", None)
        s.update(label=f"✅ Done in {dur}s! ({len(final.split())} words)", state="complete")
        return final

def log_generation(kw, user, content, filename):
    hist = []
    try:
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f: hist = json.load(f)
        hist.append({
            "id": len(hist) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user": user,
            "keyword": kw,
            "content": content,
            "filename": filename,
            "status": "Pending Review"
        })
        with open(HISTORY_PATH, "w") as f: json.dump(hist, f, indent=2)
    except: pass

def update_feedback(gen_id, feedback, status):
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r") as f: hist = json.load(f)
        for i in hist:
            if i.get('id') == gen_id:
                i['feedback'] = feedback
                i['status'] = status
                break
        with open(HISTORY_PATH, "w") as f: json.dump(hist, f, indent=2)

ROUTING_OPTIONS = {
    "all":          "🌐 All Agents",
    "strategist":   "🐈 Strategist",
    "drafter":      "🧪 Drafter",
    "seo_architect":"🏗️ SEO Architect",
    "humanizer":    "✍️ Humanizer",
}

def write_memory(keyword, feedback_text, memory_type, target="all"):
    mem = []
    try:
        if os.path.exists(MEMORY_PATH):
            with open(MEMORY_PATH, "r") as f: mem = json.load(f)
    except: pass
    mem.append({
        "type": memory_type,
        "target": target,
        "feedback": feedback_text,
        "keyword": keyword,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    with open(MEMORY_PATH, "w") as f: json.dump(mem, f, indent=2)

# --- Tabs ---
t1, t2, t3 = st.tabs(["🚀 Generator", "📜 History", "🛠️ Admin"])

with t1:
    col1, col2 = st.columns([2, 1])
    with col1:
        kw = st.text_input("Target Keyword", placeholder="How to choose the perfect mattress...")
        special_instructions = st.text_area(
            "Special Instructions (optional)",
            placeholder="Examples:\n• Primary product: Ultima Natural Latex. Audience: back pain sufferers.\n• Festive sale angle — mention 30% off. Add comparison with Wakefit.\n• Tone: casual and witty. No medical claims.",
            height=90,
        )
        engine_choice = st.selectbox("Engine", models if models else ["No Keys Found"])
        if "Groq" in engine_choice:
            st.caption("⚡ Groq free tier: compact product DB used for Drafter (6K TPM limit). Full DB on paid providers.")
        generate_btn = st.button("🚀 Generate Blog Post", type="primary")

        # Resume banner — shown when a previous run failed mid-pipeline
        saved_cp = st.session_state.get("pipeline_checkpoint", {})
        resume_btn = False
        if saved_cp.get("failed_at"):
            stages_done = [k for k in ("serp", "brief", "draft", "opt") if saved_cp.get(k)]
            st.warning(
                f"⚡ **Checkpoint saved** — `{saved_cp['keyword']}` failed at **{saved_cp['failed_at']}** "
                f"(completed: {', '.join(stages_done) or 'none'}). "
                f"Switch your API key above, then Resume."
            )
            rc1, rc2 = st.columns([3, 1])
            with rc1:
                resume_btn = st.button("▶️ Resume Pipeline", type="secondary", use_container_width=True)
            with rc2:
                if st.button("✕ Discard", use_container_width=True):
                    st.session_state.pop("pipeline_checkpoint", None)
                    st.rerun()

    with col2:
        st.subheader("Knowledge Vault")
        st.write(f"📁 **Storage:** {len(os.listdir(VAULT_PATH))} articles archived.")
        st.info("Every generation is backed up to the SleepyCat GitHub Vault.")

    run_kw = kw
    is_resume = False
    if resume_btn and saved_cp.get("keyword"):
        run_kw = saved_cp["keyword"]
        is_resume = True

    if (generate_btn and kw) or (resume_btn and saved_cp.get("keyword")):
        if generate_btn and saved_cp.get("failed_at"):
            # Fresh generate clears any existing checkpoint
            st.session_state.pop("pipeline_checkpoint", None)
        final_content = run_pipeline(run_kw, engine_choice, resume=is_resume,
                                      special_instructions=special_instructions)
        if final_content:
            vault_file = save_to_vault(run_kw, final_content)
            log_generation(run_kw, st.session_state['user_email'], final_content, vault_file)
            st.markdown("---")
            st.markdown(final_content)
            st.download_button("Download Markdown", final_content, vault_file)

with t2:
    st.subheader("Recent Generations")
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r") as f:
                hist = json.load(f)
                for i in hist[::-1]:
                    with st.expander(f"[{i.get('timestamp')}] {i.get('keyword')} (by {i.get('user')})"):
                        st.markdown(i.get('content', '*No content archived.*'))
                        st.markdown("---")
                        st.write(f"**Status:** {i.get('status', 'Legacy')}")
                        if i.get('feedback'): st.info(f"**Feedback:** {i['feedback']}")
                        
                        iid = i.get('id')
                        status_val = i.get('status', 'Pending Review')
                        if iid and status_val == "Pending Review":
                            f1, f2 = st.columns(2)
                            with f1:
                                if st.button("👍 Approve", key=f"acc_{iid}"):
                                    update_feedback(iid, "Verified Quality", "Approved")
                                    st.rerun()
                            with f2:
                                if st.button("👎 Give Feedback", key=f"rej_{iid}"):
                                    st.session_state[f"fb_mode_{iid}"] = True
                            if st.session_state.get(f"fb_mode_{iid}", False):
                                good = st.text_area("What was good? (optional)", key=f"good_{iid}")
                                bad  = st.text_area("What was bad? (optional)",  key=f"bad_{iid}")
                                if st.button("Submit Feedback", key=f"sub_{iid}"):
                                    kw = i.get('keyword', '')
                                    if good.strip(): write_memory(kw, good.strip(), "positive")
                                    if bad.strip():  write_memory(kw, bad.strip(),  "negative")
                                    update_feedback(iid, (good + " | " + bad).strip(" |"), "Reviewed")
                                    st.session_state[f"fb_mode_{iid}"] = False
                                    st.rerun()
        except: st.error("History load error.")

with t3:
    st.subheader("Platform Administration")
    admin_code = st.text_input("Admin Passcode", type="password")
    if admin_code == "SleepyCat2026":
        st.success("Admin mode unlocked.")
        
        if st.button("🚀 Sync to GitHub Cloud Vault"):
            try:
                subprocess.run(["git", "config", "user.email", "admin@sleepycat.in"], check=True)
                subprocess.run(["git", "config", "user.name", "SleepyCat Admin"], check=True)
                subprocess.run(["git", "add", "outputs/*"], check=True)
                subprocess.run(["git", "add", "*.json"], check=True)
                subprocess.run(["git", "commit", "-m", f"Vault Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=True)
                subprocess.run(["git", "push", "origin", "master"], check=True)
                st.success("Successfully synced all articles to GitHub 100GB Vault!")
            except Exception as e: st.error(f"Sync Failed: {e}")
            
        # ── Memory Browser ──────────────────────────────────────────
        st.markdown("---")
        st.subheader("🧠 Agent Memory Browser")
        st.caption("Change routing to limit which agent a memory is injected into. Delete removes it permanently.")
        if os.path.exists(MEMORY_PATH):
            try:
                with open(MEMORY_PATH, "r") as f: mem_entries = json.load(f)
                if mem_entries:
                    pos_entries  = [(i, e) for i, e in enumerate(mem_entries) if e.get("type") == "positive"]
                    neg_entries  = [(i, e) for i, e in enumerate(mem_entries) if e.get("type") == "negative"]
                    routing_keys = list(ROUTING_OPTIONS.keys())
                    col_pos, col_neg = st.columns(2)

                    def _mem_card(real_idx, e, key_suffix):
                        with st.container(border=True):
                            st.caption(f"{e.get('timestamp')} · {e.get('keyword')}")
                            st.write(e.get("feedback"))
                            cur_target = e.get("target", "all")
                            r1, r2 = st.columns([3, 1])
                            with r1:
                                new_target = st.selectbox(
                                    "Route to", routing_keys,
                                    index=routing_keys.index(cur_target) if cur_target in routing_keys else 0,
                                    format_func=lambda x: ROUTING_OPTIONS[x],
                                    key=f"route_{key_suffix}_{real_idx}"
                                )
                                if new_target != cur_target:
                                    if st.button("💾 Save routing", key=f"save_route_{key_suffix}_{real_idx}"):
                                        mem_entries[real_idx]["target"] = new_target
                                        with open(MEMORY_PATH, "w") as f: json.dump(mem_entries, f, indent=2)
                                        st.rerun()
                            with r2:
                                if st.button("🗑️", key=f"del_mem_{key_suffix}_{real_idx}", help="Delete"):
                                    mem_entries.pop(real_idx)
                                    with open(MEMORY_PATH, "w") as f: json.dump(mem_entries, f, indent=2)
                                    st.rerun()

                    with col_pos:
                        st.markdown(f"**✅ Positive ({len(pos_entries)})**")
                        for real_idx, e in reversed(pos_entries):
                            _mem_card(real_idx, e, "p")
                    with col_neg:
                        st.markdown(f"**❌ Negative ({len(neg_entries)})**")
                        for real_idx, e in reversed(neg_entries):
                            _mem_card(real_idx, e, "n")
                else:
                    st.info("No agent memories yet. Submit feedback from the History tab to build memory.")
            except Exception as e:
                st.error(f"Memory load error: {e}")
        else:
            st.info("No agent memories yet. Submit feedback from the History tab to build memory.")

        # ── History Management ───────────────────────────────────────
        st.markdown("---")
        st.subheader("🗂️ History Management")
        if os.path.exists(HISTORY_PATH):
            try:
                with open(HISTORY_PATH, "r") as f: hist_all = json.load(f)
                if hist_all:
                    for entry in reversed(hist_all):
                        eid = entry.get("id")
                        h1, h2 = st.columns([6, 1])
                        with h1:
                            status_icon = {"Approved": "✅", "Reviewed": "💬", "Pending Review": "⏳"}.get(entry.get("status"), "—")
                            st.write(f"{status_icon} `{entry.get('timestamp')}` — **{entry.get('keyword')}** · {entry.get('user')}")
                        with h2:
                            if st.button("🗑️", key=f"del_hist_{eid}", help="Delete this entry"):
                                hist_all = [e for e in hist_all if e.get("id") != eid]
                                with open(HISTORY_PATH, "w") as f: json.dump(hist_all, f, indent=2)
                                st.rerun()
                else:
                    st.info("No history entries.")
            except Exception as e:
                st.error(f"History load error: {e}")
        else:
            st.info("No history entries yet.")

    elif admin_code: st.error("Incorrect code.")
