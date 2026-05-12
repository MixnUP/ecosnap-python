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

# Estimated costs per item (in USD) for cost optimization
ITEM_COSTS = {
    # Proteins
    "chicken": 8.50, "chicken breast": 9.00, "pork": 7.50, "beef": 12.00, "fish": 10.00,
    "salmon": 15.00, "tofu": 4.00, "eggs": 3.50, "shrimp": 14.00, "turkey": 8.00, "lamb": 16.00,
    
    # Vegetables
    "spinach": 3.00, "broccoli": 2.50, "carrots": 2.00, "onions": 1.50, "peppers": 3.50,
    "tomatoes": 3.00, "lettuce": 2.50, "mushrooms": 4.00, "garlic": 1.00, "potatoes": 2.00,
    
    # Starches
    "rice": 2.50, "pasta": 2.00, "bread": 3.00, "noodles": 2.50, "quinoa": 6.00, "oats": 4.00,
    
    # Dairy
    "milk": 3.50, "cheese": 5.00, "yogurt": 4.00, "butter": 4.50, "cream": 5.50, "sour cream": 4.00,
    
    # Common items
    "oil": 6.00, "flour": 3.00, "sugar": 2.50, "salt": 1.00, "pepper": 2.00
}

# Seasonal recipe suggestions by location and season
SEASONAL_RECIPES = {
    "philippines": {
        "summer": ["gazpacho", "ceviche", "cold noodles", "grilled fish with mango salsa", "chicken salad"],
        "rainy": ["sinigang", "arroz caldo", "hot pot", "beef nilaga", "tinola"],
        "dry": ["adobo", "kare-kare", "mechado", "pakbet", "ginataan"]
    },
    "usa": {
        "summer": ["grilled burgers", "corn on the cob", "watermelon salad", "bbq ribs", "cold pasta salad"],
        "fall": ["pumpkin soup", "apple crisp", "roasted chicken", "butternut squash", "chili"],
        "winter": ["beef stew", "hot chocolate", "roasted turkey", "vegetable soup", "casseroles"],
        "spring": ["asparagus salad", "strawberry shortcake", "lamb dishes", "fresh pea soup", "herb chicken"]
    },
    "default": {
        "summer": ["grilled dishes", "cold salads", "light soups", "fruit desserts"],
        "fall": ["roasted vegetables", "hearty soups", "baked dishes", "apple recipes"],
        "winter": ["stews", "hot soups", "roasted meats", "comfort foods"],
        "spring": ["fresh vegetables", "light dishes", "herb recipes", "salads"]
    }
}

class RecipeService:
    """Service for generating recipes from expiring ingredients using Gemini."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemma-4-31b-it"
        self.firebase_service = FirebaseService()
    
    async def generate_recipe(self, expiring_items: List[dict], dietary_restrictions: List[str] = None, user_id: str = None, multi_recipe: bool = False) -> Dict[str, Any]:
        """Generate a dinner recipe from expiring ingredients using Gemma 4 31B.
        
        Args:
            expiring_items: List of expiring ingredients
            dietary_restrictions: List of dietary restrictions
            user_id: User ID for personalization
            multi_recipe: If True, return 3 recipe variants (QUICK, BALANCED, CREATIVE)
        """
        if not expiring_items:
            return None
        
        # Convert Pydantic models to dicts for processing
        items_list = [item.model_dump() if hasattr(item, 'model_dump') else item for item in expiring_items]
        
        # Phase 2: Fetch user context if user_id provided
        user_preferences = {}
        user_pantry = []
        recent_recipes = []
        seasonal_context = {}
        
        if user_id:
            user_preferences = await self.firebase_service.get_user_preferences(user_id)
            user_pantry = await self.firebase_service.get_user_pantry(user_id)
            recent_recipes = await self.firebase_service.get_recent_recipes(user_id, days=7)
            
            # Phase 3: Get seasonal suggestions based on user location
            user_location = user_preferences.get("location", "default")
            seasonal_context = self._get_seasonal_suggestions(user_location)
        
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
        if multi_recipe:
            prompt = self._build_multi_recipe_prompt(ingredients_text, restrictions_text, categorized_items, prioritized_items, user_preferences, user_pantry, recent_recipes, seasonal_context)
        else:
            prompt = self._build_enhanced_prompt(ingredients_text, restrictions_text, categorized_items, prioritized_items, user_preferences, user_pantry, recent_recipes, seasonal_context)

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
            
            # Calculate cost savings
            cost_savings = self._calculate_cost_savings(items_list, user_pantry)
            monthly_savings = await self.get_monthly_savings(user_id) if user_id else {"monthly_total": 0.0}
            
            # Add original expiring items for reference
            # Add metadata to single recipe or each recipe in multi-recipe response
            if multi_recipe and isinstance(recipe_data, dict) and "recipes" in recipe_data:
                # Multi-recipe response
                for recipe in recipe_data["recipes"]:
                    recipe["expiring_items_used"] = items_list
                    recipe["categorized_items"] = categorized_items
                    recipe["urgent_items"] = [item for item in prioritized_items if item.get("hours_until_expiry", 999) < 24]
                    recipe["user_preferences"] = user_preferences
                    recipe["user_pantry"] = user_pantry
                    # Override AI-estimated cost with calculated cost
                    recipe["estimated_cost_saved"] = cost_savings["total_saved"]
                
                # Add cost summary to multi-recipe response
                recipe_data["cost_savings"] = cost_savings
                recipe_data["monthly_savings"] = monthly_savings
                recipe_data["seasonal_context"] = seasonal_context
            else:
                # Single recipe response
                recipe_data["expiring_items_used"] = items_list
                recipe_data["categorized_items"] = categorized_items
                recipe_data["urgent_items"] = [item for item in prioritized_items if item.get("hours_until_expiry", 999) < 24]
                recipe_data["user_preferences"] = user_preferences
                recipe_data["user_pantry"] = user_pantry
                # Override AI-estimated cost with calculated cost
                recipe_data["estimated_cost_saved"] = cost_savings["total_saved"]
                recipe_data["cost_savings"] = cost_savings
                recipe_data["monthly_savings"] = monthly_savings
                recipe_data["seasonal_context"] = seasonal_context
            
            self.logger.info(f"Generated recipe: {recipe_data.get('title', 'Unknown')}")
            
            # Store in recipe history if user_id provided
            if user_id:
                if multi_recipe and isinstance(recipe_data, dict) and "recipes" in recipe_data:
                    # Store all recipes with chosen flag for the first one
                    for i, recipe in enumerate(recipe_data["recipes"]):
                        await self.firebase_service.store_recipe_history(user_id, recipe, chosen=(i == 0))
                else:
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
                             recent_recipes: List[dict] = None,
                             seasonal_context: Dict[str, Any] = None) -> str:
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
        
        # Build seasonal context
        seasonal_prompt_context = ""
        if seasonal_context:
            seasonal_prompt_context = f"\n\n{seasonal_context.get('context', '')}"
        
        prompt = f"""You are a helpful cooking assistant. Create a dinner recipe using these expiring ingredients: {ingredients_text}.{restrictions_text}{category_context}{urgency_context}{preferences_context}{pantry_context}{history_context}{seasonal_prompt_context}

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
  "estimated_cost_saved": 12.50,
  "nutrition": {{
    "calories": 450,
    "protein": 35,
    "carbs": 20,
    "fat": 25,
    "fiber": 8,
    "sodium": 600,
    "health_notes": "High in protein, moderate sodium - consider low-sodium soy sauce alternative"
  }}
}}

Include estimated nutritional information per serving. Note any health considerations or dietary benefits.

Make sure JSON is valid and properly formatted."""
        
        return prompt
    
    def _calculate_cost_savings(self, expiring_items: List[dict], user_pantry: List[dict] = None) -> Dict[str, float]:
        """Calculate cost savings from expiring items and pantry items used."""
        items_used_cost = 0.0
        pantry_items_cost = 0.0
        
        # Calculate cost of expiring items
        for item in expiring_items:
            item_name = item.get('name', '').lower()
            quantity = item.get('quantity', 1)
            
            # Find matching cost estimate
            estimated_cost = None
            for cost_key, cost_value in ITEM_COSTS.items():
                if cost_key in item_name:
                    estimated_cost = cost_value
                    break
            
            if estimated_cost is None:
                estimated_cost = 5.00  # Default cost for unknown items
            
            items_used_cost += estimated_cost * quantity
        
        # Calculate cost of pantry items (if provided)
        if user_pantry:
            for item in user_pantry[:5]:  # Limit to first 5 pantry items
                item_name = item.get('name', '').lower()
                quantity = item.get('quantity', 1)
                
                # Find matching cost estimate
                estimated_cost = None
                for cost_key, cost_value in ITEM_COSTS.items():
                    if cost_key in item_name:
                        estimated_cost = cost_value
                        break
                
                if estimated_cost is None:
                    estimated_cost = 2.00  # Default cost for pantry items
                
                pantry_items_cost += estimated_cost * 0.3  # Assume 30% of pantry item value is utilized
        
        total_saved = items_used_cost + pantry_items_cost
        
        return {
            "items_used_cost": round(items_used_cost, 2),
            "pantry_items_cost": round(pantry_items_cost, 2),
            "total_saved": round(total_saved, 2)
        }
    
    async def get_monthly_savings(self, user_id: str) -> Dict[str, float]:
        """Get cumulative savings for a user for the current month."""
        if not user_id:
            return {"monthly_total": 0.0}
        
        try:
            recent_recipes = await self.firebase_service.get_recent_recipes(user_id, days=30)
            monthly_total = 0.0
            
            for recipe in recent_recipes:
                saved_amount = recipe.get("estimated_cost_saved", 0.0)
                if isinstance(saved_amount, (int, float)):
                    monthly_total += saved_amount
            
            return {"monthly_total": round(monthly_total, 2)}
        except Exception as e:
            self.logger.error(f"Failed to calculate monthly savings: {e}")
            return {"monthly_total": 0.0}
    
    def _generate_fallback_recipe(self, expiring_items: List[dict], user_preferences: Dict[str, Any] = None, user_pantry: List[dict] = None) -> Dict[str, Any]:
        """Generate a simple fallback recipe when AI fails."""
        ingredients_text = ", ".join([item.get('name', 'Unknown') for item in expiring_items[:3]])
        
        # Apply Phase 1 enhancements to fallback as well
        categorized_items = self._categorize_items(expiring_items)
        prioritized_items = self._prioritize_by_urgency(expiring_items)
        
        # Calculate cost savings for fallback
        cost_savings = self._calculate_cost_savings(expiring_items, user_pantry)
        
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
            "estimated_cost_saved": cost_savings["total_saved"],
            "cost_savings": cost_savings,
            "nutrition": {
                "calories": 400,
                "protein": 30,
                "carbs": 25,
                "fat": 20,
                "fiber": 6,
                "sodium": 550,
                "health_notes": "Basic balanced meal - adjust seasoning to taste"
            },
            "expiring_items_used": expiring_items,
            "categorized_items": categorized_items,
            "urgent_items": [item for item in prioritized_items if item.get("hours_until_expiry", 999) < 24],
            "user_preferences": user_preferences or {},
            "user_pantry": user_pantry or [],
            "fallback": True
        }
        
        return fallback_data
    
    def _get_seasonal_suggestions(self, user_location: str = None) -> Dict[str, Any]:
        """Get seasonal recipe suggestions based on user location."""
        import datetime
        
        # Default location if not provided
        if not user_location:
            user_location = "default"
        
        # Normalize location to lowercase
        user_location = user_location.lower()
        
        # Determine current season (simplified for Northern Hemisphere)
        current_month = datetime.datetime.now().month
        if current_month in [6, 7, 8]:  # June, July, August
            season = "summer"
        elif current_month in [9, 10, 11]:  # September, October, November
            season = "fall"
        elif current_month in [12, 1, 2]:  # December, January, February
            season = "winter"
        else:  # March, April, May
            season = "spring"
        
        # Handle Philippines seasons (rainy/dry instead of traditional)
        if user_location == "philippines":
            if current_month in [6, 7, 8, 9, 10]:  # June to October
                season = "rainy"
            else:  # November to May
                season = "dry"
        
        # Get seasonal recipes for location
        location_recipes = SEASONAL_RECIPES.get(user_location, SEASONAL_RECIPES["default"])
        seasonal_suggestions = location_recipes.get(season, [])
        
        return {
            "location": user_location,
            "season": season,
            "suggestions": seasonal_suggestions,
            "context": f"Current season in {user_location}: {season}. Consider these seasonal approaches: {', '.join(seasonal_suggestions[:3])}"
        }
    
    def _build_multi_recipe_prompt(self, ingredients_text: str, restrictions_text: str, 
                                  categorized_items: Dict[str, List[dict]], 
                                  prioritized_items: List[dict],
                                  user_preferences: Dict[str, Any] = None,
                                  user_pantry: List[dict] = None,
                                  recent_recipes: List[dict] = None,
                                  seasonal_context: Dict[str, Any] = None) -> str:
        """Build prompt for generating 3 recipe variants in single call."""
        
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
        
        # Build seasonal context
        seasonal_prompt_context = ""
        if seasonal_context:
            seasonal_prompt_context = f"\n\n{seasonal_context.get('context', '')}"
        
        prompt = f"""You are a helpful cooking assistant. Generate 3 different dinner recipe options using these expiring ingredients: {ingredients_text}.{restrictions_text}{category_context}{urgency_context}{preferences_context}{pantry_context}{history_context}{seasonal_prompt_context}

Assume the user has these common pantry staples available: {', '.join(PANTRY_STAPLES)}
Do not list these pantry staples as required ingredients unless a specific quantity is needed.

Generate 3 different dinner options:
1. QUICK (15 min, minimal ingredients, very easy)
2. BALANCED (30 min, nutritionally complete, moderate difficulty)
3. CREATIVE (45+ min, uses maximum expiring items, more complex)

Respond ONLY with a valid JSON object in this exact format:
{{
  "recipes": [
    {{
      "type": "QUICK",
      "title": "Recipe name",
      "ingredients": ["list of ingredients with quantities"],
      "instructions": ["step 1", "step 2", "step 3"],
      "cook_time_minutes": 15,
      "difficulty": "easy",
      "estimated_cost_saved": 8.50,
      "nutrition": {{
        "calories": 350,
        "protein": 25,
        "carbs": 30,
        "fat": 15,
        "fiber": 5,
        "sodium": 500,
        "health_notes": "Quick and balanced, good source of protein"
      }}
    }},
    {{
      "type": "BALANCED",
      "title": "Recipe name",
      "ingredients": ["list of ingredients with quantities"],
      "instructions": ["step 1", "step 2", "step 3"],
      "cook_time_minutes": 30,
      "difficulty": "medium",
      "estimated_cost_saved": 12.50,
      "nutrition": {{
        "calories": 450,
        "protein": 35,
        "carbs": 35,
        "fat": 20,
        "fiber": 8,
        "sodium": 600,
        "health_notes": "Nutritionally complete with good macro balance"
      }}
    }},
    {{
      "type": "CREATIVE",
      "title": "Recipe name",
      "ingredients": ["list of ingredients with quantities"],
      "instructions": ["step 1", "step 2", "step 3"],
      "cook_time_minutes": 45,
      "difficulty": "hard",
      "estimated_cost_saved": 18.75,
      "nutrition": {{
        "calories": 550,
        "protein": 40,
        "carbs": 40,
        "fat": 25,
        "fiber": 10,
        "sodium": 700,
        "health_notes": "Rich and complex meal, high in vegetables and protein"
      }}
    }}
  ]
}}

Include estimated nutritional information per serving for each recipe. Note any health considerations or dietary benefits.

Make sure JSON is valid and properly formatted."""
        
        return prompt
