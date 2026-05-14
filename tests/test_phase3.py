#!/usr/bin/env python3
"""
Test script for Phase 3 implementation
Tests multi-recipe suggestions, cost optimization, nutritional analysis, and seasonal features
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.recipe_service import RecipeService

async def test_single_recipe():
    """Test single recipe generation with Phase 3 features"""
    print("🧪 Testing single recipe generation...")
    
    recipe_service = RecipeService()
    
    # Test data with expiring items
    expiring_items = [
        {"name": "chicken breast", "quantity": 2, "unit": "pieces", "hours_until_expiry": 12},
        {"name": "spinach", "quantity": 200, "unit": "grams", "hours_until_expiry": 8},
        {"name": "tomatoes", "quantity": 3, "unit": "pieces", "hours_until_expiry": 48}
    ]
    
    try:
        # Test single recipe generation
        result = await recipe_service.generate_recipe(
            expiring_items=expiring_items,
            dietary_restrictions=["halal"],
            user_id="test_user_123",
            multi_recipe=False
        )
        
        print("✅ Single recipe generated successfully!")
        print(f"📝 Title: {result.get('title', 'N/A')}")
        print(f"⏱️  Cook time: {result.get('cook_time_minutes', 'N/A')} minutes")
        print(f"💰 Cost saved: ${result.get('estimated_cost_saved', 'N/A')}")
        
        # Check for Phase 3 features
        if 'nutrition' in result:
            print("🥗 Nutritional info: ✓")
            nutrition = result['nutrition']
            print(f"   - Calories: {nutrition.get('calories', 'N/A')}")
            print(f"   - Protein: {nutrition.get('protein', 'N/A')}g")
        else:
            print("❌ Nutritional info: ✗")
            
        if 'cost_savings' in result:
            print("💸 Cost breakdown: ✓")
            cost = result['cost_savings']
            print(f"   - Items cost: ${cost.get('items_used_cost', 'N/A')}")
            print(f"   - Total saved: ${cost.get('total_saved', 'N/A')}")
        else:
            print("❌ Cost breakdown: ✗")
            
        if 'seasonal_context' in result:
            print("🌤️  Seasonal context: ✓")
            seasonal = result['seasonal_context']
            print(f"   - Location: {seasonal.get('location', 'N/A')}")
            print(f"   - Season: {seasonal.get('season', 'N/A')}")
        else:
            print("❌ Seasonal context: ✗")
            
        return True
        
    except Exception as e:
        print(f"❌ Single recipe test failed: {e}")
        return False

async def test_multi_recipe():
    """Test multi-recipe suggestion feature"""
    print("\n🧪 Testing multi-recipe suggestion...")
    
    recipe_service = RecipeService()
    
    # Test data with more varied items
    expiring_items = [
        {"name": "salmon", "quantity": 1, "unit": "piece", "hours_until_expiry": 6},
        {"name": "broccoli", "quantity": 300, "unit": "grams", "hours_until_expiry": 24},
        {"name": "rice", "quantity": 500, "unit": "grams", "hours_until_expiry": 72},
        {"name": "cheese", "quantity": 200, "unit": "grams", "hours_until_expiry": 36}
    ]
    
    try:
        # Test multi-recipe generation
        result = await recipe_service.generate_recipe(
            expiring_items=expiring_items,
            dietary_restrictions=None,
            user_id="test_user_123",
            multi_recipe=True
        )
        
        print("✅ Multi-recipe suggestion generated successfully!")
        
        if 'recipes' in result and len(result['recipes']) == 3:
            print("📋 3 recipe variants: ✓")
            for i, recipe in enumerate(result['recipes']):
                recipe_type = recipe.get('type', f'Variant {i+1}')
                title = recipe.get('title', 'N/A')
                cook_time = recipe.get('cook_time_minutes', 'N/A')
                print(f"   {i+1}. {recipe_type}: {title} ({cook_time} min)")
                
                # Check for Phase 3 features in each recipe
                if 'nutrition' in recipe:
                    print(f"      🥗 Nutrition: {recipe['nutrition'].get('calories', 'N/A')} cal")
                if 'estimated_cost_saved' in recipe:
                    print(f"      💰 Saves: ${recipe['estimated_cost_saved']}")
        else:
            print("❌ Expected 3 recipe variants")
            return False
            
        # Check for Phase 3 features at response level
        if 'cost_savings' in result:
            print("💸 Cost breakdown: ✓")
        if 'seasonal_context' in result:
            print("🌤️  Seasonal context: ✓")
            
        return True
        
    except Exception as e:
        print(f"❌ Multi-recipe test failed: {e}")
        return False

async def test_cost_calculation():
    """Test cost calculation functionality"""
    print("\n🧪 Testing cost calculation...")
    
    recipe_service = RecipeService()
    
    expiring_items = [
        {"name": "chicken", "quantity": 2, "unit": "pieces"},
        {"name": "spinach", "quantity": 200, "unit": "grams"},
        {"name": "unknown_item", "quantity": 1, "unit": "piece"}  # Test default cost
    ]
    
    try:
        cost_savings = recipe_service._calculate_cost_savings(expiring_items)
        
        print("✅ Cost calculation successful!")
        print(f"💰 Items cost: ${cost_savings.get('items_used_cost', 'N/A')}")
        print(f"🥫 Pantry cost: ${cost_savings.get('pantry_items_cost', 'N/A')}")
        print(f"💵 Total saved: ${cost_savings.get('total_saved', 'N/A')}")
        
        # Verify calculations make sense
        items_cost = cost_savings.get('items_used_cost', 0)
        if items_cost > 0:
            print("✅ Cost calculation logic working")
        else:
            print("❌ Cost calculation returned zero")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Cost calculation test failed: {e}")
        return False

async def test_seasonal_suggestions():
    """Test seasonal suggestion functionality"""
    print("\n🧪 Testing seasonal suggestions...")
    
    recipe_service = RecipeService()
    
    try:
        # Test different locations
        locations = ["philippines", "usa", "default", "unknown"]
        
        for location in locations:
            seasonal = recipe_service._get_seasonal_suggestions(location)
            
            print(f"🌍 {location.title()}:")
            print(f"   📅 Season: {seasonal.get('season', 'N/A')}")
            print(f"   💡 Suggestions: {len(seasonal.get('suggestions', []))} found")
            
            if seasonal.get('suggestions'):
                print(f"   🍽️  Example: {seasonal['suggestions'][0]}")
            
        print("✅ Seasonal suggestions working!")
        return True
        
    except Exception as e:
        print(f"❌ Seasonal suggestions test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Phase 3 Implementation Tests\n")
    
    tests = [
        ("Single Recipe", test_single_recipe),
        ("Multi-Recipe", test_multi_recipe),
        ("Cost Calculation", test_cost_calculation),
        ("Seasonal Suggestions", test_seasonal_suggestions)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 3 features working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed - check implementation")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
