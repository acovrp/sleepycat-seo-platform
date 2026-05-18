import os
import json
import requests
import time
from bs4 import BeautifulSoup
from googlesearch import search
import litellm
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# SleepyCat True Multi-Agent E-E-A-T System
# Engine v5.9 (Full-Length Content Fix)
# ==========================================

class BaseAgent:
    def __init__(self, name, role_description, temperature=0.7, primary_model="gemini/gemini-1.5-flash"):
        self.name = name
        self.role_description = role_description
        self.temperature = temperature
        self.primary_model = primary_model

    def execute_task(self, prompt_context, negative_constraints=""):
        print(f"  [Agent: {self.name}] Started...")
        full_system = f"{self.role_description}\n\nPAST FEEDBACK TO AVOID:\n{negative_constraints}" if negative_constraints else self.role_description
        messages = [{"role": "system", "content": full_system}, {"role": "user", "content": prompt_context}]
        try:
            response = litellm.completion(model=self.primary_model, messages=messages, temperature=self.temperature, timeout=90)
            return response.choices[0].message.content
        except Exception as e:
            print(f"    Error in {self.name}: {e}")
            return f"Agent {self.name} failed: {e}"


class SERPScraperAgent:
    """Agent 1: Scrapes top 3 Google results for competitor headings and content structure."""
    def __init__(self):
        self.name = "The SERP Spy"

    def _scrape_url(self, url):
        try:
            res = requests.get(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code != 200: return None
            soup = BeautifulSoup(res.text, 'html.parser')
            headings = [h.get_text().strip() for h in soup.find_all(['h2', 'h3'])[:6]]
            paras = [p.get_text().strip()[:150] for p in soup.find_all('p')[:2] if len(p.get_text().strip()) > 50]
            content = ', '.join(headings)
            preview = ' | '.join(paras)
            return f"URL: {url}\nHeadings: {content}\nPreview: {preview}"
        except:
            return None

    def execute_task(self, keyword):
        print(f"  [Agent: {self.name}] Scraping top results...")
        try:
            urls = list(search(f"{keyword} India", num_results=3))
            with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(self._scrape_url, urls))
            valid = [r for r in results if r]
            return "\n\n".join(valid) if valid else "No SERP data available."
        except:
            return "SERP scraping failed."


class BrandStrategistAgent(BaseAgent):
    """Agent 2: Produces a structured content strategy brief."""
    def __init__(self, brand_dna, product_db, model):
        system = f"""You are SleepyCat's Brand Strategist. Given a target keyword, competitor SERP data, and SleepyCat's Brand DNA, produce a structured CONTENT STRATEGY BRIEF.

Your brief must include:
1. ARTICLE ANGLE: A unique hook that differentiates us from the generic competitor content
2. TARGET READER: Who is searching this keyword and what is their specific pain point
3. H2 STRUCTURE: 5-6 H2 section titles that cover the topic comprehensively and target semantic keywords
4. KEY PRODUCT PUSHES: Which SleepyCat products to feature and exactly WHY they solve the reader's problem (reference actual specs)
5. CONTENT GAPS: What the competitors are missing that we should cover
6. TONE NOTE: Specific voice guidance for this topic

BRAND DNA:
{brand_dna}

RULES:
- Every recommendation must be specific to SleepyCat's products and voice.
- Reference actual product specs (AirGen™ foam, 5-Zone Orthopedic, Open Cell Memory Foam).
- The angle must be distinct from generic "how to choose a mattress" articles.
- Do not fabricate any product features not listed in the product DB."""
        super().__init__("Strategist", system, 0.7, model)
        self.db = product_db

    def execute_task(self, context, neg=""):
        return super().execute_task(f"{context}\n\nPRODUCT DB:\n{json.dumps(self.db, indent=1)}", neg)


class ReviewerPersonaAgent(BaseAgent):
    """Agent 3: Writes the full 1000-1500 word factual draft."""
    def __init__(self, brand_dna, model):
        system = f"""You are SleepyCat's Lab Tester and Content Drafter. You write the complete first draft of a full-length SEO blog post (1000-1500 words).

BRAND VOICE RULES:
- Confident, witty, chilled. Never preachy or clinical.
- Anti-jargon: Never use ILD, density, coil count. Use "feel", "materials", "support" instead.
- Write as "we" (SleepyCat team). Reference "Test Subject 42" or "Lab Simulation A" for credibility.
- Vary sentence length: short punchy sentences after long technical ones.
- Forbidden openers: "In today's world", "When it comes to", "It is important to", "Furthermore", "In the realm of"

CONTENT FORMULA (follow this structure):
1. Hook paragraph (2-3 sentences, lead with the reader's pain point, no fluff)
2. H2: [First section from strategy brief]
3. H2: [Second section from strategy brief]
4. H2: [Third section from strategy brief]
5. H2: Why SleepyCat? (feature specific products with real specs from DB — name the product, its tech, its benefit)
6. H2: [Fourth/fifth section from strategy brief]
7. Closing paragraph with a soft CTA (try 100 nights risk-free)

OUTPUT REQUIREMENTS:
- Full markdown blog post, 1000-1500 words minimum
- Use ONLY product data from the DB — never fabricate specs
- Every H2 must have 2-4 paragraphs of substantive content

BRAND DNA REFERENCE:
{brand_dna[:1000]}"""
        super().__init__("Drafter", system, 0.4, model)

    def execute_task(self, brief, db, neg=""):
        return super().execute_task(f"STRATEGY BRIEF:\n{brief}\n\nPRODUCT DB:\n{json.dumps(db, indent=1)}", neg)


class SEOEditorAgent(BaseAgent):
    """Agent 4: Optimizes for AEO snippets and semantic SEO without shortening the article."""
    def __init__(self, model):
        system = """You are SleepyCat's SEO Architect. You receive a full draft blog post and optimize it for Google and Answer Engine Optimization (AEO). You must NOT shorten the article.

YOUR TASKS:
1. AEO SNIPPET: Immediately after the H1 title, add a 40-50 word direct-answer paragraph in bold. It must directly answer the keyword query in plain language. No fluff.
2. HEADINGS: Ensure H2s contain natural semantic keywords. Optimize for featured snippet eligibility.
3. COMPARISON TABLE: Add or improve a markdown product comparison table using only verified specs from the DB:
   | Mattress | Technology | Key Benefit | Firmness | Best For | Link |
4. INTERNAL LINKS: Link every product mention to its page:
   - Ultima → [Ultima](https://sleepycat.in/products/ultima)
   - Original → [Original](https://sleepycat.in/products/original)
   - Ortho → [Ortho](https://sleepycat.in/products/ortho)
5. PRESERVE LENGTH: Do not cut any sections. Final output must be 1000+ words.

Return the complete optimized article in markdown."""
        super().__init__("SEO Architect", system, 0.1, model)

    def execute_task(self, draft, keyword, db, neg=""):
        return super().execute_task(f"TARGET KEYWORD: {keyword}\n\nPRODUCT DB:\n{json.dumps(db, indent=1)}\n\nFULL DRAFT:\n{draft}", neg)


class HumanizerAgent(BaseAgent):
    """Agent 5: Final pass to apply brand voice and remove AI artifacts."""
    def __init__(self, rules, model):
        system = f"""You are SleepyCat's Senior Editor. Apply a final humanizing pass to this blog post.

HUMANIZER RULES:
{rules}

ADDITIONAL RULES:
- The article must read like it was written by a sharp SleepyCat team member, not an AI.
- Keep ALL content, comparison tables, internal links, and the AEO snippet intact.
- Final output must be 1000+ words. Do not cut any sections.
- Output the complete final article in markdown, ready to publish."""
        super().__init__("Editor", system, 0.5, model)


class Orchestrator:
    def __init__(self, model="gemini/gemini-1.5-flash"):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        dna = self._read(os.path.join(self.base_path, "brand_guidelines.txt"))[:2500]
        humanizer_rules = self._read(os.path.join(self.base_path, "humanizer_rules.txt"))[:1000]
        raw = self._json(os.path.join(self.base_path, "product_catalog.json"))

        # product_catalog.json: {"ProductName": {tech, benefit, firmness, target}, ...}
        self.products = [{"name": k, **v} for k, v in raw.items()]

        self.serp_agent   = SERPScraperAgent()
        self.strategist   = BrandStrategistAgent(dna, self.products, model)
        self.drafter      = ReviewerPersonaAgent(dna, model)
        self.seo_editor   = SEOEditorAgent(model)
        self.humanizer    = HumanizerAgent(humanizer_rules or "Write with sharp, witty SleepyCat voice. Remove all AI clichés.", model)

    def _read(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f: return f.read()
        except: return ""

    def _json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

    def _load_memory(self):
        try:
            p = os.path.join(self.base_path, "agent_memory.json")
            if os.path.exists(p):
                with open(p, "r") as f:
                    m = json.load(f)
                    return "\n".join([f"- {i['feedback']}" for i in m[-3:]])
            return ""
        except: return ""

    def run(self, keyword):
        start = time.time()
        print(f"\n🚀 Pipeline Start: {keyword}")
        mem = self._load_memory()

        serp   = self.serp_agent.execute_task(keyword)
        brief  = self.strategist.execute_task(f"TARGET KEYWORD: {keyword}\n\nCOMPETITOR SERP DATA:\n{serp}", mem)
        draft  = self.drafter.execute_task(brief, self.products, mem)
        opt    = self.seo_editor.execute_task(draft, keyword, self.products, mem)
        final  = self.humanizer.execute_task(opt, mem)

        dur = round(time.time() - start, 1)
        print(f"✅ Finished in {dur}s")
        return final, dur
