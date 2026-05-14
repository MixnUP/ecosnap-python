# EcoSnap API

EcoSnap is an expiry-first dinner triage backend that leverages AI to help users reduce food waste. By inputting expiring ingredients, dietary restrictions, and personal preferences, the EcoSnap API generates personalized dinner recipes—estimating cost savings and nutritional value.

## 🚀 Key Features

### 1. Expiry-First Triage Workflows
The core of the application is the Triage API. It categorizes and prioritizes ingredients by urgency (e.g., items expiring within 24 hours). The AI model (`gemma-4-31b-it`) is prompted to formulate a recipe incorporating these urgent items efficiently.

### 2. Multi-Recipe Generation
EcoSnap provides users with up to three variations of meals in a single generation call:
- **QUICK**: 15 min, minimal ingredients, very easy.
- **BALANCED**: 30 min, nutritionally complete, moderate difficulty.
- **CREATIVE**: 45+ min, uses maximum expiring items, more complex.

### 3. User Preferences & Pantry Integration (Firebase)
EcoSnap utilizes Firebase Firestore to create a highly personalized cooking experience:
- **Pantry Tracking**: Accesses the user's current pantry items to weave existing staples into the recipe.
- **User Preferences**: Adjusts for cuisine types, spice levels, cooking skills, max cook times, and serving sizes.
- **Seasonal Context**: Analyzes the user's location to suggest seasonal dishes (e.g., "rainy" season recipes in the Philippines vs. "winter" recipes in the USA).

### 4. Recipe History & Deduplication
To ensure diverse suggestions, EcoSnap retrieves the last 7 days of generated recipes from Firestore and instructs the AI to avoid recent meals. Chosen recipes are automatically stored in the `recipe_history` collection.

### 5. Cost Savings Estimation
The system calculates approximate cost savings by looking up average prices for the expiring ingredients and pantry items utilized, showcasing the monetary value of reducing food waste.

---

## 🏗️ System Architecture

The project is built on **FastAPI** with **Google GenAI (Gemini)** for the reasoning engine, and **Firebase Firestore** for persistent data management.

### Backend Stack
- **Framework:** FastAPI
- **AI Engine:** Google GenAI (`gemma-4-31b-it`)
- **Database:** Firebase Firestore
- **Security & Rate Limiting:** API Key Authentication, `slowapi`

---

## 💻 Code Snippets

### Triage Request Model
The request payload supports multi-recipe toggling and personalization via user IDs.

```python
class ExpiringItem(BaseModel):
    name: str
    quantity: Optional[float] = 1.0
    unit: Optional[str] = "item"
    category: Optional[str] = None
    hours_until_expiry: Optional[int] = 999

class TriageRequest(BaseModel):
    expiring_items: List[ExpiringItem]
    dietary_restrictions: Optional[List[str]] = None
    user_id: Optional[str] = None
    multi_recipe: Optional[bool] = False
```

### Contextual Recipe Generation
The `RecipeService` seamlessly gathers context from Firebase before prompting the AI:

```python
# Fetch user context if user_id provided
user_preferences = {}
user_pantry = []
recent_recipes = []
seasonal_context = {}

if user_id:
    user_preferences = await self.firebase_service.get_user_preferences(user_id)
    user_pantry = await self.firebase_service.get_user_pantry(user_id)
    recent_recipes = await self.firebase_service.get_recent_recipes(user_id, days=7)
    
    # Get seasonal suggestions based on user location
    user_location = user_preferences.get("location", "default")
    seasonal_context = self._get_seasonal_suggestions(user_location)
```

### Recipe Deduplication Strategy
We prevent the AI from giving repetitive dinner ideas by passing recent history into the prompt:

```python
# Build recipe history context for deduplication
history_context = ""
if recent_recipes:
    recent_titles = [recipe.get("title", "") for recipe in recent_recipes[:5]]
    history_context = f"\n\nAvoid suggesting recipes similar to these recent meals: {', '.join(recent_titles)}"
```

### Cost Savings Calculation
EcoSnap rewards users by providing estimated savings directly alongside the generated recipe.

```python
# Override AI-estimated cost with calculated cost based on a hardcoded lookup map
cost_savings = self._calculate_cost_savings(items_list, user_pantry)
recipe_data["estimated_cost_saved"] = cost_savings["total_saved"]
recipe_data["cost_savings"] = cost_savings
```

---

## 🔒 Security & Performance

- **Rate Limiting:** IP-based rate limiting via `slowapi` (`10/minute` for health checks, `5/minute` for the AI triage endpoint) protects against abuse and API cost overruns.
- **API Key Security:** The `X-API-Key` header validates requests against the securely stored `api_secret`.

## ⚙️ Setup & Environment

Requires the following environment variables:
- `GEMINI_API_KEY`: Google Gemini API Key
- `FIREBASE_SERVICE_ACCOUNT`: Base64 encoded JSON representation of the Firebase Service Account
- `API_SECRET`: Key needed to authorize requests via the `X-API-Key` header.
