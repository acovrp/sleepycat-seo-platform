import os
import json
import requests
import time
from bs4 import BeautifulSoup
from googlesearch import search
import litellm

# ==========================================
# SleepyCat True Multi-Agent E-E-A-T System
# Engine v3.0 (LiteLLM + Memory Ready)
# ==========================================

class BaseAgent:
    """Base class for all specialized agents using LiteLLM for multi-model support."""
    def __init__(self, name, role_description, temperature=0.7, primary_model="gemini/gemini-1.5-flash"):
        self.name = name
        self.role_description = role_description
        self.temperature = temperature
        self.primary_model = primary_model
        
        # Ensure API keys are set for LiteLLM
        # Usage: GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
        
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
            # LiteLLM handles the routing and can handle fallbacks if configured
            response = litellm.completion(
                model=self.primary_model,
                messages=messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  - Error in {self.name} with model {self.primary_model}: {e}")
            # Simple manual fallback if litellm doesn't have a router config yet
            if "gemini" in self.primary_model and os.environ.get("OPENAI_API_KEY"):
                print("  - Falling back to GPT-4o-mini...")
                response = litellm.completion(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=self.temperature
                )
                return response.choices[0].message.content
            raise e


class SERPScraperAgent:
    """Agent 1: Competition Analysis (SERP Spy)"""
    def __init__(self):
        self.name = "The SERP Spy"
        
    def execute_task(self, keyword):
        print(f"\n[Agent: {self.name}] Scraping Top 3 Results for: '{keyword}'...")
        results = []
        try:
            query = f"{keyword} India"
            urls = list(search(query, num_results=3))
            
            for url in urls:
                print(f"  - Scraping: {url}")
                try:
                    res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(res.text, 'html.parser')
                    headings = [h.get_text().strip() for h in soup.find_all(['h2', 'h3'])[:10]]
                    title = soup.title.string if soup.title else "No Title"
                    results.append(f"Source: {url}\nTitle: {title}\nHeadings: {', '.join(headings)}")
                except Exception as e:
                    print(f"    Error scraping {url}: {e}")
            
            if not results:
                return "No real-time SERP data found. Falling back to industry knowledge."
            
            return "\n\n".join(results)
        except Exception as e:
            print(f"SERP Search Error: {e}")
            return "SERP search failed. Using fallback simulation."

class BrandStrategistAgent(BaseAgent):
    """Agent 2: Brand DNA Injector"""
    def __init__(self, brand_guidelines, product_db, tech_glossary, model):
        super().__init__(
            name="The Brand Strategist",
            primary_model=model,
            role_description=(
                "You are the Senior SleepyCat Brand Strategist. Your mission is to weaponize the SleepyCat Brand DNA "
                "against generic competitor claims. \n\n"
                f"BRAND DNA:\n{brand_guidelines}\n\n"
                f"TECH GLOSSARY:\n{tech_glossary}\n\n"
                "Your task is to analyze raw SERP data and output a 'Strategic Brief' that:\n"
                "1. COUNTER-POSITIONING: Identify competitor weaknesses and explain how SleepyCat's 'Joy of Rest' philosophy beats them.\n"
                "2. PRODUCT SELECTION: Select the BEST SleepyCat product for this keyword and TWO secondary products for the Comparison Table.\n"
                "3. THE 'IS IT WORTH IT?' ARGUMENT: Provide a clear value-based justification for why the reader should invest in this specific product.\n"
                "4. COMPARISON DATA: List 3-4 key differentiators (Materials, Feel, Certifications) between the primary product and the secondary products for the Table section."
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
                "You are a SleepyCat Technical Product Expert. You MUST follow the BRAND FINAL FORMULA strictly.\n\n"
                "BRAND FINAL FORMULA STRUCTURE:\n"
                "1. Title (H1)\n"
                "2. Direct Answer (2-3 lines) - Explicitly answer 'What is it?' or 'Which is best?' for AI snippets.\n"
                "3. Comparison Table Section - (Placeholder for Agent 4 to populate).\n"
                "4. Main Content Section (Core Info) - Pointers & benefits deep dives.\n"
                "5. Comparison / Evaluation Section - Detailed product vs category analysis.\n"
                "6. How to Choose (Buyer Guide) - Actionable checklist.\n"
                "7. FAQ Section (5-10 questions) - Use REAL FAQs from the product database.\n"
                "8. EXTRA (Pros & Cons, Use Cases, Is it worth it?).\n\n"
                f"PROPRIETARY TECH GLOSSARY:\n{tech_glossary}\n\n"
                "RULES:\n"
                "1. NO FABRICATION: Use only specs from the JSON provided.\n"
                "2. NO JARGON: Do NOT mention 'Density' (kg/m3) or 'ILD' ratings. Focus on the FEEL (Firm/Medium/Soft) and the materials used.\n"
                "3. FAQ HARVESTING: Search the JSON for 'faq_specs' for the recommended products and include them verbatim."
            )
        )

    def execute_task(self, strategy_brief, product_db, negative_constraints=""):
        full_prompt = (
            f"STRATEGY BRIEF:\n{strategy_brief}\n\n"
            f"PRODUCT DATABASE (JSON):\n{json.dumps(product_db, indent=2)}\n\n"
            "TASK: Draft a comprehensive blog following the BRAND FINAL FORMULA. Include a dedicated section for FAQs pulled from the data."
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
                "You are an Answer Engine Optimization (AEO) expert. Your job is to transform a draft into a 2026-ready search asset.\n\n"
                "AEO MANDATES:\n"
                "1. SNIPPET OPTIMIZATION: Refine the 'Direct Answer' section to be exactly 40-50 words, answering the primary query verbatim for Google AI Overviews.\n"
                "2. DATA-DRIVEN TABLES: Create a high-fidelity Markdown Comparison Table comparing the 3 products selected by the Strategist (Primary vs Secondary 1 vs Secondary 2). Use real specs (Feel, Materials, Certs, Price) from the JSON. NEVER mention Density or ILD.\n"
                "3. SCHEMA POINTERS: Ensure FAQs are formatted as H3 questions followed by clear answers.\n"
                "4. INTERNAL LINKS: Insert [Product Name](https://sleepycat.in/products/slug) links using real slugs."
            )
        )
        self.gsc_config = self._load_gsc_config()

    def _load_gsc_config(self):
        # Priority 1: Environment Variables (for Secure Cloud Hosting)
        if os.environ.get("GSC_CLIENT_ID") and os.environ.get("GSC_API_KEY"):
            return {
                "client_id": os.environ.get("GSC_CLIENT_ID"),
                "api_key": os.environ.get("GSC_API_KEY")
            }
            
        # Priority 2: Local JSON File
        try:
            with open("gsc_config.json", "r") as f:
                return json.load(f)
        except:
            return None

    def execute_task(self, draft, keyword, product_db, negative_constraints=""):
        prompt = (
            f"TARGET KEYWORD: {keyword}\n"
            f"PRODUCT DATABASE:\n{json.dumps(product_db, indent=2)}\n\n"
            f"DRAFT TO OPTIMIZE:\n{draft}"
        )
        return super().execute_task(prompt, negative_constraints)

class HumanizerAgent(BaseAgent):
    """Agent 5: Anti-AI Scrubbing (Senior Editor)"""
    def __init__(self, humanizer_rules, model):
        super().__init__(
            name="The Senior Editor (Humanizer)",
            primary_model=model,
            role_description=(
                "You are the final Senior Editor for the SleepyCat blog. Your job is to make text sound 100% human. \n\n"
                f"HUMANIZER RULES:\n{humanizer_rules}\n"
                "1. DELETE AI CLICHES: Remove 'In today's fast-paced world', 'Test Subject 42', 'Lab Simulation A', or any phrase that sounds like a fake scientific study.\n"
                "2. AUTHORITATIVE TONE: Ensure the tone is expert, confident, and sharp. No fluff.\n"
                "3. FORMATTING: Ensure clean markdown, bold headers, and short, readable paragraphs."
            )
        )


class Orchestrator:
    """Manages the hand-offs between the 5 distinct agents."""
    def __init__(self, model="gemini/gemini-1.5-flash"):
        # Paths to real data
        self.kb_path = r"C:\Users\Aayushi\sleepycat-brand\product knowledge"
        self.brand_kb_path = r"C:\Users\Aayushi\sleepycat-brand\brand knowledge"
        self.model = model
        
        # Load external data
        self.brand_dna = self._load_file(os.path.join(self.brand_kb_path, "brand_guidelines.txt"), "D2C Sleep Brand")
        self.tech_glossary = self._load_file(os.path.join(self.kb_path, "sleepycat-tech-glossary.md"), "")
        self.product_db = self._load_json(os.path.join(self.kb_path, "sleepycat-products.json"), {"products": []})
        self.humanizer_rules = self._load_file(os.path.join(self.brand_kb_path, "humanizer_rules.txt"), "Professional & Sharp.")
        
        # Filter product DB for relevant products to save context space
        self.filtered_products = self._filter_products(self.product_db)

        self.serp_agent = SERPScraperAgent()
        self.strategist = BrandStrategistAgent(self.brand_dna, self.filtered_products, self.tech_glossary, self.model)
        self.drafter = ReviewerPersonaAgent(self.tech_glossary, self.model)
        self.seo_editor = SEOEditorAgent(self.model)
        self.humanizer = HumanizerAgent(self.humanizer_rules, self.model)

    def _filter_products(self, db):
        """Keep only core mattresses and tech relevant products to keep JSON size manageable."""
        return [p for p in db.get("products", []) if p.get("category") == "Mattresses"]

    def _load_file(self, path, fallback):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return fallback

    def _load_json(self, path, fallback):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return fallback

    def _load_memory(self):
        """Loads 'Why?' feedback from rejected outputs to avoid repeating mistakes."""
        try:
            memory_path = os.path.join(self.brand_kb_path, "agent_memory.json")
            if os.path.exists(memory_path):
                with open(memory_path, "r") as f:
                    mem_data = json.load(f)
                    # Convert feedback list into a single string of negative constraints
                    return "\n".join([f"- {m['feedback']}" for m in mem_data[-10:]]) # Last 10 feedbacks
            return ""
        except:
            return ""

    def run(self, keyword):
        print(f"\n🚀 Starting DATA-DRIVEN Orchestrator for keyword: '{keyword}'")
        
        # Phase 3: Load RLHF Memory (Negative Constraints)
        feedback_memory = self._load_memory()
        if feedback_memory:
            print(f"  - Injected Memory Constraints: {len(feedback_memory.splitlines())} entries found.")
        
        # Step 1: Scrape
        serp_data = self.serp_agent.execute_task(keyword)
        time.sleep(1)
        
        # Step 2: Strategize
        brief_prompt = f"Target Keyword: {keyword}\nCompetitor Data:\n{serp_data}"
        strategy_brief = self.strategist.execute_task(brief_prompt, feedback_memory)
        time.sleep(1)
        
        # Step 3: Draft (Factual Only)
        draft = self.drafter.execute_task(strategy_brief, self.filtered_products, feedback_memory)
        time.sleep(1)
        
        # Step 4: Optimize
        optimized_draft = self.seo_editor.execute_task(draft, keyword, self.filtered_products, feedback_memory)
        time.sleep(1)
        
        # Step 5: Humanize
        final_content = self.humanizer.execute_task(optimized_draft, feedback_memory)
        
        # Save output (if running in CLI)
        if __name__ == "__main__":
            filename = f"{keyword.replace(' ', '_')}_final.md"
            filename = "".join([c for c in filename if c.isalnum() or c in ('_', '.')]).rstrip()
            with open(os.path.join(self.brand_kb_path, filename), "w", encoding="utf-8") as f:
                f.write(final_content)
            print(f"\n[+] Data-driven output saved to {filename}")
            
        return final_content


if __name__ == "__main__":
    # For local CLI testing
    target = input("Enter target SEO keyword: ")
    if not target:
        target = "Best mattress for back pain in India"
    
    orchestrator = Orchestrator()
    orchestrator.run(target)
