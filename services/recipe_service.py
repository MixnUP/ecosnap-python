from typing import List, Dict, Any
import logging
import json
from google import genai
from google.genai import types

from core.config import settings

logger = logging.getLogger(__name__)

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
        
        ingredients_text = ", ".join([
            f"{item.get('quantity', 1)} {item.get('unit', 'item')} {item.get('name', 'Unknown')}"
            for item in expiring_items[:5]
        ])
        
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text = f"\nDietary restrictions to follow: {', '.join(dietary_restrictions)}."
        
        self.logger.info(f"Generating recipe for: {ingredients_text}{restrictions_text}")
        
        prompt = f"""You are a helpful cooking assistant. Create a dinner recipe using these expiring ingredients: {ingredients_text}.{restrictions_text}

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

Make sure the JSON is valid and properly formatted."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            
            # Parse the JSON response
            recipe_text = response.text.strip()
            
            # Handle markdown code blocks if present
            if recipe_text.startswith("```json"):
                recipe_text = recipe_text.replace("```json", "").replace("```", "").strip()
            elif recipe_text.startswith("```"):
                recipe_text = recipe_text.replace("```", "").strip()
            
            recipe_data = json.loads(recipe_text)
            
            # Add original expiring items for reference
            recipe_data["expiring_items_used"] = expiring_items
            
            self.logger.info(f"Generated recipe: {recipe_data.get('title', 'Unknown')}")
            return recipe_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini response as JSON: {e}")
            self.logger.error(f"Raw response: {recipe_text}")
            # Fallback to structured response
            return self._generate_fallback_recipe(expiring_items)
            
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")
            return self._generate_fallback_recipe(expiring_items)
    
    def _generate_fallback_recipe(self, expiring_items: List[dict]) -> Dict[str, Any]:
        """Generate a simple fallback recipe when AI fails."""
        ingredients_text = ", ".join([item.get('name', 'Unknown') for item in expiring_items[:3]])
        
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
            "fallback": True
        }
