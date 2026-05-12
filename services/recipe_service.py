from typing import List, Dict, Any
import logging
import json
from google import genai
from google.genai import types

from core.config import settings

logger = logging.getLogger(__name__)

# Food categories for detection and prioritization
FOOD_CATEGORIES = {
    "proteins": ["chicken", "pork", "beef", "fish", "tofu", "eggs", "shrimp", "salmon", "turkey", "lamb"],
    "vegetables": ["spinach", "broccoli", "carrots", "onions", "peppers", "tomatoes", "lettuce", "mushrooms", "garlic", "potatoes"],
    "starches": ["rice", "pasta", "potatoes", "bread", "noodles", "quinoa", "oats"],
    "dairy": ["milk", "cheese", "yogurt", "butter", "cream", "sour cream"],
    "pantry": ["oil", "spices", "garlic", "onions", "flour", "sugar", "salt", "pepper"]
}

# Common pantry staples to assume user has
PANTRY_STAPLES = ["salt", "pepper", "oil", "garlic", "onions", "soy sauce", "vinegar", "flour", "sugar"]

class RecipeService:
    """Service for generating recipes from expiring ingredients using Gemini."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemma-4-31b-it"
    
    async def generate_recipe(self, expiring_items: List[dict], dietary_restrictions: List[str] = None) -> Dict[str, Any]:
        """Generate a dinner recipe from expiring ingredients using Gemma 4 31B."""
        if not expiring_items:
            return None
        
        # Convert Pydantic models to dicts for processing
        items_list = [item.model_dump() if hasattr(item, 'model_dump') else item for item in expiring_items]
        
        # Phase 1 enhancements
        categorized_items = self._categorize_items(items_list)
        prioritized_items = self._prioritize_by_urgency(items_list)
        
        ingredients_text = ", ".join([
            f"{item.get('quantity', 1)} {item.get('unit', 'item')} {item.get('name', 'Unknown')}"
            for item in prioritized_items[:5]
        ])
        
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text = f"\nDietary restrictions to follow: {', '.join(dietary_restrictions)}."
        
        self.logger.info(f"Generating recipe for: {ingredients_text}{restrictions_text}")
        
        # Build enhanced prompt with category context and pantry staples
        prompt = self._build_enhanced_prompt(ingredients_text, restrictions_text, categorized_items, prioritized_items)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            
            # Parse JSON response
            recipe_text = response.text.strip()
            
            # Handle markdown code blocks if present
            if recipe_text.startswith("```json"):
                recipe_text = recipe_text.replace("```json", "").replace("```", "").strip()
            elif recipe_text.startswith("```"):
                recipe_text = recipe_text.replace("```", "").strip()
            
            recipe_data = json.loads(recipe_text)
            
            # Add original expiring items for reference
            recipe_data["expiring_items_used"] = items_list
            recipe_data["categorized_items"] = categorized_items
            recipe_data["urgent_items"] = [item for item in prioritized_items if item.get("hours_until_expiry", 999) < 24]
            
            self.logger.info(f"Generated recipe: {recipe_data.get('title', 'Unknown')}")
            return recipe_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini response as JSON: {e}")
            self.logger.error(f"Raw response: {recipe_text}")
            # Fallback to structured response
            return self._generate_fallback_recipe(items_list)
            
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Exception details: {str(e)}")
            return self._generate_fallback_recipe(items_list)
    
    def _categorize_items(self, items: List[dict]) -> Dict[str, List[dict]]:
        """Categorize expiring items by food type."""
        categorized = {category: [] for category in FOOD_CATEGORIES}
        
        for item in items:
            name = item.get('name', '').lower()
            matched = False
            
            for category, foods in FOOD_CATEGORIES.items():
                if any(food in name for food in foods):
                    categorized[category].append(item)
                    matched = True
                    break
            
            if not matched:
                categorized['misc'] = categorized.get('misc', []) + [item]
        
        return categorized
    
    def _prioritize_by_urgency(self, items: List[dict]) -> List[dict]:
        """Prioritize items by expiry time, with urgent items first."""
        # Sort by hours_until_expiry (ascending - most urgent first)
        sorted_items = sorted(items, key=lambda x: x.get('hours_until_expiry', 999))
        return sorted_items
    
    def _build_enhanced_prompt(self, ingredients_text: str, restrictions_text: str, 
                             categorized_items: Dict[str, List[dict]], 
                             prioritized_items: List[dict]) -> str:
        """Build enhanced prompt with category context and pantry staples."""
        
        # Separate urgent vs regular items
        urgent_items = [item for item in prioritized_items if item.get('hours_until_expiry', 999) < 24]
        regular_items = [item for item in prioritized_items if item.get('hours_until_expiry', 999) >= 24]
        
        # Build category context
        category_context = ""
        if categorized_items.get('proteins'):
            category_context += f"\nMain protein available: {', '.join([item['name'] for item in categorized_items['proteins']])}"
        if categorized_items.get('vegetables'):
            category_context += f"\nVegetables available: {', '.join([item['name'] for item in categorized_items['vegetables']])}"
        
        # Build urgency context
        urgency_context = ""
        if urgent_items:
            urgency_context = f"\n\nCRITICAL - Must use these items (expire within 24h): {', '.join([item['name'] for item in urgent_items])}"
        if regular_items:
            urgency_context += f"\nAlso incorporate if possible: {', '.join([item['name'] for item in regular_items])}"
        
        prompt = f"""You are a helpful cooking assistant. Create a dinner recipe using these expiring ingredients: {ingredients_text}.{restrictions_text}{category_context}{urgency_context}

Assume the user has these common pantry staples available: {', '.join(PANTRY_STAPLES)}
Do not list these pantry staples as required ingredients unless a specific quantity is needed.

The recipe should be practical for a home cook making dinner tonight. 

Respond ONLY with a valid JSON object in this exact format:
{{
  "title": "Recipe name",
  "ingredients": ["list of ingredients with quantities"],
  "instructions": ["step 1", "step 2", "step 3"],
  "cook_time_minutes": 30,
  "difficulty": "easy|medium|hard",
  "estimated_cost_saved": 12.50
}}

Make sure JSON is valid and properly formatted."""
        
        return prompt
    
    def _generate_fallback_recipe(self, expiring_items: List[dict]) -> Dict[str, Any]:
        """Generate a simple fallback recipe when AI fails."""
        ingredients_text = ", ".join([item.get('name', 'Unknown') for item in expiring_items[:3]])
        
        # Apply Phase 1 enhancements to fallback as well
        categorized_items = self._categorize_items(expiring_items)
        prioritized_items = self._prioritize_by_urgency(expiring_items)
        
        return {
            "title": f"Quick Dinner with {ingredients_text}",
            "ingredients": expiring_items,
            "instructions": [
                "Prepare ingredients by washing and cutting as needed.",
                "Heat pan over medium-high heat with oil.",
                "Cook proteins first, then add vegetables.",
                "Season to taste and serve immediately."
            ],
            "cook_time_minutes": 25,
            "difficulty": "easy",
            "estimated_cost_saved": sum([6.50 for _ in expiring_items]),
            "expiring_items_used": expiring_items,
            "categorized_items": categorized_items,
            "urgent_items": [item for item in prioritized_items if item.get("hours_until_expiry", 999) < 24],
            "fallback": True
        }
