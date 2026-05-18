import streamlit as st
import os
import json
from datetime import datetime

# ==========================================
# SleepyCat SEO Platform (v3.0 - Hosted)
# Frontend: Streamlit with Cloud-Path Fixes
# ==========================================

st.set_page_config(page_title="SleepyCat SEO Engine", page_icon="🐈", layout="wide")

# Force Absolute Path Resolution for Cloud
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE_PATH, "agent_memory.json")

# Ensure UI renders BEFORE heavy imports
st.title("🐈 SleepyCat Multi-Agent SEO Engine")

# Lazy load the Orchestrator to prevent startup hangs
def get_orchestrator(model):
    try:
        from sleepycat_seo_agent import Orchestrator
        return Orchestrator(model=model)
    except Exception as e:
        st.error(f"Failed to initialize Agents: {e}")
        return None

# Admin Settings
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def admin_login():
    with st.sidebar:
        st.header("🔑 Admin Console")
        passcode = st.text_input("Enter Dept Head Passcode", type="password")
        if passcode == "SleepyCat2026":
            st.session_state['authenticated'] = True
            st.success("Authenticated!")
        elif passcode:
            st.error("Incorrect Passcode")
        
        if st.session_state['authenticated']:
            st.markdown("---")
            st.subheader("🧠 Active Memory")
            if os.path.exists(MEMORY_PATH):
                try:
                    with open(MEMORY_PATH, "r") as f:
                        mems = json.load(f)
                        for m in mems[-5:]:
                            st.caption(f"[{m['timestamp']}] {m['feedback']}")
                except:
                    st.write("Error reading memory.")
            else:
                st.write("Memory is empty.")

admin_login()

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🚀 Content Generator")
    keyword = st.text_input("Enter Target Keyword", placeholder="e.g., Best mattress for back pain in India")
    
    model_choice = st.selectbox(
        "Primary AI Model",
        ["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro", "anthropic/claude-3-5-sonnet", "openai/gpt-4o"],
        index=0
    )
    
    generate_btn = st.button("Generate Blog Post", type="primary")

with col2:
    st.subheader("📝 Branding Summary")
    st.info("Structure: Brand Final Formula\nData: 69 Products Connected\nMode: No-Jargon AEO")

# Orchestration Flow
if generate_btn and keyword:
    orchestrator = get_orchestrator(model=model_choice)
    
    if orchestrator:
        with st.status("Agents are working...", expanded=True) as status:
            try:
                st.write("🕵️ SERP Spy: Scraping live competitor data...")
                serp_data = orchestrator.serp_agent.execute_task(keyword)
                
                st.write("🐈 Brand Strategist: Loading Memory & Weaponizing DNA...")
                feedback_mem = orchestrator._load_memory()
                strategy_brief = orchestrator.strategist.execute_task(f"Target: {keyword}\nData: {serp_data}", feedback_mem)
                
                st.write("🧪 Lab Tester: Drafting factual content...")
                draft = orchestrator.drafter.execute_task(strategy_brief, orchestrator.filtered_products, feedback_mem)
                
                st.write("🏗️ SEO Architect: Optimizing for AEO snippets...")
                optimized_draft = orchestrator.seo_editor.execute_task(draft, keyword, orchestrator.filtered_products, feedback_mem)
                
                st.write("✍️ Senior Editor: Applying human touch...")
                final_content = orchestrator.humanizer.execute_task(optimized_draft, feedback_mem)
                
                status.update(label="Workflow Complete!", state="complete", expanded=False)
                
                st.markdown("---")
                st.subheader("📄 Generated Content")
                st.markdown(final_content)
                
                st.download_button(
                    label="Download Markdown File",
                    data=final_content,
                    file_name=f"{keyword.replace(' ', '_')}.md",
                    mime="text/markdown"
                )
            except Exception as e:
                st.error(f"Workflow failed: {e}")
                status.update(label="Workflow Failed", state="error")

        # Feedback Loop (Simplified)
        st.markdown("---")
        st.subheader("🧐 Review Output")
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            if st.button("✅ Accept Output"):
                st.success("Great! Content marked as ready for publishing.")
        
        with f_col2:
            if st.button("❌ Reject Output"):
                st.session_state['show_feedback'] = True

        if st.session_state.get('show_feedback', False):
            feedback_text = st.text_area("Why? (e.g., used jargon, tone too robotic)")
            if st.button("Submit Feedback"):
                new_mem = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "keyword": keyword,
                    "feedback": feedback_text
                }
                mems = []
                try:
                    if os.path.exists(MEMORY_PATH):
                        with open(MEMORY_PATH, "r") as f:
                            mems = json.load(f)
                    mems.append(new_mem)
                    with open(MEMORY_PATH, "w") as f:
                        json.dump(mems, f, indent=2)
                    st.info("Feedback logged.")
                    st.session_state['show_feedback'] = False
                except:
                    st.error("Could not save feedback.")

# Admin Logic
if st.session_state['authenticated']:
    st.markdown("---")
    st.subheader("🛠️ Admin Controls")
    
    try:
        guideline_path = os.path.join(BASE_PATH, "brand_guidelines.txt")
        with open(guideline_path, "r") as f:
            current_dna = f.read()
        new_dna = st.text_area("Brand DNA", value=current_dna, height=300)
        if st.button("Overwrite Guidelines"):
            with open(guideline_path, "w") as f:
                f.write(new_dna)
            st.success("Guidelines updated.")
    except:
        st.error("Could not load brand guidelines.")
