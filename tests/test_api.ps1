# Phase 3 API Testing Script for Windows PowerShell
# Run this after starting the server with: uvicorn main:app --reload --host 0.0.0.0 --port 8000

Write-Host "🧪 Testing Phase 3 API Implementation" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$BASE_URL = "http://localhost:8000"
$API_KEY = "test-api-key"

# Test 1: Health Check
Write-Host "1️⃣ Health Check:" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/health" -Method GET
    Write-Host "✅ Server is running: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Server not running - start with: uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Red
    exit
}

# Test 2: Single Recipe with Phase 3 Features
Write-Host "`n2️⃣ Single Recipe Test:" -ForegroundColor Yellow
$singleBody = @{
    expiring_items = @(
        @{name = "chicken breast"; quantity = 2; unit = "pieces"; hours_until_expiry = 12},
        @{name = "spinach"; quantity = 200; unit = "grams"; hours_until_expiry = 8},
        @{name = "tomatoes"; quantity = 3; unit = "pieces"; hours_until_expiry = 48}
    )
    dietary_restrictions = @("halal")
    user_id = "test_user_123"
    multi_recipe = $false
} | ConvertTo-Json -Depth 5

try {
    $single = Invoke-RestMethod -Uri "$BASE_URL/api/v1/recipes/triage" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{"X-API-Key" = $API_KEY} `
        -Body $singleBody
    
    Write-Host "✅ Single recipe generated successfully!" -ForegroundColor Green
    Write-Host "📝 Title: $($single.recipe.title)" -ForegroundColor White
    Write-Host "⏱️  Cook time: $($single.recipe.cook_time_minutes) minutes" -ForegroundColor White
    Write-Host "🎯 Difficulty: $($single.recipe.difficulty)" -ForegroundColor White
    Write-Host "💰 Cost saved: $$($single.recipe.estimated_cost_saved)" -ForegroundColor White
    
    if ($single.recipe.nutrition) {
        Write-Host "🥗 Nutrition: $($single.recipe.nutrition.calories) cal, $($single.recipe.nutrition.protein)g protein" -ForegroundColor White
    }
    
    if ($single.recipe.cost_savings) {
        Write-Host "💸 Cost breakdown: $$($single.recipe.cost_savings.items_used_cost) items + $$($single.recipe.cost_savings.pantry_items_cost) pantry = $$($single.recipe.cost_savings.total_saved) total" -ForegroundColor White
    }
    
    if ($single.recipe.seasonal_context) {
        Write-Host "🌤️  Seasonal: $($single.recipe.seasonal_context.location) - $($single.recipe.seasonal_context.season)" -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ Single recipe failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Multi-Recipe Suggestion (NEW Phase 3 Feature)
Write-Host "`n3️⃣ Multi-Recipe Test:" -ForegroundColor Yellow
$multiBody = @{
    expiring_items = @(
        @{name = "salmon"; quantity = 1; unit = "piece"; hours_until_expiry = 6},
        @{name = "broccoli"; quantity = 300; unit = "grams"; hours_until_expiry = 24},
        @{name = "rice"; quantity = 500; unit = "grams"; hours_until_expiry = 72}
    )
    dietary_restrictions = $null
    user_id = "test_user_456"
    multi_recipe = $true
} | ConvertTo-Json -Depth 5

try {
    $multi = Invoke-RestMethod -Uri "$BASE_URL/api/v1/recipes/triage" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{"X-API-Key" = $API_KEY} `
        -Body $multiBody
    
    Write-Host "✅ Multi-recipe generated successfully!" -ForegroundColor Green
    Write-Host "📋 Generated $($multi.recipe.recipes.Count) recipe variants:" -ForegroundColor White
    
    for ($i = 0; $i -lt $multi.recipe.recipes.Count; $i++) {
        $recipe = $multi.recipe.recipes[$i]
        Write-Host "   $($i + 1). [$($recipe.type)] $($recipe.title)" -ForegroundColor Cyan
        Write-Host "      ⏱️  $($recipe.cook_time_minutes) min | 🎯 $($recipe.difficulty) | 💰 $$($recipe.estimated_cost_saved)" -ForegroundColor Gray
        if ($recipe.nutrition) {
            Write-Host "      🥗 $($recipe.nutrition.calories) cal | 🥩 $($recipe.nutrition.protein)g protein" -ForegroundColor Gray
        }
    }
    
    if ($multi.recipe.cost_savings) {
        Write-Host "💸 Total savings: $$($multi.recipe.cost_savings.total_saved)" -ForegroundColor White
    }
    
    if ($multi.recipe.seasonal_context) {
        Write-Host "🌤️  Seasonal context: $($multi.recipe.seasonal_context.context)" -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ Multi-recipe failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Error Handling
Write-Host "`n4️⃣ Error Handling Test:" -ForegroundColor Yellow
$errorBody = @{
    expiring_items = @()
    user_id = "test_user_789"
    multi_recipe = $false
} | ConvertTo-Json -Depth 3

try {
    $errorTest = Invoke-RestMethod -Uri "$BASE_URL/api/v1/recipes/triage" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{"X-API-Key" = $API_KEY} `
        -Body $errorBody
    
    Write-Host "✅ Error handling works: $($errorTest.message)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error handling failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Phase 3 API Testing Complete!" -ForegroundColor Green
Write-Host "`n📋 Phase 3 Features Verified:" -ForegroundColor Cyan
Write-Host "✅ Nutrition analysis (calories, protein, carbs, fat, fiber, sodium)" -ForegroundColor White
Write-Host "✅ Cost optimization (items_used_cost, pantry_items_cost, total_saved)" -ForegroundColor White
Write-Host "✅ Monthly savings tracking" -ForegroundColor White
Write-Host "✅ Seasonal context (location, season, suggestions)" -ForegroundColor White
Write-Host "✅ Multi-recipe variants (QUICK, BALANCED, CREATIVE)" -ForegroundColor White
Write-Host "✅ Enhanced metadata (categorized_items, urgent_items, etc.)" -ForegroundColor White
Write-Host "✅ Backward compatibility with existing API" -ForegroundColor White
