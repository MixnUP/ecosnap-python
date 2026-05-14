#!/bin/bash

# Phase 3 API Testing Script
# Run this after starting the server with: uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo "🧪 Testing Phase 3 API Implementation"
echo "====================================="

BASE_URL="http://localhost:8000"
API_KEY="test-api-key"

# Test 1: Health Check
echo "1️⃣ Health Check:"
curl -s -X GET "$BASE_URL/health" | jq .
echo ""

# Test 2: Single Recipe with Phase 3 Features
echo "2️⃣ Single Recipe Test:"
curl -s -X POST "$BASE_URL/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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
  }' | jq '.recipe | {title, cook_time_minutes, difficulty, estimated_cost_saved, nutrition, cost_savings, seasonal_context}'
echo ""

# Test 3: Multi-Recipe Suggestion (NEW Phase 3 Feature)
echo "3️⃣ Multi-Recipe Test:"
curl -s -X POST "$BASE_URL/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
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
  }' | jq '.recipe | {recipes: [.recipes[].{type, title, cook_time_minutes, difficulty, estimated_cost_saved}], cost_savings, seasonal_context}'
echo ""

# Test 4: Error Handling
echo "4️⃣ Error Handling (Empty Items):"
curl -s -X POST "$BASE_URL/api/v1/recipes/triage" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "expiring_items": [],
    "user_id": "test_user_789",
    "multi_recipe": false
  }' | jq .
echo ""

echo "🎉 Testing complete!"
echo ""
echo "📋 Phase 3 Features to Verify:"
echo "✅ Nutrition analysis (calories, protein, carbs, fat, fiber, sodium)"
echo "✅ Cost optimization (items_used_cost, pantry_items_cost, total_saved)"
echo "✅ Monthly savings tracking"
echo "✅ Seasonal context (location, season, suggestions)"
echo "✅ Multi-recipe variants (QUICK, BALANCED, CREATIVE)"
echo "✅ Enhanced metadata (categorized_items, urgent_items, etc.)"
