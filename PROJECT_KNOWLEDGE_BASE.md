# 🐈 SleepyCat SEO Platform: 360° Knowledge Base (v6.1)

## 1. Project Mission
To transform SleepyCat’s content strategy from "AI-assisted drafting" to a "Data-Driven, Multi-Agent SEO Factory." The platform generates 1000-1500 word AEO-optimized blog posts grounded in real-time competitor data and verified product specs (E-E-A-T).

---

## 2. Technical Architecture: The 5-Agent Pipeline
The system utilizes a sequential hand-off model:

1.  **🕵️ The SERP Spy (Agent 1):** Scrapes top 3 Google results + 150-char paragraph previews.
2.  **🐈 The Brand Strategist (Agent 2):** Produces a structured 6-section brief (Angle, Gaps, Tone, Product Pushes).
3.  **🧪 The Lab Tester / Drafter (Agent 3):** Writes a 1500-word draft following the Brand Final Formula. (Anti-Jargon enforced).
4.  **🏗️ The SEO Architect (Agent 4):** Optimizes for AEO. Adds 40-50 word bold snippets, comparison tables, and internal links. **Does not shorten.**
5.  **✍️ The Senior Editor / Humanizer (Agent 5):** Final pass for brand soul. Preserves all AEO/SEO structures.

---

## 3. Key Enterprise Features (v6.1 Merged)
-   **Knowledge Vault:** Auto-archives every generation to `/outputs/`.
-   **Cloud Sync:** Admin-controlled button to push all local archival data to GitHub (100GB permanent storage).
-   **RLHF Memory Review:** Dept Head can review rejections and update the agent's long-term brain (`agent_memory.json`).
-   **Enterprise Security:** Domain-locked Google OAuth v2 (`@sleepycat.in`).
-   **Model-Agnostic Routing:** Supports Claude 3.5/4.x, Gemini 2.5, GPT-4o, and Kimi.
-   **Company Defaulting:** Prioritizes `COMPANY_CLAUDE_KEY` from secrets with session-based user fallback.

---

## 4. File Map & Environment
-   `brand_guidelines.txt`: Core brand DNA.
-   `product_catalog.json`: Verified spec source for 69 products.
-   `humanizer_rules.txt`: Voice/Tone constraints for the final pass.
-   `outputs/`: Folder for auto-archived markdown files.

---

## 5. Deployment Specs
-   **URL:** `https://sleepycat-seo1.streamlit.app/`
-   **Passcode:** `SleepyCat2026` (Admin Tab)
-   **Repository:** `acovrp/sleepycat-seo-platform`

---
*Unified v6.1 Build - May 2026*
