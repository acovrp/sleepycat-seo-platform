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
