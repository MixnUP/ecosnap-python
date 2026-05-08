# TODO: Streak Counter Implementation

## Status
**Priority:** Medium  
**Created:** 2024-XX-XX  
**Assignee:** TBD  
**Status:** Not started

---

## Feature Description

Implement a streak counter to track consecutive days with zero food waste. Displayed in the Impact Receipt modal after user marks a recipe as "Cooked".

**User-facing copy:**
- "3 days of zero waste"
- "🔥 5 day streak!"
- "Longest streak: 12 days"

---

## Business Logic

```javascript
// Daily job (runs at midnight)
function updateStreak(user) {
  const itemsExpiredToday = getItemsExpiredOn(user, today);
  
  if (itemsExpiredToday.length === 0 && user.app_opened_today) {
    // No waste + engaged user = streak continues
    user.streak += 1;
    user.longest_streak = Math.max(user.streak, user.longest_streak);
  } else {
    // Waste detected or no app engagement = streak reset
    user.streak = 0;
  }
  
  user.last_streak_check = today;
}
```

### Edge Cases
- **Items marked "consumed" before expiry:** Don't break streak
- **Items deleted without cooking:** Counts as waste → reset streak
- **User doesn't open app:** Streak pauses (no increment, no reset)
- **First-time user:** Start at 0

---

## Data Model

### User Document (Firebase)
```javascript
{
  id: "user_123",
  email: "user@example.com",
  
  // Streak fields
  streak: 3,                          // Current consecutive days
  longest_streak: 12,                 // All-time high
  last_streak_check: "2024-01-15",    // ISO date of last check
  app_opened_today: true,             // Flag reset daily
  
  // Metadata
  created_at: timestamp,
  updated_at: timestamp
}
```

---

## Implementation Options

### Option A: Firebase Cloud Function (Recommended)

**Location:** `functions/index.js` or `functions/src/streak.ts`

**Pros:**
- Native access to Firebase Auth/Firestore
- Scheduled functions built-in
- Stays in data layer where user/inventory lives

**Code sketch:**
```javascript
const functions = require('firebase-functions');
const admin = require('firebase-admin');

exports.dailyStreakCheck = functions.pubsub
  .schedule('0 0 * * *')  // Every midnight
  .timeZone('America/New_York')
  .onRun(async (context) => {
    const db = admin.firestore();
    const today = new Date().toISOString().split('T')[0];
    
    // Get all users
    const usersSnapshot = await db.collection('users').get();
    
    const batch = db.batch();
    
    for (const userDoc of usersSnapshot.docs) {
      const user = userDoc.data();
      
      // Check for expired items today
      const expiredItems = await db
        .collection('inventory_items')
        .where('user_id', '==', userDoc.id)
        .where('estimated_expiry', '<=', today)
        .where('is_consumed', '==', false)
        .get();
      
      const hadWaste = !expiredItems.empty;
      const wasActive = user.app_opened_today || false;
      
      let newStreak = user.streak || 0;
      
      if (!hadWaste && wasActive) {
        newStreak += 1;
      } else if (hadWaste) {
        newStreak = 0;
      }
      // If !wasActive, streak unchanged
      
      batch.update(userDoc.ref, {
        streak: newStreak,
        longest_streak: Math.max(newStreak, user.longest_streak || 0),
        last_streak_check: today,
        app_opened_today: false  // Reset for tomorrow
      });
    }
    
    await batch.commit();
    console.log(`Processed ${usersSnapshot.size} users for streak update`);
  });

// Track app opens
exports.trackAppOpen = functions.https.onCall(async (data, context) => {
  if (!context.auth) return;
  
  const today = new Date().toISOString().split('T')[0];
  const userRef = admin.firestore().doc(`users/${context.auth.uid}`);
  
  await userRef.update({
    app_opened_today: true,
    last_app_open: new Date()
  });
});
```

---

### Option B: FastAPI Backend + External Cron

**File:** `api/streak.py`

**Pros:**
- All backend logic in one place

**Cons:**
- Requires external cron service (Render cron jobs don't exist)
- More complex to access Firebase data
- Need to set up separate scheduler (e.g., GitHub Actions, external cron)

**Not recommended** for this feature.

---

## Decision

**Selected:** Option A (Firebase Cloud Function)

**Rationale:**
- Streak logic tightly coupled to Firebase data (users, inventory_items)
- Firebase provides native scheduling
- Keeps FastAPI backend focused on AI recipe generation only

---

## Implementation Checklist

- [ ] Set up Firebase Cloud Functions project
- [ ] Install dependencies: `firebase-functions`, `firebase-admin`
- [ ] Write `dailyStreakCheck` scheduled function
- [ ] Write `trackAppOpen` callable function
- [ ] Add `streak`, `longest_streak`, `last_streak_check`, `app_opened_today` to User model
- [ ] Deploy function: `firebase deploy --only functions`
- [ ] Test with mock data
- [ ] Add to Impact Receipt UI component
- [ ] Add streak celebration animation (optional)

---

## Testing Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| No items expire + app opened | Streak +1 |
| 1 item expires + app opened | Streak reset to 0 |
| No items expire + no app open | Streak unchanged |
| Item consumed before expiry | Streak +1 (not expired) |
| Item deleted without cooking | Streak reset (counts as waste) |
| New user first day | Streak = 0 → 1 after first check |
| 7 consecutive days | Display "🔥 7 day streak!" |

---

## Open Questions

1. **Time zone handling:** Should streak reset at midnight local time or UTC?
2. **Grace period:** Should users get 1 "free" waste day before streak resets?
3. **Streak freeze:** Should streak freeze on vacation (no app open) vs. reset?
4. **Social features:** Share streak to social media? Leaderboards?

---

## Related Files

- `docs/user-flow-overview.md` - Impact Receipt display location
- `docs/environmental-impact-methodology.md` - Displayed alongside CO₂ savings

---

*Last updated: 2024-XX-XX*  
*Next review: When Firebase Functions are set up*
