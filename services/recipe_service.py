from typing import List, Dict, Any
import logging
import json
from google import genai
from google.genai import types

from core.config import settings
from services.firebase_service import FirebaseService

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
        self.firebase_service = FirebaseService()
    
    async def generate_recipe(self, expiring_items: List[dict], dietary_restrictions: List[str] = None, user_id: str = None) -> Dict[str, Any]:
        """Generate a dinner recipe from expiring ingredients using Gemma 4 31B."""
        if not expiring_items:
            return None
        
        # Convert Pydantic models to dicts for processing
        items_list = [item.model_dump() if hasattr(item, 'model_dump') else item for item in expiring_items]
        
        # Phase 2: Fetch user context if user_id provided
        user_preferences = {}
        user_pantry = []
        recent_recipes = []
        
        if user_id:
            user_preferences = await self.firebase_service.get_user_preferences(user_id)
            user_pantry = await self.firebase_service.get_user_pantry(user_id)
            recent_recipes = await self.firebase_service.get_recent_recipes(user_id, days=7)
        
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
        
        # Build enhanced prompt with all Phase 1 + Phase 2 context
        prompt = self._build_enhanced_prompt(ingredients_text, restrictions_text, categorized_items, prioritized_items, user_preferences, user_pantry, recent_recipes)

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
            recipe_data["user_preferences"] = user_preferences
            recipe_data["user_pantry"] = user_pantry
            
            self.logger.info(f"Generated recipe: {recipe_data.get('title', 'Unknown')}")
            
            # Store in recipe history if user_id provided
            if user_id:
                await self.firebase_service.store_recipe_history(user_id, recipe_data, chosen=True)
            
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
                             prioritized_items: List[dict],
                             user_preferences: Dict[str, Any] = None,
                             user_pantry: List[dict] = None,
                             recent_recipes: List[dict] = None) -> str:
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
        
        # Build user preferences context
        preferences_context = ""
        if user_preferences:
            cuisine_types = user_preferences.get("cuisineTypes", [])
            spice_level = user_preferences.get("spiceLevel", "medium")
            cooking_skill = user_preferences.get("cookingSkill", "intermediate")
            max_cook_time = user_preferences.get("maxCookTime", 45)
            serving_size = user_preferences.get("servingSize", 2)
            
            preferences_context = f"\n\nUser preferences:"
            if cuisine_types:
                preferences_context += f"\n- Preferred cuisines: {', '.join(cuisine_types)}"
            preferences_context += f"\n- Spice level: {spice_level}"
            preferences_context += f"\n- Cooking skill: {cooking_skill}"
            preferences_context += f"\n- Max cook time: {max_cook_time} minutes"
            preferences_context += f"\n- Serving size: {serving_size} people"
        
        # Build user pantry context
        pantry_context = ""
        if user_pantry:
            pantry_items = [f"{item.get('quantity', 1)} {item.get('unit', 'item')} {item.get('name', 'Unknown')}" for item in user_pantry[:10]]
            pantry_context = f"\n\nUser has these pantry items available: {', '.join(pantry_items)}"
            pantry_context += "\nIncorporate these pantry items efficiently with expiring ingredients."
        
        # Build recipe history context for deduplication
        history_context = ""
        if recent_recipes:
            recent_titles = [recipe.get("title", "") for recipe in recent_recipes[:5]]
            history_context = f"\n\nAvoid suggesting recipes similar to these recent meals: {', '.join(recent_titles)}"
        
        prompt = f"""You are a helpful cooking assistant. Create a dinner recipe using these expiring ingredients: {ingredients_text}.{restrictions_text}{category_context}{urgency_context}{preferences_context}{pantry_context}{history_context}

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
    
    def _generate_fallback_recipe(self, expiring_items: List[dict], user_preferences: Dict[str, Any] = None, user_pantry: List[dict] = None) -> Dict[str, Any]:
        """Generate a simple fallback recipe when AI fails."""
        ingredients_text = ", ".join([item.get('name', 'Unknown') for item in expiring_items[:3]])
        
        # Apply Phase 1 enhancements to fallback as well
        categorized_items = self._categorize_items(expiring_items)
        prioritized_items = self._prioritize_by_urgency(expiring_items)
        
        # Add user context to fallback
        fallback_data = {
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
            "user_preferences": user_preferences or {},
            "user_pantry": user_pantry or [],
            "fallback": True
        }
        
        return fallback_data
