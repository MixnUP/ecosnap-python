# Triage Logic Enhancement Roadmap

This document outlines planned and proposed enhancements to the `/api/v1/recipes/triage` endpoint to make recipe generation smarter, more personalized, and more effective at reducing food waste.

---

## Current State

**Endpoint:** `POST /api/v1/recipes/triage`
**Current Behavior:**
- Accepts `expiring_items` array from frontend
- Calls Gemini (`gemma-4-31b-it`) with basic prompt
- Returns single recipe suggestion
- No user context, history, or prioritization

---

## Phase 1: Quick Wins (Immediate)

### 1.1 Food Category Detection & Prioritization
**Status:** Proposed  
**Effort:** Low (30 min)  
**Impact:** Medium

**Implementation:**
```python
FOOD_CATEGORIES = {
    "proteins": ["chicken", "pork", "beef", "fish", "tofu", "eggs", "shrimp"],
    "vegetables": ["spinach", "broccoli", "carrots", "onions", "peppers"],
    "starches": ["rice", "pasta", "potatoes", "bread"],
    "dairy": ["milk", "cheese", "yogurt", "butter"],
    "pantry": ["oil", "spices", "garlic", "onions"]
}
```

**Logic:**
- Detect categories from item names
- Prioritize proteins as "main dish" base
- Suggest complementary categories missing from expiring items
- Build smarter prompt: "Create a pork-based dinner with spinach side dish"

**Benefits:**
- More coherent meal structure
- Better ingredient pairing suggestions
- Natural fallback when items don't match well

---

### 1.2 Expiry Urgency Weighting
**Status:** Proposed  
**Effort:** Low (20 min)  
**Impact:** High

**Implementation:**
Frontend already sends `hours_until_expiry`. Backend should:
```python
# Sort by urgency
items.sort(key=lambda x: x.get("hours_until_expiry", 999))

# Prioritize items expiring < 24h in prompt
urgent_items = [i for i in items if i.get("hours_until_expiry", 999) < 24]
regular_items = [i for i in items if i.get("hours_until_expiry", 999) >= 24]
```

**Prompt Enhancement:**
```
CRITICAL - Must use these items (expire within 24h): {urgent_items}
Also incorporate if possible: {regular_items}
```

**Benefits:**
- Prevents waste of most urgent items
- Uses "nice to have" items as supplementary

---

### 1.3 Pantry Staples Assumption
**Status:** Proposed  
**Effort:** Low (15 min)  
**Impact:** Medium

**Implementation:**
Hardcode common pantry items in prompt context:
```python
PANTRY_STAPLES = ["salt", "pepper", "oil", "garlic", "onions", "soy sauce", "vinegar"]

prompt += f"""
Assume the user has these pantry staples: {', '.join(PANTRY_STAPLES)}
Do not list these as required ingredients unless quantity matters.
"""
```

**Benefits:**
- Shorter ingredient lists
- More realistic recipes
- Better user experience (users don't need to buy basics)

---

## Phase 2: Context Integration (Short-term)

### 2.1 Fetch User Preferences from Firebase
**Status:** Proposed  
**Effort:** Medium (2-3 hours)  
**Impact:** High

**Data to Fetch:**
```typescript
userPreferences: {
  cuisineTypes: ["italian", "asian", "mexican"],  // preferred cuisines
  spiceLevel: "medium",                           // mild/medium/spicy
  cookingSkill: "intermediate",                   // beginner/intermediate/advanced
  dietaryRestrictions: ["halal"],                 // persistent restrictions
  servingSize: 2,                                 // household size
  maxCookTime: 45,                                // minutes preference
}
```

**Implementation:**
```python
async def get_user_preferences(user_id: str) -> dict:
    db = get_firestore_db()
    doc = await db.collection("users").document(user_id).get()
    return doc.to_dict().get("preferences", {})
```

**Prompt Enhancement:**
```
User preferences:
- Cuisine: {cuisineTypes}
- Spice level: {spiceLevel}
- Cooking time max: {maxCookTime} minutes
- Skill level: {cookingSkill}
```

**Benefits:**
- Personalized recipe suggestions
- Respects household constraints
- Better user satisfaction

---

### 2.2 Recipe History Deduplication
**Status:** Proposed  
**Effort:** Medium (3-4 hours)  
**Impact:** Medium

**Data to Store:**
```typescript
recipeHistory: {
  recipeId: string,
  title: string,
  ingredients: string[],
  generatedAt: timestamp,
  embedding: vector[384]  // for similarity comparison
}
```

**Implementation:**
```python
async def get_recent_recipes(user_id: str, days: int = 7) -> list:
    db = get_firestore_db()
    cutoff = datetime.now() - timedelta(days=days)
    
    query = (db.collection("recipe_history")
               .where("user_id", "==", user_id)
               .where("generated_at", ">=", cutoff)
               .order_by("generated_at", direction="DESCENDING"))
    
    return [doc.to_dict() for doc in query.stream()]
```

**Deduplication Logic:**
- Generate 3 candidate recipes from Gemini
- Calculate semantic similarity to recent recipes
- Return least similar option
- Store all 3 with "chosen" flag for learning

**Benefits:**
- Avoids repetitive meals
- Encourages culinary variety
- Learns user preferences over time

---

### 2.3 Smart Pantry Integration
**Status:** Proposed  
**Effort:** Medium (2-3 hours)  
**Impact:** High

**Data to Fetch:**
```typescript
userPantry: [
  { name: "olive oil", category: "oil", quantity: 500, unit: "ml" },
  { name: "garlic", category: "vegetable", quantity: 3, unit: "cloves" }
]
```

**Implementation:**
```python
async def get_user_pantry(user_id: str) -> list:
    db = get_firestore_db()
    docs = db.collection("users").document(user_id).collection("pantry").stream()
    return [doc.to_dict() for doc in docs]
```

**Prompt Enhancement:**
```
User has these pantry items available: {pantry_items}
Suggest recipes that incorporate pantry items + expiring items efficiently.
```

**Benefits:**
- More realistic ingredient lists
- Encourages complete meal planning
- Reduces redundant purchases

---

## Phase 3: Advanced Features (Long-term)

### 3.1 Multi-Recipe Suggestion
**Status:** Proposed  
**Effort:** High (6-8 hours)  
**Impact:** High
**Constraint:** Hits rate limit (5 req/min currently)

**Implementation Options:**

**Option A: Sequential Calls (Slow)**
Call Gemini 3x for different recipe types:
```python
recipes = await asyncio.gather(
    generate_quick_recipe(items),      # 15 min, minimal
    generate_balanced_recipe(items),   # 30 min, complete
    generate_creative_recipe(items)    # uses most items
)
```

**Option B: Single Prompt with 3 Variants**
Modify prompt to return 3 options in one call:
```
Generate 3 different dinner options:
1. QUICK (15 min, minimal ingredients)
2. BALANCED (30 min, nutritionally complete)
3. CREATIVE (uses maximum expiring items)

Return as JSON array with 3 recipe objects.
```

**Option C: Cache Common Patterns**
Pre-generate recipes for common ingredient combinations and cache them.

**Recommended:** Option B (fits within single Gemini call)

**Benefits:**
- User choice and variety
- Different solutions for different time constraints
- Higher satisfaction

---

### 3.2 Cost Optimization Engine
**Status:** Proposed  
**Effort:** Medium (3-4 hours)  
**Impact:** Medium

**Implementation:**
Store estimated costs per item:
```python
item_costs = {
    "chicken breast": 8.50,
    "salmon fillet": 12.00,
    "spinach": 3.00
}

total_saved = sum(
    item.get("estimated_cost", 5.00) * item.get("quantity", 1)
    for item in expiring_items
)
```

**Features:**
- Calculate actual money saved per recipe
- Track cumulative savings per user
- Gamification: "You've saved $47 this month!"
- Leaderboards (optional)

**Response Enhancement:**
```json
{
  "recipe": { ... },
  "savings": {
    "items_used_cost": 15.50,
    "pantry_items_cost": 3.00,
    "total_saved": 18.50,
    "monthly_total": 47.20
  }
}
```

**Benefits:**
- Quantifies value proposition
- Gamification drives engagement
- Clear ROI for users

---

### 3.3 Nutritional Analysis
**Status:** Proposed  
**Effort:** High (8-10 hours)  
**Impact:** Medium

**Implementation:**
Use Gemini or external API to estimate:
```json
{
  "nutrition": {
    "calories": 450,
    "protein": 35,
    "carbs": 20,
    "fat": 25,
    "fiber": 8
  }
}
```

**Features:**
- Estimate macros per serving
- Compare to daily recommended values
- Flag high-sodium or high-sugar recipes
- Suggest healthier substitutions

**Prompt Enhancement:**
```
Include estimated nutritional information per serving:
- Calories, protein, carbs, fat, fiber
- Note any health considerations
```

**Benefits:**
- Appeals to health-conscious users
- Better meal planning
- Competitive advantage over basic recipe apps

---

### 3.4 Seasonal & Local Optimization
**Status:** Proposed  
**Effort:** High (6-8 hours)  
**Impact:** Low-Medium

**Implementation:**
Detect user location from Firebase, suggest seasonal recipes:
```python
SEASONAL_RECIPES = {
    "philippines": {
        "summer": ["gazpacho", "ceviche", "cold noodles"],
        "rainy": ["sinigang", "arroz caldo", "hot pot"]
    }
}
```

**Benefits:**
- Culturally relevant suggestions
- Seasonal ingredient compatibility
- Local flavor preferences

---

## Implementation Priority Matrix

| Enhancement | Effort | Impact | Phase | Dependencies |
|-------------|--------|--------|-------|--------------|
| Category Detection | Low | Medium | 1 | None |
| Expiry Urgency | Low | High | 1 | None |
| Pantry Staples | Low | Medium | 1 | None |
| User Preferences | Medium | High | 2 | Firebase read |
| Recipe History | Medium | Medium | 2 | Firestore storage |
| Pantry Integration | Medium | High | 2 | Firebase read |
| Multi-Recipe | High | High | 3 | None (prompt change) |
| Cost Engine | Medium | Medium | 3 | Item cost data |
| Nutrition Analysis | High | Medium | 3 | None |
| Seasonal | High | Low | 3 | Location data |

---

## Recommended Next Steps

1. **Immediate:** Implement Phase 1 (categories, urgency, staples) - 1 hour total
2. **This Week:** Add user preferences fetch from Firebase
3. **Next Sprint:** Implement multi-recipe suggestion (Option B)
4. **Future:** Cost tracking for gamification

---

## Technical Notes

### Rate Limit Considerations
- Current: 5 req/min to Gemini
- Each enhancement should minimize additional API calls
- Cache aggressively where possible

### Firebase Reads
- User preferences: 1 read per request
- Pantry items: 1 read per request (if implemented)
- Recipe history: 1 read per request (can be cached)

### Cost Analysis
- Additional Firebase reads: ~$0.06 per 100k reads
- Gemini calls remain the bottleneck at 5 req/min
- No additional AI costs for most enhancements

---

**Last Updated:** 2026-05-09  
**Status:** Draft - Ready for review
