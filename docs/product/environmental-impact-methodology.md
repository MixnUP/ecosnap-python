# Environmental Impact Calculation Methodology

## Source

**Primary Study:** Poore, J., & Nemecek, T. (2018). Reducing food's environmental impacts through producers and consumers. *Science*, 360(6392), 987-992.

**Publisher:** Our World in Data (ourworldindata.org)  
**Data Coverage:** 38,000 commercial farms across 119 countries  
**Metric:** CO₂-equivalents (CO₂eq) - includes CO₂, methane, and nitrous oxide weighted by 100-year global warming potential  
**Scope:** Full lifecycle from land use change through farm, processing, transport, retail, and packaging

---

## Emission Factors by Food Category

Based on Poore & Nemecek (2018) - kg CO₂eq per kg of food product:

| Category | Food Item | Emissions (kg CO₂eq/kg) | Notes |
|----------|-----------|------------------------|-------|
| **Red Meat** | Beef | 60.0 | Highest emitter; 80%+ from land use + farm |
| | Lamb | 24.0 | Primarily land use and enteric fermentation |
| **Dairy** | Cheese | 21.0 | Concentrated milk products = concentrated emissions |
| | Milk | 3.0 | Lower due to lower density |
| **Poultry/Fish** | Pork | 7.0 | |
| | Poultry (Chicken) | 6.0 | Significantly lower than ruminants |
| | Fish (farmed) | 5.0 | Varies by species; average used |
| | Eggs | 4.5 | Per kg of eggs |
| **Grains** | Rice | 4.0 | Methane from flooded paddies |
| | Wheat | 1.5 | |
| | Other grains | 1.5 | Corn, oats, barley |
| **Produce** | Vegetables (average) | 2.0 | Range: 0.5-4.0 |
| | Fruits (average) | 1.0 | Range: 0.3-3.0 |
| | Root vegetables | 0.5 | Potatoes, carrots, onions |
| **Legumes/Nuts** | Peas, beans, lentils | 1.0 | Lowest protein sources |
| | Nuts | 1.0 | Almonds higher (~3.0), others lower |

---

## Calculation Formula

### Basic Calculation

```
co2_saved_kg = Σ (quantity_kg × emission_factor_kg_per_kg)
```

### Example Calculation

User cooks dinner using expiring items:
- 0.5 kg chicken breast: 0.5 × 6.0 = **3.0 kg CO₂eq**
- 0.3 kg spinach: 0.3 × 2.0 = **0.6 kg CO₂eq**
- 0.2 kg tomatoes: 0.2 × 2.0 = **0.4 kg CO₂eq**

**Total CO₂ Offset: 4.0 kg CO₂eq**

---

## Implementation in EcoSnap

### Category Mapping

Map inventory items to emission categories:

```javascript
const emissionFactors = {
  'beef': 60.0,
  'lamb': 24.0,
  'cheese': 21.0,
  'pork': 7.0,
  'chicken': 6.0,
  'poultry': 6.0,
  'fish': 5.0,
  'eggs': 4.5,
  'rice': 4.0,
  'wheat': 1.5,
  'bread': 1.5,
  'pasta': 1.5,
  'vegetables': 2.0,
  'leafy_greens': 2.0,
  'fruits': 1.0,
  'root_vegetables': 0.5,
  'potatoes': 0.5,
  'legumes': 1.0,
  'beans': 1.0,
  'lentils': 1.0,
  'nuts': 1.0,
  'milk': 3.0,
  'dairy': 3.0,
  'default': 2.0  // Conservative average for unknown items
};
```

### Quantity Normalization

Convert user-input quantities to kilograms:

```javascript
const unitConversions = {
  'kg': 1.0,
  'g': 0.001,
  'gram': 0.001,
  'lb': 0.453592,
  'pound': 0.453592,
  'oz': 0.0283495,
  'ounce': 0.0283495,
  'item': 0.15,    // Average piece of produce
  'piece': 0.15,
  'pack': 0.5,     // Average pack size
  'bag': 0.5,
  'bunch': 0.2,    // Herbs/greens
  'bottle': 1.0,   // Liquids (rough)
  'can': 0.4,
  'carton': 1.0
};
```

### Impact Receipt Display

```javascript
function calculateImpact(items) {
  let totalCO2 = 0;
  let estimatedValue = 0;
  
  items.forEach(item => {
    const factor = emissionFactors[item.category] || emissionFactors['default'];
    const kg = item.quantity * (unitConversions[item.unit] || unitConversions['item']);
    totalCO2 += kg * factor;
    estimatedValue += kg * 13.0;  // $13/kg average food cost
  });
  
  return {
    co2_saved_kg: Math.round(totalCO2 * 10) / 10,
    money_saved_usd: Math.round(estimatedValue * 100) / 100,
    streak_days: user.streak_counter
  };
}
```

---

## Key Insights from Source Study

### Why These Numbers Matter

1. **Transport is negligible:** <10% of emissions for most foods (<0.5% for beef)
   - *Implication:* Local vs. imported has minimal impact on carbon footprint

2. **Land use + farm stage dominates:** 80%+ of footprint for most foods
   - *Implication:* Focus on food type, not food miles

3. **Ruminant meat vs. plant-based:** 10-60x difference in emissions
   - *Implication:* Replacing beef with legumes has massive impact

### Limitations & Caveats

1. **Averages across 119 countries:** Individual farms may vary ±50%
2. **Organic vs. conventional:** Not differentiated in this dataset
3. **Seasonal variations:** Not captured (e.g., greenhouse tomatoes in winter)
4. **Processing level:** Raw ingredients assumed; processed foods higher
5. **User estimation error:** Quantity/unit conversions introduce ±20% error

### Uncertainty Range

Display to users with appropriate precision:
- **High confidence** (±10%): Beef, lamb, dairy, poultry
- **Medium confidence** (±25%): Vegetables, fruits (varies by type/season)
- **Low confidence** (±50%): Mixed dishes, processed foods, "default" category

---

## Alternative Sources for Future Reference

| Source | Year | Scope | Notes |
|--------|------|-------|-------|
| Poore & Nemecek | 2018 | 38,000 farms, 119 countries | **Current gold standard** |
| Clune et al. | 2017 | Systematic review | Meta-analysis, similar findings |
| IPCC AR6 WG3 | 2022 | Global assessment | Chapter 5: Food systems |
| FAO LEAP | 2022 | Livestock guidelines | Methodology framework |

---

## Legal/Disclaimer Text

Display to users:

> *"CO₂ estimates based on average lifecycle emissions from Poore & Nemecek (2018), covering 38,000 farms globally. Actual emissions vary by production method, season, and location. These are estimates for awareness purposes only."*

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-XX-XX | Initial implementation based on Poore & Nemecek 2018 |

---

*Document Status: Based on verified peer-reviewed research (Science, 2018). Emission factors current as of 2018. No major revisions to methodology expected until next comprehensive global food systems study.*
