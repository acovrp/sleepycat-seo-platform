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
# Engine v4.3 (Performance Optimized)
# ==========================================

class BaseAgent:
    """Base class for all specialized agents using LiteLLM."""
    def __init__(self, name, role_description, temperature=0.7, primary_model="gemini/gemini-1.5-flash"):
        self.name = name
        self.role_description = role_description
        self.temperature = temperature
        self.primary_model = primary_model
        
    def execute_task(self, prompt_context, negative_constraints=""):
        print(f"\n[Agent: {self.name}] Executing task...")
        
        full_system_instruction = self.role_description
        if negative_constraints:
            full_system_instruction += f"\n\nSTRICT NEGATIVE CONSTRAINTS (Based on user feedback):\n{negative_constraints}"
            
        messages = [
            {"role": "system", "content": full_system_instruction},
            {"role": "user", "content": prompt_context}
        ]
        
        try:
            response = litellm.completion(
                model=self.primary_model,
                messages=messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  - Error in {self.name}: {e}")
            raise e


class SERPScraperAgent:
    """Agent 1: Competition Analysis (SERP Spy) - PARALLEL"""
    def __init__(self):
        self.name = "The SERP Spy"
        
    def _scrape_url(self, url):
        try:
            res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code != 200: return None
            soup = BeautifulSoup(res.text, 'html.parser')
            headings = [h.get_text().strip() for h in soup.find_all(['h2', 'h3'])[:8]]
            title = soup.title.string if soup.title else "No Title"
            return f"Source: {url}\nTitle: {title}\nHeadings: {', '.join(headings)}"
        except:
            return None

    def execute_task(self, keyword):
        print(f"\n[Agent: {self.name}] Fast-Scraping results for: '{keyword}'...")
        try:
            query = f"{keyword} India"
            urls = list(search(query, num_results=3))
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(self._scrape_url, urls))
            
            valid_results = [r for r in results if r]
            if not valid_results:
                return "No real-time SERP data found. Falling back."
            
            return "\n\n".join(valid_results)
        except Exception as e:
            return f"SERP search failed: {e}"

class BrandStrategistAgent(BaseAgent):
    """Agent 2: Brand DNA Injector"""
    def __init__(self, brand_guidelines, product_db, tech_glossary, model):
        super().__init__(
            name="The Brand Strategist",
            primary_model=model,
            role_description=(
                "You are the Senior SleepyCat Brand Strategist. Weaponize Brand DNA against generic claims. \n\n"
                f"BRAND DNA:\n{brand_guidelines}\n\n"
                f"TECH GLOSSARY:\n{tech_glossary}\n\n"
                "1. Identify competitor weaknesses.\n"
                "2. Select Primary product + 2 Secondary products from DB.\n"
                "3. Justify 'Is it worth it?'\n"
                "4. List Table Differentiators (Materials, Feel, Certs)."
            )
        )
        self.product_db = product_db

    def execute_task(self, prompt_context, negative_constraints=""):
        full_prompt = f"{prompt_context}\n\nPRODUCT DATABASE (JSON):\n{json.dumps(self.product_db, indent=2)}"
        return super().execute_task(full_prompt, negative_constraints)

class ReviewerPersonaAgent(BaseAgent):
    """Agent 3: E-E-A-T Drafter (The Structural Architect)"""
    def __init__(self, tech_glossary, model):
        super().__init__(
            name="The Lab Tester (Drafter)",
            temperature=0.2,
            primary_model=model,
            role_description=(
                "You are a SleepyCat Technical Product Expert. Follow BRAND FINAL FORMULA strictly.\n\n"
                "Structure: 1. Title, 2. Direct Answer (AI Snippet), 3. Comparison Table, 4. Content, 5. Evaluation, 6. Buyer Guide, 7. FAQ, 8. Extra.\n"
                f"TECH GLOSSARY:\n{tech_glossary}\n\n"
                "RULES: 1. NO FABRICATION. 2. NO JARGON (No Density/ILD). 3. Harvest 'faq_specs' from DB."
            )
        )

    def execute_task(self, strategy_brief, product_db, negative_constraints=""):
        full_prompt = (
            f"STRATEGY BRIEF:\n{strategy_brief}\n\n"
            f"PRODUCT DATABASE (JSON):\n{json.dumps(product_db, indent=2)}\n\n"
            "TASK: Draft comprehensive blog following FINAL FORMULA."
        )
        return super().execute_task(full_prompt, negative_constraints)

class SEOEditorAgent(BaseAgent):
    """Agent 4: AEO & Semantic Optimizer (SEO Architect)"""
    def __init__(self, model):
        super().__init__(
            name="The SEO Architect",
            temperature=0.1,
            primary_model=model,
            role_description=(
                "You are an AEO expert. \n\n"
                "1. SNIPPET: Refine Direct Answer to 40-50 words.\n"
                "2. TABLE: Create Markdown comparison using Feel, Materials, Certs, Price.\n"
                "3. LINKS: Insert [Product](https://sleepycat.in/products/slug).\n"
                "4. SEMANTIC: Use spinal alignment, breathability, edge support."
            )
        )
        self.gsc_config = self._load_gsc_config()

    def _load_gsc_config(self):
        if os.environ.get("GSC_CLIENT_ID") and os.environ.get("GSC_API_KEY"):
            return {"client_id": os.environ.get("GSC_CLIENT_ID"), "api_key": os.environ.get("GSC_API_KEY")}
        return None

    def execute_task(self, draft, keyword, product_db, negative_constraints=""):
        prompt = (f"TARGET: {keyword}\nDB: {json.dumps(product_db, indent=2)}\nDRAFT: {draft}")
        return super().execute_task(prompt, negative_constraints)

class HumanizerAgent(BaseAgent):
    """Agent 5: Anti-AI Scrubbing (Senior Editor)"""
    def __init__(self, humanizer_rules, model):
        super().__init__(
            name="The Senior Editor (Humanizer)",
            primary_model=model,
            role_description=(
                "You are the final Senior Editor. Make text 100% human. \n\n"
                f"RULES:\n{humanizer_rules}\n"
                "1. REMOVE AI CLICHES. 2. Expert/Sharp tone. 3. Clean Markdown."
            )
        )


class Orchestrator:
    """Manages the hand-offs between the 5 distinct agents."""
    def __init__(self, model="gemini/gemini-1.5-flash"):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.model = model
        
        self.brand_dna = self._load_file(os.path.join(self.base_path, "brand_guidelines.txt"), "D2C Sleep Brand")
        self.tech_glossary = self._load_file(os.path.join(self.base_path, "sleepycat-tech-glossary.md"), "")
        self.product_db = self._load_json(os.path.join(self.base_path, "sleepycat-products.json"), {"products": []})
        self.humanizer_rules = self._load_file(os.path.join(self.base_path, "humanizer_rules.txt"), "Professional & Sharp.")
        
        self.filtered_products = self._filter_products(self.product_db)

        self.serp_agent = SERPScraperAgent()
        self.strategist = BrandStrategistAgent(self.brand_dna, self.filtered_products, self.tech_glossary, model)
        self.drafter = ReviewerPersonaAgent(self.tech_glossary, model)
        self.seo_editor = SEOEditorAgent(model)
        self.humanizer = HumanizerAgent(self.humanizer_rules, model)

    def _filter_products(self, db):
        return [p for p in db.get("products", []) if p.get("category") == "Mattresses"]

    def _load_file(self, path, fallback):
        try:
            with open(path, "r", encoding="utf-8") as f: return f.read()
        except: return fallback

    def _load_json(self, path, fallback):
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except: return fallback

    def _load_memory(self):
        try:
            memory_path = os.path.join(self.base_path, "agent_memory.json")
            if os.path.exists(memory_path):
                with open(memory_path, "r") as f:
                    mem_data = json.load(f)
                    return "\n".join([f"- {m['feedback']}" for m in mem_data[-10:]])
            return ""
        except: return ""

    def run(self, keyword):
        start_time = time.time()
        print(f"\n🚀 Starting: '{keyword}'")
        
        feedback_memory = self._load_memory()
        
        serp_data = self.serp_agent.execute_task(keyword)
        strategy_brief = self.strategist.execute_task(f"Target: {keyword}\nData: {serp_data}", feedback_memory)
        draft = self.drafter.execute_task(strategy_brief, self.filtered_products, feedback_memory)
        optimized_draft = self.seo_editor.execute_task(draft, keyword, self.filtered_products, feedback_memory)
        final_content = self.humanizer.execute_task(optimized_draft, feedback_memory)
        
        duration = round(time.time() - start_time, 2)
        return final_content, duration


if __name__ == "__main__":
    try:
        if os.isatty(0):
            target = input("Keyword: ")
            orchestrator = Orchestrator()
            content, dur = orchestrator.run(target)
            print(f"Done in {dur}s")
        else: print("Non-interactive.")
    except Exception as e: print(f"Error: {e}")
