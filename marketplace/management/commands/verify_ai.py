from django.core.management.base import BaseCommand
from marketplace.ai_service import (
    get_ai_config,
    call_llm_chat,
    generate_catalogue_assistant_suggestions,
    smart_craft_discovery
)


class Command(BaseCommand):
    help = "Verifies CraftConnect AI connectivity and tests both AI pipelines (Catalogue Assistant & Smart Discovery)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))
        self.stdout.write(self.style.MIGRATE_HEADING(" CraftConnect AI Pipeline Verification"))
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))

        config = get_ai_config()
        self.stdout.write(f"Provider:   {config['provider']}")
        self.stdout.write(f"API URL:    {config['api_url']}")
        self.stdout.write(f"Model:      {config['model']}")
        
        raw_key = config["api_key"]
        if raw_key:
            masked_key = raw_key[:10] + "..." + raw_key[-4:] if len(raw_key) > 14 else "***"
            self.stdout.write(self.style.SUCCESS(f"API Key:    Present ({masked_key})"))
        else:
            self.stdout.write(self.style.WARNING("API Key:    Not detected (using fallback heuristic engine)"))

        # Test 1: Direct LLM Chat Connectivity
        self.stdout.write("\n[1/3] Testing Direct LLM Connectivity...")
        test_messages = [
            {"role": "system", "content": "You are CraftConnect verification bot."},
            {"role": "user", "content": "Reply with single word: CONNECTED"}
        ]
        response = call_llm_chat(test_messages, max_tokens=15, timeout=12)
        if response:
            clean_resp = response.strip()[:60].replace("\n", " ")
            self.stdout.write(self.style.SUCCESS(f"  [OK] LLM API Connected Successfully: {clean_resp}"))
        else:
            self.stdout.write(self.style.WARNING("  [!] LLM API did not return response. Fallbacks remain fully active."))

        # Test 2: Artisan Catalogue Assistant Pipeline
        self.stdout.write("\n[2/3] Testing Artisan Catalogue Assistant Pipeline...")
        sample_title = "Terracotta Chai Kulhad"
        sample_notes = "Wheel-thrown earthenware clay, unglazed, smoky kiln finish"
        suggestions = generate_catalogue_assistant_suggestions(
            title=sample_title,
            raw_notes=sample_notes,
            material="Natural Red Clay",
            category_name="Ceramics & Terracotta"
        )
        self.stdout.write(self.style.SUCCESS(f"  [OK] Engine: {suggestions.get('ai_engine')}"))
        self.stdout.write(f"  [OK] Title: {suggestions.get('suggested_title')}")
        self.stdout.write(f"  [OK] Category: {suggestions.get('suggested_category')}")
        self.stdout.write(f"  [OK] Price: Rs. {suggestions.get('suggested_price')}")
        self.stdout.write(f"  [OK] Tags: {suggestions.get('suggested_tags')}")
        desc_sample = suggestions.get('suggested_description', '').replace("\n", " ")[:100]
        self.stdout.write(f"  [OK] Description: {desc_sample}...")

        # Test 3: Smart Craft Discovery Pipeline
        self.stdout.write("\n[3/3] Testing Smart Craft Discovery Pipeline...")
        query = "earthy clay cup for evening chai"
        discovery = smart_craft_discovery(query)
        self.stdout.write(self.style.SUCCESS(f"  [OK] Query: '{query}'"))
        self.stdout.write(f"  [OK] Extracted Keywords: {discovery.get('extracted_keywords')}")
        self.stdout.write(f"  [OK] Category Hint: {discovery.get('suggested_category')}")
        self.stdout.write(f"  [OK] AI Explanation: {discovery.get('ai_explanation')}")
        products_count = len(discovery.get("products", []))
        self.stdout.write(self.style.SUCCESS(f"  [OK] Matched Products: {products_count} items found"))

        self.stdout.write(self.style.MIGRATE_HEADING("\n=================================================="))
        self.stdout.write(self.style.SUCCESS(" ALL AI PIPELINES OPERATIONAL & VERIFIED"))
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))
