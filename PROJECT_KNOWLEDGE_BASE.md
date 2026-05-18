# 🐈 SleepyCat SEO Platform: 360° Knowledge Base (v6.0)

## 1. Project Mission
To transform SleepyCat’s content strategy from "AI-assisted drafting" to a "Data-Driven, Multi-Agent SEO Factory." The platform generates AEO-optimized (Answer Engine Optimization) blog posts grounded in real-time competitor data and verified product specs, ensuring E-E-A-T (Experience, Expertise, Authoritativeness, and Trustworthiness) at scale.

---

## 2. Technical Architecture: The 5-Agent Pipeline
The system utilizes a sequential hand-off model where specialized agents perform discrete tasks:

1.  **🕵️ The SERP Spy (Agent 1):** Scrapes the Top 3 Google results for the target keyword in real-time. Identifies competitor headings, content gaps, and structural trends.
2.  **🐈 The Brand Strategist (Agent 2):** Injects SleepyCat’s Brand DNA. Cross-references competitor weaknesses with our specific product USPs (spinal alignment, breathability, certifications).
3.  **🧪 The Lab Tester / Drafter (Agent 3):** Drafts the factual core. Enforces the "Anti-Jargon" rule (No Density/ILD; Use 'Feel/Materials'). Uses the **Brand Final Formula**.
4.  **🏗️ The SEO Architect (Agent 4):** Optimizes for AEO snippets (40-50 word direct answers) and semantic search. Inserts valid markdown comparison tables and internal SleepyCat links.
5.  **✍️ The Senior Editor / Humanizer (Agent 5):** Final pass to remove AI cliches. Ensures the tone is professional, sharp, and authoritative.

---

## 3. Key Enterprise Features
-   **AEO-First Content:** Every post includes a 40-50 word direct answer designed to win Google's "Featured Snippets."
-   **Zero-Fabrication Data:** Hard-wired to `sleepycat-products.json`. The agents cannot hallucinate specs; they only use verified data.
-   **Model-Agnostic Engine:** Powered by LiteLLM. Supports Gemini 2.5, Claude 3.5 Sonnet, and GPT-4o with automatic company-to-personal failover.
-   **Enterprise Security:** Restricted to `@sleepycat.in` via Google OAuth.
-   **The Knowledge Vault:** Automatic archival of all generations to a GitHub repository (100GB+ persistent storage).
-   **RLHF Memory Loop:** Admins can "Reject" content and update the agent's long-term memory to avoid repeating mistakes.

---

## 4. Platform Evolution (Changelog Summary)
-   **v1.0-v3.0:** Transitioned from a single creative script to a modular 5-agent orchestrator.
-   **v4.0:** Migrated from local execution to a hosted Streamlit Cloud platform.
-   **v5.0:** Implemented Enterprise OAuth and the GitHub Archival system.
-   **v5.8 (Current):** Ultra-Performance overhaul. Parallelized scraping and optimized context loading. Generation time reduced from 15+ mins to **< 2 mins**.

---

## 5. Deployment Specs
-   **Frontend:** Streamlit
-   **Backend:** Python 3.12 (uv)
-   **Hosting:** Streamlit Cloud
-   **Auth:** Google OAuth v2 (Restricted Domain)
-   **Repository:** `https://github.com/acovrp/sleepycat-seo-platform`

---
*Created by Gemini CLI & SleepyCat Team - May 2026*

---

## 6. Agent Prompt Specifications (v5.9)

Each agent's system prompt is defined in `sleepycat_seo_agent.py`. This section documents the intended behaviour so future edits don't regress content quality.

### Agent 1 — SERP Spy
- Scrapes **3 URLs** (up from 2), 3s timeout
- Extracts: H2/H3 headings (up to 6) + first 2 paragraph previews (150 chars each)
- Output: raw competitor structure passed to Strategist

### Agent 2 — Brand Strategist
- Produces a **structured strategy brief** with 6 sections: Article Angle, Target Reader, H2 Structure (5-6 headings), Key Product Pushes, Content Gaps, Tone Note
- Has full brand DNA + product DB in system prompt
- Temperature: 0.7 (creative angles needed)

### Agent 3 — Lab Tester / Drafter
- Writes **1000-1500 word full draft** following the Brand Final Formula
- Formula: Hook → 4-5 H2 sections → "Why SleepyCat?" section → CTA closing
- Anti-jargon enforced: no ILD/density/coil count — use feel/materials/support
- Temperature: 0.4 (factual but natural)
- Uses only verified specs from product_catalog.json

### Agent 4 — SEO Architect
- **Does NOT shorten the article** — common regression point
- Adds 40-50 word AEO snippet immediately after H1 (bold, direct answer)
- Adds/improves comparison table with: Mattress | Technology | Key Benefit | Firmness | Best For | Link
- Adds internal links: Ultima/Original/Ortho → sleepycat.in/products/{name}
- Temperature: 0.1 (precise, structural)

### Agent 5 — Senior Editor / Humanizer
- Receives full humanizer_rules.txt content as system prompt
- Must preserve ALL content — tables, links, AEO snippet, length (1000+ words)
- Temperature: 0.5

---

## 7. File Map

| File | Purpose | Used By |
|------|---------|---------|
| `brand_guidelines.txt` | Full SleepyCat brand DNA (2500 chars) | Strategist, Drafter |
| `humanizer_rules.txt` | Voice/tone rules for final pass | Humanizer |
| `product_catalog.json` | `{"ProductName": {tech, benefit, firmness, target}}` | Strategist, Drafter, SEO Architect |
| `agent_memory.json` | RLHF feedback loop (last 3 entries used) | All agents as negative constraints |
| `generation_history.json` | Archive of all successful generations | History tab |

---

## 8. Changelog

| Version | Date | Change |
|---------|------|--------|
| v5.9 | May 2026 | Rewrote all 5 agent system prompts. Strategist now produces structured brief. Drafter outputs 1000-1500 words using Brand Final Formula. SEO Architect no longer shortens content — adds AEO snippet at top instead. Humanizer given full rules. SERP scraper upgraded to 3 URLs. Fixed product_catalog.json loading (was looking for sleepycat-products.json). Fixed multi-provider support: Gemini, Claude 4.x, GPT-4o, Kimi. MODEL_MAP separates display names from litellm model IDs. |
| v5.8 | May 2026 | Ultra-Performance overhaul by Gemini CLI. Reduced generation time. (Note: gutted agent prompts — caused short/generic output, fixed in v5.9) |
| v5.0 | May 2026 | Google OAuth, Streamlit Cloud hosting, @sleepycat.in domain restriction |
