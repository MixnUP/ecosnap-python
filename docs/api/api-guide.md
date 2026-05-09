# EcoSnap API Guide & Reference

This document serves as the master guide for interacting with the EcoSnap FastAPI backend.

**Purpose:** AI-powered recipe generation for expiring ingredients  
**Base URL:** `https://ecosnap-api-production.onrender.com` (production) / `http://localhost:8000` (local)  
**Version:** 1.0.0

---

## 🔐 Authentication

All endpoints except `/health` require an API Key passed via the `X-API-Key` header.

| Attribute | Value |
| :--- | :--- |
| **Header Name** | `X-API-Key` |
| **Local Value** | `API_SECRET` from `.env` |
| **Production Value** | Configured in Render environment variables |

**Example:**
```bash
curl -H "X-API-Key: your-secret-key" \
     https://api.ecosnap.app/api/v1/recipes/triage
```

---

## 💻 Local Development Setup

### Prerequisites

Ensure Python 3.11+ and virtual environment:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required variables:**
- `FIREBASE_SERVICE_ACCOUNT` - Base64 encoded Firebase service account JSON
  - Download from Firebase Console > Project Settings > Service Accounts
  - Encode: `cat service-account.json | base64 | pbcopy` (Mac) or `cat service-account.json | base64 -w 0` (Linux)
- `GEMINI_API_KEY` - Google Gemini API key
- `API_SECRET` - Your API security key

### Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Base URL:** `http://localhost:8000`
- **Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)

---

## 🚦 Rate Limits

Rate limits are enforced per-IP to prevent abuse.

| Endpoint | Limit | Description |
| :--- | :--- | :--- |
| `GET /health` | 10/min | Health check |
| `POST /api/v1/recipes/triage` | 20/min | Recipe generation (AI calls) |

**429 Response:**
```json
{
  "error": "Rate limit exceeded"
}
```

---

## 🛠 Endpoint Reference

### 1. Health Check
`GET /health`

Simple status check for monitoring and load balancers.

*   **Auth:** None
*   **Rate Limit:** 10/min

**Response:**
```json
{
  "status": "ok",
  "service": "ecosnap-api"
}
```

---

### 2. Triage Dinner
`POST /api/v1/recipes/triage`

Generate a dinner recipe from expiring ingredients using Gemini AI.

*   **Auth:** Required (`X-API-Key` header)
*   **Rate Limit:** 20/min
*   **Content-Type:** `application/json`

**Request Body:**
```json
{
  "expiring_items": [
    {
      "name": "Chicken Breast",
      "quantity": 0.5,
      "unit": "kg",
      "category": "poultry"
    },
    {
      "name": "Spinach",
      "quantity": 1,
      "unit": "bag",
      "category": "vegetables"
    }
  ],
  "dietary_restrictions": ["gluten-free", "dairy-free"]
}
```

**Parameters:**

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `expiring_items` | `array` | Yes | List of expiring ingredients |
| `expiring_items[].name` | `string` | Yes | Ingredient name |
| `expiring_items[].quantity` | `number` | No | Amount (default: 1) |
| `expiring_items[].unit` | `string` | No | Unit (default: "item") |
| `expiring_items[].category` | `string` | No | Food category |
| `dietary_restrictions` | `array` | No | Dietary filters (e.g., "vegetarian", "gluten-free") |

**Flow:**
1. Validate API key
2. Parse expiring items from request
3. Build structured prompt for Gemini
4. Call Gemini API (gemma-4-31b model)
5. Parse JSON response
6. Return formatted recipe or fallback

**Success Response (200):**
```json
{
  "success": true,
  "recipe": {
    "title": "Pan-Seared Chicken with Wilted Spinach",
    "ingredients": [
      "0.5 kg chicken breast, sliced",
      "1 bag fresh spinach"
    ],
    "instructions": [
      "Season chicken with salt and pepper.",
      "Heat pan over medium-high heat, add oil.",
      "Sear chicken 4-5 minutes per side until golden.",
      "Add spinach to pan, toss until wilted (2 min).",
      "Serve immediately."
    ],
    "cook_time_minutes": 25,
    "difficulty": "easy",
    "estimated_cost_saved": 12.50,
    "expiring_items_used": [
      { "name": "Chicken Breast", "quantity": 0.5, "unit": "kg" }
    ]
  }
}
```

**Empty Items Response (200):**
```json
{
  "success": true,
  "recipe": null,
  "message": "No items provided"
}
```

**Error Response (500):**
```json
{
  "detail": "Recipe generation failed"
}
```

**Fallback Recipe:**
If Gemini fails or returns invalid JSON, a simple fallback recipe is generated:
```json
{
  "title": "Quick Dinner with Chicken Breast",
  "fallback": true,
  "ingredients": [...],
  "instructions": ["Basic preparation steps..."]
}
```

---

## 🧪 Testing with cURL

### Local Development

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Generate Recipe:**
```bash
curl -X POST "http://localhost:8000/api/v1/recipes/triage" \
     -H "X-API-Key: your-local-secret" \
     -H "Content-Type: application/json" \
     -d '{
       "expiring_items": [
         {"name": "Chicken Breast", "quantity": 0.5, "unit": "kg"},
         {"name": "Spinach", "quantity": 1, "unit": "bag"}
       ],
       "dietary_restrictions": []
     }'
```

**With Dietary Restrictions:**
```bash
curl -X POST "http://localhost:8000/api/v1/recipes/triage" \
     -H "X-API-Key: your-local-secret" \
     -H "Content-Type: application/json" \
     -d '{
       "expiring_items": [
         {"name": "Tofu", "quantity": 300, "unit": "g"},
         {"name": "Broccoli", "quantity": 1, "unit": "head"}
       ],
       "dietary_restrictions": ["vegan", "gluten-free"]
     }'
```

### Production (Staging)

```bash
curl -X POST "https://ecosnap-api-staging.onrender.com/api/v1/recipes/triage" \
     -H "X-API-Key: $STAGING_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"expiring_items": [{"name": "Salmon", "quantity": 0.4, "unit": "kg"}]}'
```

---

## 🔧 Development Tips

### Check Syntax
```bash
# Verify main file compiles
python3 -m py_compile main.py && echo "Syntax OK"

# Verify service file compiles
python3 -m py_compile services/recipe_service.py && echo "Syntax OK"
```

### Run Tests
```bash
pytest tests/ -v
```

### View Logs (Render)
```bash
render logs --service ecosnap-api-production
```

## 🛡 Security Notes

*   **API Key:** Never commit `API_SECRET` to version control. Use Render environment variables.
*   **Gemini API Key:** Stored in environment, not exposed to clients.
*   **Input Validation:** All requests validated via Pydantic models.
*   **Error Masking:** Internal exceptions logged server-side; generic messages returned to clients.
*   **Rate Limiting:** Per-IP limits prevent brute force and abuse.
*   **CORS:** Configured for specific frontend origins only.

---

## 📊 Architecture Overview

```
Frontend (Next.js/Firebase)
    │
    ├── Queries Firebase directly for inventory
    │
    └── POST /api/v1/recipes/triage
            │
            ▼
    FastAPI Backend (Render)
            │
            ├── Validates API Key
            ├── Builds prompt from items
            │
            └── Calls Gemini API (gemma-4-31b)
                    │
                    └── Returns structured recipe
```

**Key Design:** Backend is AI-only. Frontend handles all inventory/user data via Firebase.

---

## 📝 Environment Variables Reference

| Variable | Required | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Yes | Google Gemini API access |
| `API_SECRET` | Yes | API authentication key |
| `FIREBASE_SERVICE_ACCOUNT` | Yes | Firebase Admin SDK credentials |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `PYTHON_VERSION` | No | Render uses 3.11.0 |

---

## ✅ Checklist: Integration Complete

- [ ] API key obtained and configured
- [ ] `/health` responds 200
- [ ] Recipe generation returns valid JSON
- [ ] Dietary restrictions filter correctly
- [ ] Rate limits understood (20/min for recipes)
- [ ] Fallback behavior tested (Gemini failure scenario)
- [ ] Error handling implemented on frontend
- [ ] CORS origins configured for production domain

---

**Last Updated:** 2024-XX-XX  
**Contact:** [Your team contact]
