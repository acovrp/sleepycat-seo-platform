import os
import json
import re
import requests
import time
from bs4 import BeautifulSoup
from ddgs import DDGS
import litellm
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# ==========================================
# SleepyCat True Multi-Agent E-E-A-T System
# Engine v6.9 (domain dedup, single-pass API calls)
# ==========================================

class BaseAgent:
    def __init__(self, name, role_description, temperature=0.7, primary_model="gemini/gemini-1.5-flash"):
        self.name = name
        self.role_description = role_description
        self.temperature = temperature
        self.primary_model = primary_model

    def _build_system(self, negative_constraints="", positive_examples=""):
        parts = [self.role_description]
        si = getattr(self, "special_instructions", "")
        if si:
            parts.append(f"\nSPECIAL INSTRUCTIONS FOR THIS ARTICLE:\n{si}")
        if positive_examples:
            parts.append(f"\nWHAT WORKED WELL (keep doing this):\n{positive_examples}")
        if negative_constraints:
            parts.append(f"\nPAST FEEDBACK TO AVOID:\n{negative_constraints}")
        return "\n".join(parts)

    def execute_task(self, prompt_context, negative_constraints="", positive_examples=""):
        print(f"  [Agent: {self.name}] Started...")
        full_system = self._build_system(negative_constraints, positive_examples)
        messages = [{"role": "system", "content": full_system}, {"role": "user", "content": prompt_context}]
        for attempt in range(3):
            try:
                response = litellm.completion(model=self.primary_model, messages=messages, temperature=self.temperature, timeout=180)
                return response.choices[0].message.content
            except Exception as e:
                err = str(e)
                is_rate_limit = "rate_limit" in err.lower() or "429" in err or "RateLimitError" in err or "RESOURCE_EXHAUSTED" in err
                if is_rate_limit and attempt < 2:
                    m = re.search(r'retry[^\d]*(\d+(?:\.\d+)?)', err, re.IGNORECASE)
                    delay = min(int(float(m.group(1))) + 5, 90) if m else 65
                    print(f"  [{self.name}] Rate limit — retrying in {delay}s (attempt {attempt+1}/3)...")
                    time.sleep(delay)
                else:
                    print(f"    Error in {self.name}: {e}")
                    return f"Agent {self.name} failed: {e}"

    def stream_task(self, prompt_context, negative_constraints="", positive_examples=""):
        """Yields cumulative text as LLM generates. Falls back to non-streaming on Gemini repetition loops."""
        print(f"  [Agent: {self.name}] Streaming...")
        full_system = self._build_system(negative_constraints, positive_examples)
        messages = [{"role": "system", "content": full_system}, {"role": "user", "content": prompt_context}]
        try:
            response = litellm.completion(model=self.primary_model, messages=messages,
                                          temperature=self.temperature, timeout=180, stream=True)
            full_text = ""
            for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_text += delta
                    yield full_text
            if not full_text:
                yield f"Agent {self.name} returned empty response."
        except Exception as e:
            err = str(e)
            if "repeating the same chunk" in err or "MidStreamFallback" in err:
                # Gemini repetition loop — retry non-streaming at slightly higher temperature
                print(f"  [{self.name}] Repetition loop detected — retrying without streaming...")
                try:
                    fallback_temp = min(self.temperature + 0.2, 0.7)
                    response = litellm.completion(model=self.primary_model, messages=messages,
                                                  temperature=fallback_temp, timeout=180)
                    yield response.choices[0].message.content
                except Exception as e2:
                    yield f"Agent {self.name} failed: {e2}"
            else:
                yield f"Agent {self.name} failed: {e}"


def _is_error(text):
    """Returns True if the text is an agent failure message, not real content."""
    if not text:
        return True
    t = str(text).strip()
    return t.startswith("Agent ") and " failed:" in t


COMPETITOR_DOMAINS = [
    "thesleepcompany.in", "wakefit.co", "duroflex.com", "sunday.in",
    "kurlon.com", "sleepycat.in", "wakeup.in", "flo.health", "centuary.in",
    "morningsleepcompany.com", "peps.in", "springwel.com",
]
URL_BLACKLIST = [
    "youtube.com", "youtu.be", "reddit.com", "amazon.", "flipkart.",
    "quora.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "snapchat.com", "tiktok.com",
]

class SERPScraperAgent:
    """Agent 1: Two-pass DDG search (competitor blogs first, filtered fallback second) + rich page scraping."""
    def __init__(self):
        self.name = "The SERP Spy"

    def _scrape_page(self, url):
        """Scrapes meta description, H1, H2/H3, first 4 paragraphs, bold claims from a URL."""
        try:
            res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            if res.status_code != 200: return {}
            soup = BeautifulSoup(res.text, 'html.parser')

            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta_tag: meta_desc = (meta_tag.get("content") or "")[:200]

            h1 = next((h.get_text().strip() for h in soup.find_all('h1')[:1]), "")
            headings = [h.get_text().strip() for h in soup.find_all(['h2', 'h3'])[:8] if h.get_text().strip()]
            paras = [p.get_text().strip()[:200] for p in soup.find_all('p')[:4] if len(p.get_text().strip()) > 60]
            bold = list({b.get_text().strip() for b in soup.find_all(['strong', 'b'])
                         if 10 < len(b.get_text().strip()) < 120})[:5]

            return {"meta": meta_desc, "h1": h1, "headings": headings, "paras": paras, "bold": bold}
        except:
            return {}

    def _ddg_search(self, query, max_results=5):
        try:
            return DDGS().text(query, max_results=max_results) or []
        except:
            return []

    def _is_junk(self, url):
        return any(b in url for b in URL_BLACKLIST)

    def execute_task(self, keyword):
        print(f"  [Agent: {self.name}] Two-pass DDG search...")
        collected = []
        seen_domains = set()

        def _domain(url):
            return urlparse(url).netloc.replace("www.", "")

        # Pass 1: competitor blog targeting — 1 result per brand
        site_filter = " OR ".join(f"site:{d}" for d in COMPETITOR_DOMAINS)
        p1_results = self._ddg_search(f"{keyword} ({site_filter})", max_results=8)
        for r in p1_results:
            d = _domain(r['href'])
            if not self._is_junk(r['href']) and d not in seen_domains and len(collected) < 3:
                collected.append(r)
                seen_domains.add(d)

        # Pass 2: generic fallback — fill up to 3 if pass 1 came up short
        if len(collected) < 3:
            p2_results = self._ddg_search(f"{keyword} India mattress", max_results=10)
            seen_urls = {r['href'] for r in collected}
            for r in p2_results:
                d = _domain(r['href'])
                if not self._is_junk(r['href']) and r['href'] not in seen_urls and d not in seen_domains and len(collected) < 3:
                    collected.append(r)
                    seen_domains.add(d)
                    seen_urls.add(r['href'])

        if not collected:
            return "No real-time SERP data available."

        # Scrape each URL in parallel for rich page data
        urls = [r['href'] for r in collected]
        with ThreadPoolExecutor(max_workers=3) as executor:
            page_data = list(executor.map(self._scrape_page, urls))

        output = []
        for r, pd in zip(collected, page_data):
            lines = [f"URL: {r['href']}", f"Title: {r['title']}"]
            if pd.get("meta"):    lines.append(f"Meta: {pd['meta']}")
            if pd.get("h1"):      lines.append(f"H1: {pd['h1']}")
            if pd.get("headings"):lines.append(f"H2/H3: {' | '.join(pd['headings'])}")
            if pd.get("paras"):   lines.append(f"Content: {' // '.join(pd['paras'])}")
            if pd.get("bold"):    lines.append(f"Key claims: {' | '.join(pd['bold'])}")
            if not pd:            lines.append(f"Preview: {r['body'][:200]}")
            output.append("\n".join(lines))

        return "\n\n".join(output)


class BrandStrategistAgent(BaseAgent):
    """Agent 2: Produces a 6-section structured strategy brief."""
    def __init__(self, brand_dna, product_db, tech_glossary, model):
        system = f"""You are SleepyCat's Senior Brand Strategist. Produce a structured CONTENT STRATEGY BRIEF.

REQUIRED SECTIONS:
1. ARTICLE ANGLE: A unique hook that differentiates us from generic competitor jargon.
2. TARGET READER: Who is searching this and what is their specific pain point.
3. H2 STRUCTURE: 5-6 H2 section titles covering the topic comprehensively.
4. KEY PRODUCT PUSHES: Select 1 Primary + up to 4 Secondary products from the DB. Match material type to keyword intent (foam keyword → foam products; latex keyword → latex; comparison keyword → include both; pillow/accessory keyword → no mattresses).
5. CONTENT GAPS: What competitors missed that we will cover.
6. TONE NOTE: Specific voice guidance (Confident, Witty, Relatable Expert).
7. PRODUCT_SLUGS: Output the exact slugs of all chosen products as a JSON array.
   Format EXACTLY as: PRODUCT_SLUGS: ["slug-one", "slug-two", "slug-three"]
   Use only slugs present in the PRODUCT DB. No invented slugs.

BRAND DNA: {brand_dna[:2000]}
TECH GLOSSARY: {tech_glossary[:2000]}

RULES:
- Use real specs (AirGen™, 5-Zone Ortho, GOLS Latex).
- Do not fabricate any features.
- Angle must be 'The Art of Rest' vs 'Hustle Culture'.
- Section 7 PRODUCT_SLUGS must be valid JSON — the Drafter reads it programmatically."""
        super().__init__("Strategist", system, 0.7, model)
        self.db = product_db

    def execute_task(self, context, neg="", pos=""):
        return super().execute_task(f"{context}\n\nPRODUCT DB:\n{json.dumps(self.db, indent=1)}", negative_constraints=neg, positive_examples=pos)

    def stream_task(self, context, neg="", pos=""):
        yield from super().stream_task(f"{context}\n\nPRODUCT DB:\n{json.dumps(self.db, indent=1)}", negative_constraints=neg, positive_examples=pos)


class ReviewerPersonaAgent(BaseAgent):
    """Agent 3: Writes the full 1000-1500 word factual draft."""
    def __init__(self, brand_dna, tech_glossary, model):
        system = f"""You are SleepyCat's Technical Drafter. Write a complete first draft (1000-1500 words).

BRAND VOICE: Confident, witty, chilled. Never clinical. Use "we".
ANTI-JARGON: NEVER use ILD, density, coil count. Use "feel", "materials", "support".

CONTENT FORMULA:
1. Hook paragraph (Reader pain point, no fluff).
2. 3-4 Thematic H2 sections from strategy brief.
3. H2: Why SleepyCat? (Cite specific products & tech from DB).
4. FAQ Section: Harvest 'faq_specs' from the product DB verbatim.
5. Closing: Soft CTA (100-night trial).

REQUIREMENTS:
- Minimum 1000 words. 2-4 paragraphs per H2.
- NO FABRICATION. If it's not in the DB, don't write it.

GLOSSARY: {tech_glossary[:2000]}"""
        super().__init__("Drafter", system, 0.4, model)

    def execute_task(self, brief, db, neg="", pos=""):
        return super().execute_task(f"STRATEGY BRIEF:\n{brief}\n\nPRODUCT DB:\n{json.dumps(db, indent=1)}", negative_constraints=neg, positive_examples=pos)

    def stream_task(self, brief, db, neg="", pos=""):
        yield from super().stream_task(f"STRATEGY BRIEF:\n{brief}\n\nPRODUCT DB:\n{json.dumps(db, indent=1)}", negative_constraints=neg, positive_examples=pos)


class SEOEditorAgent(BaseAgent):
    """Agent 4: Optimizes for AEO snippets without shortening content."""
    def __init__(self, model):
        system = """You are SleepyCat's SEO Architect. Optimize for Google and AEO. DO NOT SHORTEN.

TASKS:
1. AEO SNIPPET: Add a 40-50 word bold direct-answer paragraph immediately after H1.
2. COMPARISON TABLE: Add/Improve table: | Mattress | Technology | Key Benefit | Firmness | Best For | Link |
3. INTERNAL LINKS: Link products to sleepycat.in/products/{slug}.
4. SEMANTIC SEARCH: Weave in 'spinal alignment', 'breathability', 'pressure relief'.

Final output must be 1000+ words."""
        super().__init__("SEO Architect", system, 0.3, model)

    def execute_task(self, draft, keyword, db, neg="", pos=""):
        return super().execute_task(f"TARGET: {keyword}\n\nPRODUCT DB:\n{json.dumps(db, indent=1)}\n\nDRAFT:\n{draft}", negative_constraints=neg, positive_examples=pos)

    def stream_task(self, draft, keyword, db, neg="", pos=""):
        yield from super().stream_task(f"TARGET: {keyword}\n\nPRODUCT DB:\n{json.dumps(db, indent=1)}\n\nDRAFT:\n{draft}", negative_constraints=neg, positive_examples=pos)


class HumanizerAgent(BaseAgent):
    """Agent 5: Final pass to apply brand soul."""
    def __init__(self, rules, model):
        system = f"""You are SleepyCat's Senior Editor. Apply final humanizing pass.

RULES: {rules}
- Preserve all tables, links, and the AEO snippet.
- Keep the length 1000+ words. Do not cut sections.
- Tone: Not just "AI clean" but "SleepyCat sharp"."""
        super().__init__("Editor", system, 0.5, model)


class Orchestrator:
    def __init__(self, model="gemini/gemini-1.5-flash"):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        dna = self._read(os.path.join(self.base_path, "brand_guidelines.txt"))
        tech = self._read(os.path.join(self.base_path, "sleepycat-tech-glossary.md"))
        rules = self._read(os.path.join(self.base_path, "humanizer_rules.txt"))
        raw = self._json(os.path.join(self.base_path, "sleepycat-products.json"))
        self.products = raw.get("products", []) if isinstance(raw, dict) else raw

        # Compact: enough for Strategist to pick the right product type + material + use-case
        self.compact_products = [
            {
                "name": p.get("product_name", ""),
                "slug": p.get("slug", ""),
                "category": p.get("category", ""),
                "material": p.get("key_technologies", p.get("technologies", [])),
                "firmness": p.get("firmness", ""),
                "best_for": p.get("best_for", ""),
                "summary": (p.get("description_short") or p.get("description", ""))[:150],
            }
            for p in self.products
        ]

        # SEO trim: enough for comparison table + internal links, not full specs
        self.seo_products = [
            {
                "name": p.get("product_name", ""),
                "slug": p.get("slug", ""),
                "category": p.get("category", ""),
                "technologies": p.get("technologies", p.get("key_technologies", [])),
                "certifications": p.get("certifications", []),
                "firmness": p.get("firmness", ""),
                "best_for": p.get("best_for", ""),
            }
            for p in self.products
        ]

        # Groq free tier: 6K TPM hard limit.
        # Drafter: _select_products() (3-5 full specs) on paid; compact on Groq.
        # SEO Architect: name+slug only (~700 tokens) on Groq — enough for internal links + table.
        self.is_groq = model.startswith("groq/")
        self.seo_arch_products = (
            [{"name": p.get("product_name", ""), "slug": p.get("slug", "")} for p in self.products]
            if self.is_groq else self.seo_products
        )

        self.serp_agent = SERPScraperAgent()
        self.strategist = BrandStrategistAgent(dna, self.compact_products, tech, model)
        self.drafter = ReviewerPersonaAgent(dna, tech, model)
        self.seo_editor = SEOEditorAgent(model)
        self.humanizer = HumanizerAgent(rules, model)

    def _read(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f: return f.read()
        except: return ""

    def _json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

    def _select_products(self, brief):
        """Parse PRODUCT_SLUGS from Strategist brief. Returns full-spec products for those slugs.
        Falls back to compact_products if parsing fails or no slugs match the DB."""
        try:
            m = re.search(r'PRODUCT_SLUGS:\s*(\[[\s\S]*?\])', brief)
            if not m:
                print("  [Orchestrator] No PRODUCT_SLUGS found — compact fallback")
                return self.compact_products
            slugs = json.loads(m.group(1))
            slug_set = {s.lower().strip() for s in slugs if isinstance(s, str)}
            selected = [p for p in self.products if p.get("slug", "").lower() in slug_set]
            if not selected:
                print(f"  [Orchestrator] No slug matches for {slugs} — compact fallback")
                return self.compact_products
            print(f"  [Orchestrator] Drafter gets {len(selected)} products: {[p.get('slug') for p in selected]}")
            return selected
        except Exception as e:
            print(f"  [Orchestrator] Slug parse error: {e} — compact fallback")
            return self.compact_products

    def _load_memory(self, agent_name=None):
        """Returns (positives_str, negatives_str) filtered to entries targeting this agent or 'all'."""
        try:
            p = os.path.join(self.base_path, "agent_memory.json")
            if os.path.exists(p):
                with open(p, "r") as f: m = json.load(f)
                if agent_name:
                    m = [i for i in m if i.get("target", "all") in ("all", agent_name)]
                pos = "\n".join([f"- {i['feedback']}" for i in m[-6:] if i.get('type') == 'positive'])
                neg = "\n".join([f"- {i['feedback']}" for i in m[-6:] if i.get('type') == 'negative'])
                return pos, neg
            return "", ""
        except: return "", ""

    def run(self, keyword, checkpoint=None, progress_callback=None):
        """Full quality pass with per-agent memory injection. Pass checkpoint to skip completed stages.

        progress_callback(agent, status, ctx, out) is called before ("running") and after ("done")
        each agent so the UI can highlight the active agent and accumulate token estimates.
        """
        start = time.time()
        print(f"\n🚀 Pipeline Start: {keyword}")
        cp = checkpoint or {}

        def _cb(agent, status, ctx="", out=""):
            if progress_callback:
                progress_callback(agent, status, ctx, out)

        serp = cp.get("serp") or self.serp_agent.execute_task(keyword)

        if not cp.get("brief"):
            pos, neg = self._load_memory("strategist")
            ctx = f"TARGET: {keyword}\nSERP: {serp}\n\nPRODUCT DB:\n{json.dumps(self.compact_products, indent=1)}"
            _cb("strategist", "running", ctx, "")
            brief = self.strategist.execute_task(f"TARGET: {keyword}\nSERP: {serp}", neg=neg, pos=pos)
            if _is_error(brief): return brief, round(time.time() - start, 1)
            _cb("strategist", "done", ctx, brief)
        else:
            brief = cp["brief"]

        # Select only the products Strategist recommended — Groq stays on compact (6K TPM limit)
        drafter_db = self.compact_products if self.is_groq else self._select_products(brief)

        if not cp.get("draft"):
            pos, neg = self._load_memory("drafter")
            ctx = f"STRATEGY BRIEF:\n{brief}\n\nPRODUCT DB:\n{json.dumps(drafter_db, indent=1)}"
            _cb("drafter", "running", ctx, "")
            draft = self.drafter.execute_task(brief, drafter_db, neg=neg, pos=pos)
            if _is_error(draft): return draft, round(time.time() - start, 1)
            _cb("drafter", "done", ctx, draft)
        else:
            draft = cp["draft"]

        if not cp.get("opt"):
            pos, neg = self._load_memory("seo_architect")
            ctx = f"TARGET: {keyword}\n\nPRODUCT DB:\n{json.dumps(self.seo_arch_products, indent=1)}\n\nDRAFT:\n{draft}"
            _cb("seo_architect", "running", ctx, "")
            opt = self.seo_editor.execute_task(draft, keyword, self.seo_arch_products, neg=neg, pos=pos)
            if _is_error(opt): return opt, round(time.time() - start, 1)
            _cb("seo_architect", "done", ctx, opt)
        else:
            opt = cp["opt"]

        pos, neg = self._load_memory("humanizer")
        _cb("humanizer", "running", opt, "")
        final = self.humanizer.execute_task(opt, negative_constraints=neg, positive_examples=pos)
        if _is_error(final): return final, round(time.time() - start, 1)
        _cb("humanizer", "done", opt, final)

        dur = round(time.time() - start, 1)
        return final, dur


if __name__ == "__main__":
    try:
        if os.isatty(0):
            target = input("Target Keyword: ")
            orchestrator = Orchestrator()
            content, dur = orchestrator.run(target)
            print(f"✅ Success in {dur}s")
        else: print("Non-interactive.")
    except Exception as e: print(f"Error: {e}")
