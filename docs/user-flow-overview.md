# EcoSnap User Flow Overview

## Core Flow: The Daily Triage (Free Tier)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TRIGGER: 5:30 PM - "What should I cook for dinner?"                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. OPEN APP                                                                │
│     • Minimalist home screen loads instantly                                │
│     • High-urgency data isolated: "Expiring within 48h: 3 items"           │
│     • Primary CTA: "Triage Dinner" (prominent, single action)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. TAP "TRIAGE DINNER"                                                     │
│     • Frontend queries Firebase for inventory_items expiring ≤48h          │
│     • POST to /api/v1/recipes/triage with expiring items array             │
│     • Backend calls Gemini (gemma-4-31b) for recipe generation             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. RECIPE CARD DISPLAYS                                                    │
│     • Stark, easy-to-read card: "Pan-Seared Chicken & Wilted Spinach"      │
│     • Ingredients list with quantities                                      │
│     • Step-by-step instructions (3-6 steps)                               │
│     • Estimated cook time: 25 min                                           │
│     • Difficulty: Easy                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. TAP "COOKED"                                                            │
│     • Items automatically removed from Inventory_Items (Firebase)          │
│     • Trigger: mark as consumed                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. IMPACT RECEIPT (Retention Loop)                                         │
│     • Clean modal: "Dinner Saved!"                                         │
│     • Financial: "~$6.50 saved tonight"                                    │
│     • Environmental: "2.3 kg CO₂ offset"                                   │
│     • Streak counter: "3 days of zero waste"                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Premium Flow: Receipt Scan (Sachet Purchase)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TRIGGER: Post-grocery run - "I don't want to type all this in"              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. TAP "SCAN RECEIPT"                                                      │
│     • Camera interface opens                                                 │
│     • User positions receipt in frame                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. MONETIZATION GATE                                                       │
│     • Modal appears: "Advanced Receipt Parsing requires 1 Sachet"          │
│     • Balance display: "You have 3 Sachets remaining"                        │
│     • Options: "Use 1 Sachet" | "Cancel"                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. CONFIRM SACHET USE                                                      │
│     • 1 Sachet deducted from Transaction_History ledger                     │
│     • User proceeds to camera capture                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. SNAP PHOTO                                                              │
│     • User captures receipt image                                            │
│     • Image sent to backend for AI parsing                                 │
│     • Gemini/OCR extracts line items and categorizes                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. AUTO-POPULATE INVENTORY                                                 │
│     • Items appear in dashboard within seconds                               │
│     • Each item has estimated expiry timestamp                             │
│     • User can edit any item before confirming                              │
│     • Tap "Confirm" to save to Firebase                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Supporting Flows

### Manual Item Entry (Free)
```
Tap "+" → Enter item name → Select category → Set quantity 
→ Set estimated expiry → Save to Firebase
```

### Sachet Purchase Flow
```
Profile → Sachet Store → Select pack (5/10/20 Sachets) 
→ Stripe checkout → Transaction_History updated → Balance displayed
```

### Dietary Restriction Setup
```
Settings → Dietary Preferences → Toggle restrictions 
(Vegetarian, Vegan, Gluten-Free, Dairy-Free, Nut-Free, etc.)
→ Saved to User profile in Firebase
→ Sent with every /api/v1/recipes/triage request
```

---

## Data Architecture Summary

| Data | Location | Access Pattern |
|------|----------|----------------|
| User profiles | Firebase | Direct from frontend |
| Inventory_Items | Firebase | Direct from frontend (CRUD) |
| Recipe generation | FastAPI backend | POST /api/v1/recipes/triage |
| Transaction_History | Firebase | Direct from frontend |
| Sachet balance | Firebase | Direct from frontend |

---

## Key Design Principles

1. **Firebase-first**: Frontend queries inventory directly; backend only handles AI
2. **Single primary action**: "Triage Dinner" is the dominant CTA
3. **Micro-transactions**: Sachets purchased at moments of high convenience friction
4. **Algorithmic language**: "Estimated expiry" not "Safe until" (liability protection)
5. **Immediate feedback**: Impact receipt shown instantly after "Cooked" action
