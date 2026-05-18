# 🐈 SleepyCat SEO Platform: 360° Knowledge Base (v6.3)

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

## 3. Key Enterprise Features (v6.2)
-   **Knowledge Vault:** Auto-archives every generation to `/outputs/`.
-   **Cloud Sync:** Admin-controlled button to push all local archival data to GitHub (100GB permanent storage).
-   **RLHF Two-Field Memory:** History tab lets users submit what was good (→ positive memory) and what was bad (→ negative memory). Both injected into all 5 agents on next run.
-   **Enterprise Security:** Domain-locked Google OAuth v2 (`@sleepycat.in`).
-   **Model-Agnostic Routing:** Supports Claude 4.x, Gemini 2.5, GPT-4o, and Kimi.
-   **Company Defaulting:** Prioritizes `COMPANY_CLAUDE_KEY` from secrets with session-based user fallback.

---

## 4. File Map & Environment
- `brand_guidelines.txt`: Core brand DNA.
- `sleepycat-products.json`: Verified spec source for 69 products (Production DB).
- `sleepycat-tech-glossary.md`: Proprietary tech definitions.
- `sleepycat-context.md`: High-level history and strategy deep-dive.
- `humanizer_rules.txt`: Voice/Tone constraints for the final pass.
- `outputs/`: Folder for auto-archived markdown files.


---

## 5. Deployment Specs
-   **URL:** `https://sleepycat-seo1.streamlit.app/`
-   **Passcode:** `SleepyCat2026` (Admin Tab)
-   **Repository:** `acovrp/sleepycat-seo-platform`

---

## 6. Agent Prompt Specifications (v5.9 Claude Suggestions)

Each agent's system prompt is defined in `sleepycat_seo_agent.py`. This section documents the intended behaviour so future edits don't regress content quality.

### Agent 1 — SERP Spy
- Scrapes **3 URLs**, 3s timeout
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
- Uses only verified specs from sleepycat-products.json (69 products, `products[]` array)

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

## 7. Changelog

| Version | Date | Change |
|---------|------|--------|
| v6.3 | May 2026 | **(Claude) Full audit.** Kimi key injection added (sidebar input + MOONSHOT_API_KEY env var). Unused deps removed (google-genai, python-dotenv, botocore). `claude_suggestions.md` merged into knowledge base. |
| v6.2 | May 2026 | **(Claude) RLHF Two-Field Memory.** `agent_memory.json` now stores `type: positive/negative`. History tab replaced with two-field feedback form. All 5 agents inject both "WHAT WORKED WELL" and "PAST FEEDBACK TO AVOID". Agent file updated to load `sleepycat-products.json` (69 products). Fixed Claude model names (`claude-sonnet-4-6`). |
| v6.1.1 | May 2026 | **Unified Aligned Build.** Merged Claude's v5.9 deep-content prompts. Restored Enterprise Cloud Sync, Knowledge Vault, and Admin controls. |
| v5.9 | May 2026 | (Claude Suggestion) Rewrote all 5 agent system prompts. Strategist now produces structured brief. Drafter outputs 1000-1500 words using Brand Final Formula. SEO Architect no longer shortens content — adds AEO snippet at top instead. |
| v5.8 | May 2026 | (Gemini CLI) Ultra-Performance overhaul. Reduced generation time to <2 mins. |
| v5.0 | May 2026 | Google OAuth, Streamlit Cloud hosting, @sleepycat.in domain restriction |

---

## 8. Architecture Decisions & Regression Guards

These decisions look wrong but are intentional. Do not revert them.

| Decision | Why |
|----------|-----|
| OAuth uses `st.link_button()`, not `st.markdown` with onclick | Streamlit's DOMPurify strips onclick handlers; `st.link_button()` is the only reliable external navigation |
| Claude model IDs: `claude-sonnet-4-6` / `claude-opus-4-7` | `claude-3-5-sonnet-latest` and `claude-3-5-sonnet-20241022` return not-found on the company Anthropic account |
| `app.py` calls agents 1–4 individually, then `engine.run()` re-executes all 5 | Double execution is intentional — individual calls drive UI progress steps; `engine.run()` produces the final output with full memory injection. Extra token cost accepted for quality. |
| RLHF memory writes always include `"type": "positive"` or `"type": "negative"` | Typeless entries are silently ignored by `_load_memory()` — they neither help nor harm but waste the memory slot |
| `sleepycat-products.json` loaded via `raw.get("products", [])` | File is a wrapper dict `{generated_at, products: [...]}`, not a bare array or simple key→value dict |
| `product_catalog.json` kept in repo | 3-product backup. Not used by main pipeline. Useful for local testing without the full 202KB DB. |

---

## 9. RLHF Memory Technical Flow

```
User submits feedback (History tab)
  → write_memory(keyword, text, "positive"|"negative")
  → appended to agent_memory.json as {type, feedback, keyword, timestamp}

Next generation (Orchestrator.run())
  → _load_memory() reads agent_memory.json
  → splits by type: last 6 positive entries, last 6 negative entries
  → returns (positives_str, negatives_str) tuple
  → all 5 agents receive both via execute_task():
      system prompt gets:
        "WHAT WORKED WELL (keep doing this):\n- ..."  [if positives exist]
        "PAST FEEDBACK TO AVOID:\n- ..."               [if negatives exist]
```

---

## 10. Verified Model IDs (Company Anthropic Account)

| Model ID | Status |
|----------|--------|
| `anthropic/claude-sonnet-4-6` | Works |
| `anthropic/claude-opus-4-7` | Works |
| `anthropic/claude-3-5-sonnet-latest` | Fails (not-found) |
| `anthropic/claude-3-5-sonnet-20241022` | Fails (not-found) |

---

## 11. Backlog

| Item | Detail |
|------|--------|
| Memory curation UI | Show `agent_memory.json` entries in Admin tab with delete button — no way to remove bad memories once written |
| Per-agent memory routing | Inject feedback only into the relevant agent (tone feedback → Humanizer; structure feedback → Strategist) |
| Memory count tuning | Currently last 6 per type; consider 3 positive + 3 negative = 6 total per generation |
| SERP timeout | 4s is tight for slow Indian domains — increase to 6s |
| History storage size | `generation_history.json` stores full article text per entry — will grow large; consider storing 500-char preview + vault filename only |
| Post-approval feedback | No way to give positive feedback after approving — "Leave a note" option would enable positive memory from approved articles |
| Live agent stream | Show token-by-token LLM output per agent during generation (litellm stream=True + st.empty() placeholder) |

---

*Unified v6.3 Build - May 2026*
