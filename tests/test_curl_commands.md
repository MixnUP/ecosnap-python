# Phase 3 API Testing with cURL

## Server Setup
First, start the server:
```bash
cd c:\Users\jamis\Downloads\charie\ecosnap-python
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Test 1: Health Check
Verify server is running:
```bash
curl -X GET "http://localhost:8000/health"
```

Expected response:
```json
{"status": "ok", "service": "ecosnap-api"}
```

## Test 2: Single Recipe (Backward Compatible)
Test single recipe generation with Phase 3 features:

```bash
curl -X POST "http://localhost:8000/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "expiring_items": [
      {
        "name": "chicken breast",
        "quantity": 2,
        "unit": "pieces",
        "hours_until_expiry": 12
      },
      {
        "name": "spinach",
        "quantity": 200,
        "unit": "grams", 
        "hours_until_expiry": 8
      },
      {
        "name": "tomatoes",
        "quantity": 3,
        "unit": "pieces",
        "hours_until_expiry": 48
      }
    ],
    "dietary_restrictions": ["halal"],
    "user_id": "test_user_123",
    "multi_recipe": false
  }'
```

### Expected Response Features:
- ✅ `nutrition` object with calories, protein, carbs, fat, fiber, sodium
- ✅ `cost_savings` breakdown with items_used_cost, pantry_items_cost, total_saved
- ✅ `monthly_savings` with cumulative tracking
- ✅ `seasonal_context` with location and seasonal suggestions
- ✅ Enhanced metadata (categorized_items, urgent_items, etc.)

## Test 3: Multi-Recipe (New Phase 3 Feature)
Test multi-recipe suggestion with 3 variants:

```bash
curl -X POST "http://localhost:8000/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "expiring_items": [
      {
        "name": "salmon",
        "quantity": 1,
        "unit": "piece",
        "hours_until_expiry": 6
      },
      {
        "name": "broccoli",
        "quantity": 300,
        "unit": "grams",
        "hours_until_expiry": 24
      },
      {
        "name": "rice",
        "quantity": 500,
        "unit": "grams",
        "hours_until_expiry": 72
      }
    ],
    "dietary_restrictions": null,
    "user_id": "test_user_456",
    "multi_recipe": true
  }'
```

### Expected Multi-Recipe Response:
- ✅ `recipes` array with 3 objects: QUICK, BALANCED, CREATIVE
- ✅ Each recipe has individual `nutrition` analysis
- ✅ Each recipe has individual `estimated_cost_saved`
- ✅ Response-level `cost_savings` and `seasonal_context`
- ✅ Different cook times (15, 30, 45+ minutes)
- ✅ Progressive difficulty levels (easy, medium, hard)

## Test 4: Error Handling
Test with invalid/expiring items:

```bash
curl -X POST "http://localhost:8000/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "expiring_items": [],
    "user_id": "test_user_789",
    "multi_recipe": false
  }'
```

Expected response:
```json
{"success": true, "recipe": null, "message": "No items provided"}
```

## Test 5: Rate Limiting
Test rate limiting (should work after 5 requests in 1 minute):

```bash
# Run this 6 times quickly to test rate limiting
curl -X POST "http://localhost:8000/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"expiring_items": [{"name": "test", "quantity": 1}], "multi_recipe": false}'
```

## Test 6: API Key Validation
Test with missing/invalid API key:

```bash
curl -X POST "http://localhost:8000/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -d '{"expiring_items": [{"name": "test", "quantity": 1}], "multi_recipe": false}'
```

Expected response: `403 Forbidden`

## Phase 3 Feature Verification Checklist

### Single Recipe Response Should Include:
- [ ] `title`, `ingredients`, `instructions`, `cook_time_minutes`, `difficulty`
- [ ] `nutrition` object with calories, protein, carbs, fat, fiber, sodium, health_notes
- [ ] `estimated_cost_saved` (calculated from ITEM_COSTS)
- [ ] `cost_savings` object with items_used_cost, pantry_items_cost, total_saved
- [ ] `monthly_savings` object with monthly_total
- [ ] `seasonal_context` object with location, season, suggestions, context
- [ ] `expiring_items_used`, `categorized_items`, `urgent_items` arrays
- [ ] `user_preferences`, `user_pantry` objects

### Multi-Recipe Response Should Include:
- [ ] `recipes` array with exactly 3 recipe objects
- [ ] Each recipe has `type`: "QUICK", "BALANCED", "CREATIVE"
- [ ] Each recipe has individual `nutrition` analysis
- [ ] Each recipe has individual `estimated_cost_saved`
- [ ] Response-level `cost_savings`, `monthly_savings`, `seasonal_context`
- [ ] Progressive cook times: ~15, ~30, ~45+ minutes
- [ ] Progressive difficulty: easy, medium, hard

## PowerShell Alternative (Windows)

If using PowerShell on Windows:

```powershell
# Test 2: Single Recipe
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/recipes/triage" `
  -Method POST `
  -ContentType "application/json" `
  -Headers @{"X-API-Key" = "your-api-key-here"} `
  -Body '{
    "expiring_items": [
      {"name": "chicken breast", "quantity": 2, "unit": "pieces", "hours_until_expiry": 12},
      {"name": "spinach", "quantity": 200, "unit": "grams", "hours_until_expiry": 8},
      {"name": "tomatoes", "quantity": 3, "unit": "pieces", "hours_until_expiry": 48}
    ],
    "dietary_restrictions": ["halal"],
    "user_id": "test_user_123",
    "multi_recipe": false
  }' | ConvertTo-Json -Depth 10

# Test 3: Multi-Recipe
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/recipes/triage" `
  -Method POST `
  -ContentType "application/json" `
  -Headers @{"X-API-Key" = "your-api-key-here"} `
  -Body '{
    "expiring_items": [
      {"name": "salmon", "quantity": 1, "unit": "piece", "hours_until_expiry": 6},
      {"name": "broccoli", "quantity": 300, "unit": "grams", "hours_until_expiry": 24},
      {"name": "rice", "quantity": 500, "unit": "grams", "hours_until_expiry": 72}
    ],
    "user_id": "test_user_456",
    "multi_recipe": true
  }' | ConvertTo-Json -Depth 10
```

## Quick Test Script

Save this as `test_api.ps1` and run:

```powershell
# Test API endpoints
$baseUrl = "http://localhost:8000"
$apiKey = "your-api-key-here"

Write-Host "🧪 Testing Phase 3 API Implementation" -ForegroundColor Cyan

# Health check
Write-Host "`n1️⃣ Health Check:" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✅ $health" -ForegroundColor Green
} catch {
    Write-Host "❌ Server not running" -ForegroundColor Red
    exit
}

# Single recipe test
Write-Host "`n2️⃣ Single Recipe Test:" -ForegroundColor Yellow
$singleBody = @{
    expiring_items = @(
        @{name = "chicken breast"; quantity = 2; unit = "pieces"; hours_until_expiry = 12},
        @{name = "spinach"; quantity = 200; unit = "grams"; hours_until_expiry = 8}
    )
    dietary_restrictions = @("halal")
    user_id = "test_user_123"
    multi_recipe = $false
} | ConvertTo-Json -Depth 5

try {
    $single = Invoke-RestMethod -Uri "$baseUrl/api/v1/recipes/triage" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{"X-API-Key" = $apiKey} `
        -Body $singleBody
    
    Write-Host "✅ Single recipe generated" -ForegroundColor Green
    Write-Host "📝 Title: $($single.recipe.title)" -ForegroundColor White
    Write-Host "💰 Cost saved: $$($single.recipe.estimated_cost_saved)" -ForegroundColor White
    Write-Host "🥗 Nutrition: $($single.recipe.nutrition.calories) cal" -ForegroundColor White
} catch {
    Write-Host "❌ Single recipe failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Multi-recipe test
Write-Host "`n3️⃣ Multi-Recipe Test:" -ForegroundColor Yellow
$multiBody = @{
    expiring_items = @(
        @{name = "salmon"; quantity = 1; unit = "piece"; hours_until_expiry = 6},
        @{name = "broccoli"; quantity = 300; unit = "grams"; hours_until_expiry = 24}
    )
    user_id = "test_user_456"
    multi_recipe = $true
} | ConvertTo-Json -Depth 5

try {
    $multi = Invoke-RestMethod -Uri "$baseUrl/api/v1/recipes/triage" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{"X-API-Key" = $apiKey} `
        -Body $multiBody
    
    Write-Host "✅ Multi-recipe generated" -ForegroundColor Green
    Write-Host "📋 Recipes: $($multi.recipe.recipes.Count) variants" -ForegroundColor White
    for ($i = 0; $i -lt $multi.recipe.recipes.Count; $i++) {
        $recipe = $multi.recipe.recipes[$i]
        Write-Host "   $($i + 1). $($recipe.type): $($recipe.title) ($($recipe.cook_time_minutes) min)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Multi-recipe failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Testing complete!" -ForegroundColor Green
```

Run with: `.\test_api.ps1`
