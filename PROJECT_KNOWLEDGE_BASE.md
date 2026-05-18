# 🐈 SleepyCat SEO Platform: 360° Knowledge Base (v7.3)

## 1. Project Mission
To transform SleepyCat’s content strategy from "AI-assisted drafting" to a "Data-Driven, Multi-Agent SEO Factory." The platform generates 1000-1500 word AEO-optimized blog posts grounded in real-time competitor data and verified product specs (E-E-A-T).

---

## 2. Technical Architecture: The 5-Agent Pipeline
The system uses a sequential hand-off model with a **single API pass** (v7.0+):

1.  **🕵️ The SERP Spy (Agent 1):** Two-pass DDG scrape — competitor domains first, generic fallback second. Domain-deduplicated (1 result per brand). Collects: meta, H1, H2/H3 (×8), 4 paragraphs, bold claims per URL. No LLM API call.
2.  **🐈 The Brand Strategist (Agent 2):** Produces a 7-section brief including a `PRODUCT_SLUGS: ["slug-1", ...]` JSON array. Matches product material type to keyword intent (foam keyword → foam products; latex → latex; comparison → both; pillow keyword → no mattresses).
3.  **🧪 The Lab Tester / Drafter (Agent 3):** Writes a 1500-word draft using only the 3–5 products selected by the Strategist (not the full 69-product DB). Anti-Jargon enforced.
4.  **🏗️ The SEO Architect (Agent 4):** Optimizes for AEO. Adds 40-50 word bold snippets, comparison tables, and internal links. **Does not shorten.**
5.  **✍️ The Senior Editor / Humanizer (Agent 5):** Final pass for brand soul. Preserves all AEO/SEO structures.

**Display pass (app.py):** Only Agent 1 runs for display. Agents 2–5 show ⏳ status placeholders only — no API calls. All LLM work happens once inside `engine.run()` with per-agent memory injection.

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
- Produces a **structured strategy brief** with 7 sections: Article Angle, Target Reader, H2 Structure (5-6 headings), Key Product Pushes (1 primary + up to 4 secondary), Content Gaps, Tone Note, **PRODUCT_SLUGS**
- `PRODUCT_SLUGS: ["slug-1", "slug-2"]` — exact slugs of chosen products, valid JSON array
- Material-type matching: foam keyword → foam products; latex → latex; comparison → both types; pillow/accessory keyword → no mattresses
- Receives enriched compact_products: name + slug + category + **material + firmness + best_for** + 150-char summary
- Temperature: 0.7 (creative angles needed)

### Agent 3 — Lab Tester / Drafter
- Writes **1000-1500 word full draft** following the Brand Final Formula
- Formula: Hook → 4-5 H2 sections → "Why SleepyCat?" section → CTA closing
- Anti-jargon enforced: no ILD/density/coil count — use feel/materials/support
- Temperature: 0.4 (factual but natural)
- Receives only the **3–5 products selected by Strategist** (full specs from sleepycat-products.json) — not all 69. `_select_products(brief)` parses `PRODUCT_SLUGS` and filters the DB. Falls back to compact_products if parsing fails.
- Groq exception: always gets compact_products (6K TPM hard limit)

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
| v7.3 | May 2026 | **(Claude) Smart product selection — Strategist picks slugs, Drafter gets only those.** Strategist prompt adds section 7: `PRODUCT_SLUGS: ["slug-1", ...]` — a JSON array of the 3–5 products chosen for this article. Material-type matching enforced in prompt (foam/latex/pillow). `compact_products` enriched with `material`, `firmness`, `best_for` so Strategist has signal beyond name/category. `_select_products(brief)` parses slugs, validates against DB, returns full-spec objects. Fallback to `compact_products` if JSON parse fails or no slugs match — pipeline never breaks. Drafter input drops from ~50K to ~3–5K tokens. Claude Sonnet cost per article: ~₹35 → ~₹5. Company key (10K TPM) now works — no single agent exceeds the limit. |
| v7.2 | May 2026 | **(Claude) Rate limit auto-retry.** `execute_task()` retries up to 3 attempts on any 429/rate_limit/RESOURCE_EXHAUSTED error. Parses "retry in Xs" from the API error message, sleeps delay+5s (capped at 90s), then retries transparently. Covers Claude TPM limits (personal 30K/min, company 10K/min) and Gemini free-tier daily quota. Pipeline self-recovers without user intervention. |
| v7.1 | May 2026 | **(Claude) Active-agent highlight + live per-agent token/INR tracking.** `engine.run()` now accepts `progress_callback(agent, status, ctx, out)`. App creates `st.empty()` placeholders per agent: ⏳ waiting → **⚙️ bold** (active) → ✅ done (N words). `_track(ctx, out)` called on each "done" event so token count and INR cost accumulate live. Cost displayed in INR (not USD). Removed the ×2 multiplier — single-pass now, so estimate reflects one real pass. |
| v7.0 | May 2026 | **(Claude) Single-pass API architecture + SERP domain deduplication.** Display pass no longer calls Claude/Gemini/GPT for agents 2–4 — eliminated the duplicate API calls that caused org rate limit errors (10K/30K TPM). Agents 2–5 show status lines only; `engine.run()` is the sole LLM execution path. Checkpoint now saves only `serp` (brief/draft/opt no longer populated from display pass). SERP: added `seen_domains` set via `urlparse` — prevents 3 results from same brand; Pass 1 max_results 5→8, Pass 2 8→10. |
| v6.9 | May 2026 | **(Claude) Token cost tracker + special instructions.** Running token estimate updates after each agent during display pass; final card shows total tokens × 2 (display + quality pass) + cost in INR. PRICING dict covers all 9 supported models (Groq shows FREE). Special instructions text area below Target Keyword — injected into all 5 agents via `agent.special_instructions` instance var → `_build_system()`. |
| v6.8 | May 2026 | **(Claude) Two-pass SERP + rich page scraping.** Pass 1 targets competitor domains (The Sleep Company, Wakefit, Duroflex, Kurlon, Sunday + 6 more) via DDG `site:` filter. Pass 2 generic fallback with YouTube/Reddit/Amazon blacklist. Scraper now collects: meta description, H1, H2/H3 (8), first 4 paragraphs, bold claims per URL. |
| v6.7 | May 2026 | **(Claude) SERP fix + SEO Architect repetition fix.** Replaced `googlesearch-python` with `ddgs` (DuckDuckGo) — Google was returning a JS challenge page, silently giving 0 results. SEO Architect temperature raised 0.1→0.3 to prevent Gemini repetition loops. `stream_task()` now catches `MidStreamFallbackError` and silently retries non-streaming at +0.2 temperature before failing. |
| v6.6 | May 2026 | **(Claude) Per-agent memory routing + history delete.** Each memory entry gets a `target` field (`all`/`strategist`/`drafter`/`seo_architect`/`humanizer`). Admin can reroute entries in Memory Browser. `_load_memory(agent_name)` filters by target. `Orchestrator.run()` loads separate memory per agent. Admin History Management section with per-entry delete. |
| v6.5 | May 2026 | **(Claude) Live session checkpoint.** Pipeline saves each agent output to `st.session_state["pipeline_checkpoint"]`. On failure: Resume banner appears with stages completed. User switches API key, hits Resume — pipeline continues from the failed stage. `Orchestrator.run()` accepts `checkpoint=` to skip already-completed stages in the quality pass. |
| v6.4 | May 2026 | **(Claude) Streaming display + tiered context + 180s timeout.** Token-by-token streaming for agents 2–4 via `stream_task()`. Tiered product context: compact for Strategist, full 69-product JSON for Drafter, seo-trim for SEO Architect. Timeout 90s → 180s. Error propagation: pipeline exits early on any failure, shows `st.error()`. Admin Memory Browser replaces broken Rejected queue. |
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
| `app.py` only runs Agent 1 (SERP) in the display pass; `engine.run()` executes agents 2–5 | Was double-execution until v7.0. Removed because it triggered org rate limits (10K–30K TPM) — the Drafter alone sends ~50K input tokens (full product DB). Display pass now shows ⏳ status placeholders for agents 2–5 with no API calls. `engine.run()` is the single LLM execution path with full memory injection. `progress_callback` updates the placeholders live. |
| RLHF memory writes always include `"type": "positive"` or `"type": "negative"` | Typeless entries are silently ignored by `_load_memory()` — they neither help nor harm but waste the memory slot |
| `sleepycat-products.json` loaded via `raw.get("products", [])` | File is a wrapper dict `{generated_at, products: [...]}`, not a bare array or simple key→value dict |
| `product_catalog.json` kept in repo | 3-product backup. Not used by main pipeline. Useful for local testing without the full 202KB DB. |
| SEO Architect temperature is 0.3, not 0.1 | 0.1 causes Gemini to lock into a repetition loop of dashes on long structural tasks (2000+ word drafts). 0.3 is still precise enough for table/link work. |
| `stream_task()` catches `MidStreamFallbackError` and retries non-streaming | Gemini repetition loop raises this mid-stream. Retry at temp+0.2 recovers silently without failing the pipeline. |
| SERP uses `ddgs` (DuckDuckGo), not `googlesearch-python` | Google returns a JS challenge page to automated requests; `googlesearch-python` silently returns `[]`. DDG provides URL + title + body snippet reliably. |
| SERP uses `seen_domains` (not just `seen_urls`) for deduplication | Without domain-level dedup, Pass 1 competitor filter returned 3 pages from the same brand (e.g. all Springwel) — same domain just different article URLs. `urlparse(url).netloc.replace("www.", "")` ensures 3 different brands. |
| `engine.run()` accepts `progress_callback(agent, status, ctx, out)` | Callbacks from within a blocking call update `st.empty()` placeholders inside `st.status()` — Streamlit flushes these immediately. Do not remove the callback parameter; it drives both the active-agent highlight and the per-agent token tracking. |
| `execute_task()` retries up to 3× on rate limit errors with parsed delay | Rate limits return "retry in Xs" in the error body. Parsing this and sleeping prevents unnecessary permanent failures. Cap is 90s to avoid hanging the pipeline for daily-quota errors (Gemini free tier) where retrying is futile after 2 attempts. |
| `_select_products()` always has a fallback to `compact_products` | If the Strategist hallucinates a slug, produces malformed JSON, or omits the PRODUCT_SLUGS line entirely, `_select_products()` returns compact_products rather than raising an exception. Drafter still runs — just with less detail. Do not remove the fallback. |

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
| ~~Live agent stream~~ | ✅ Redesigned in v7.1 — `progress_callback` + `st.empty()` per-agent placeholders with ⏳→⚙️→✅ states. Streaming removed from display pass to fix rate limits. |
| ~~Drafter cost reduction~~ | ✅ Shipped in v7.3 — Strategist outputs `PRODUCT_SLUGS`, `_select_products()` filters to 3–5 full-spec products. Drafter input: ~50K → ~3–5K tokens. Claude Sonnet cost: ~₹35 → ~₹5 per article. Company key (10K TPM) now works. |

---

## 12. Live Session Checkpoint (v7.0+)

Saves the SERP result so a failed pipeline doesn't re-scrape competitors on resume.

```
run_pipeline() saves to st.session_state["pipeline_checkpoint"]:
  {
    "keyword": "best mattress india",
    "serp":  "...scraped data...",    # ✅ saved after Agent 1
    "failed_at": "pipeline"           # set if engine.run() fails
  }

On failure:
  → Resume banner shows: "SERP data: ✅ SERP. Switch key, then Resume."
  → User switches API key in sidebar
  → User clicks "▶️ Resume Pipeline"
  → run_pipeline(resume=True) skips SERP, passes saved serp to engine.run()
  → engine.run() runs agents 2–5 fresh with memory injection

On success:
  → st.session_state.pop("pipeline_checkpoint") — checkpoint cleared
```

**v7.0 regression vs v6.5:** Previously the checkpoint also saved `brief`, `draft`, `opt` from the display pass — so a failure at the Drafter could resume from Strategist output. Now that display pass makes no API calls, only `serp` is ever saved. If engine.run() fails mid-pipeline (e.g. at SEO Architect), user must restart agents 2–5 from scratch. Accepted trade-off: eliminates rate limit errors and halves token spend.

**Limitation:** `st.session_state` is per-browser-session. Closing or hard-refreshing the tab loses the checkpoint. File-based persistence not implemented (low priority — the rate-limit auto-retry in v7.2 makes mid-pipeline failures much rarer).

**Tiered context (v7.3):**
| Agent | Product data | Tokens (approx) | Why |
|-------|-------------|-----------------|-----|
| Strategist | enriched compact (name + slug + category + material + firmness + best_for + 150-char summary) | ~6K | Needs material/use-case fields to pick the right product type |
| **Drafter** | **3–5 selected full-spec products** (from `_select_products()`) | **~3–5K** | Only the products being featured — full specs, FAQs, certs |
| SEO Architect | seo-trim (name + slug + tech tags + certifications + firmness) | ~5K | Comparison table + internal links only |
| Humanizer | none | — | Editing prose only |
| Drafter (Groq) | compact (6K TPM hard limit) | ~4K | Groq can't handle even selected full specs within rate limit |

---

*v7.3 Build - May 2026*
