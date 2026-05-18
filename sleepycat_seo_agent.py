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
# Engine v5.8 (Ultra-Performance)
# ==========================================

class BaseAgent:
    def __init__(self, name, role_description, temperature=0.7, primary_model="gemini/gemini-1.5-flash"):
        self.name = name
        self.role_description = role_description
        self.temperature = temperature
        self.primary_model = primary_model
        
    def execute_task(self, prompt_context, negative_constraints=""):
        print(f"  [Agent: {self.name}] Started...")
        full_system = f"{self.role_description}\n\nNEGATIVES:\n{negative_constraints}" if negative_constraints else self.role_description
        messages = [{"role": "system", "content": full_system}, {"role": "user", "content": prompt_context}]
        
        try:
            response = litellm.completion(model=self.primary_model, messages=messages, temperature=self.temperature, timeout=60)
            return response.choices[0].message.content
        except Exception as e:
            print(f"    Error in {self.name}: {e}")
            return f"Agent {self.name} failed."


class SERPScraperAgent:
    """Agent 1: Competition Analysis - Aggressive Timeouts"""
    def __init__(self):
        self.name = "The SERP Spy"
        
    def _scrape_url(self, url):
        try:
            # High speed 2s timeout
            res = requests.get(url, timeout=2, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code != 200: return None
            soup = BeautifulSoup(res.text, 'html.parser')
            headings = [h.get_text().strip() for h in soup.find_all(['h2', 'h3'])[:5]]
            return f"Source: {url} | Content: {', '.join(headings)}"
        except:
            return None

    def execute_task(self, keyword):
        print(f"  [Agent: {self.name}] Parallel Scraping...")
        try:
            # Reduced to 2 URLs for instant results
            urls = list(search(f"{keyword} India", num_results=2))
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(self._scrape_url, urls))
            valid = [r for r in results if r]
            return "\n".join(valid) if valid else "No SERP data."
        except:
            return "SERP error."

class BrandStrategistAgent(BaseAgent):
    def __init__(self, brand_dna, product_db, tech, model):
        super().__init__("Strategist", f"D2C DNA: {brand_dna}\nTECH: {tech}", 0.7, model)
        self.db = product_db
    def execute_task(self, context, neg=""):
        return super().execute_task(f"{context}\n\nDB: {json.dumps(self.db, indent=1)}", neg)

class ReviewerPersonaAgent(BaseAgent):
    def __init__(self, tech, model):
        super().__init__("Drafter", f"Follow Formula. No jargon. TECH: {tech}", 0.2, model)
    def execute_task(self, brief, db, neg=""):
        return super().execute_task(f"BRIEF: {brief}\n\nDB: {json.dumps(db, indent=1)}", neg)

class SEOEditorAgent(BaseAgent):
    def __init__(self, model):
        super().__init__("SEO Architect", "AEO Snippet 40-50 words. Comparison table. Markdown links.", 0.1, model)
    def execute_task(self, draft, keyword, db, neg=""):
        return super().execute_task(f"KEYWORD: {keyword}\nDB: {json.dumps(db, indent=1)}\nDRAFT: {draft}", neg)

class HumanizerAgent(BaseAgent):
    def __init__(self, rules, model):
        super().__init__("Editor", f"Tone: {rules}. Remove AI cliches.", 0.5, model)


class Orchestrator:
    def __init__(self, model="gemini/gemini-1.5-flash"):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        dna = self._read(os.path.join(self.base_path, "brand_guidelines.txt"))[:2000]
        humanizer_rules = self._read(os.path.join(self.base_path, "humanizer_rules.txt"))[:1000]
        raw = self._json(os.path.join(self.base_path, "product_catalog.json"))

        # product_catalog.json is {"ProductName": {tech, benefit, firmness, target}, ...}
        self.products = [{"name": k, **v} for k, v in raw.items()]

        self.serp_agent = SERPScraperAgent()
        self.strategist = BrandStrategistAgent(dna, self.products, dna, model)
        self.drafter = ReviewerPersonaAgent(dna, model)
        self.seo_editor = SEOEditorAgent(model)
        self.humanizer = HumanizerAgent(humanizer_rules or "Professional & Human", model)

    def _read(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f: return f.read()
        except: return ""

    def _json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except: return {"products": []}

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
        
        serp = self.serp_agent.execute_task(keyword)
        brief = self.strategist.execute_task(f"Target: {keyword}\nSERP: {serp}", mem)
        draft = self.drafter.execute_task(brief, self.products, mem)
        opt = self.seo_editor.execute_task(draft, keyword, self.products, mem)
        final = self.humanizer.execute_task(opt, mem)
        
        dur = round(time.time() - start, 1)
        print(f"✅ Finished in {dur}s")
        return final, dur
