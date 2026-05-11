# TODO: Streak Counter Implementation

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

## Implementation

The streak counter runs entirely in the Python/FastAPI backend. An external cron trigger (e.g., Cloudflare Workers, GitHub Actions, etc.) calls the `POST /internal/streak/daily-check` endpoint at midnight UTC to process all users.

### Service Layer

**`services/streak_service.py`** (following existing pattern):
```python
from datetime import date, datetime
from typing import Dict, Any
import logging

from core.firebase_client import get_firebase_db

logger = logging.getLogger(__name__)

class StreakService:
    """Service for managing user streak counters."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = get_firebase_db()
    
    async def process_daily_streaks(self) -> Dict[str, Any]:
        """
        Daily cron job: Check all users for expired items and update streaks.
        Called at midnight UTC by external trigger.
        """
        today = date.today().isoformat()
        users_ref = self.db.collection("users")
        users = users_ref.stream()
        
        updated_count = 0
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            user_id = user_doc.id
            
            # Check for expired items today
            expired_items = (
                self.db.collection("inventory_items")
                .where("user_id", "==", user_id)
                .where("estimated_expiry", "<=", today)
                .where("is_consumed", "==", False)
                .stream()
            )
            
            had_waste = any(True for _ in expired_items)
            was_active = user_data.get("app_opened_today", False)
            
            current_streak = user_data.get("streak", 0)
            
            if not had_waste and was_active:
                new_streak = current_streak + 1
            elif had_waste:
                new_streak = 0
            else:
                new_streak = current_streak  # No change if inactive
            
            longest_streak = max(new_streak, user_data.get("longest_streak", 0))
            
            # Update user document
            user_doc.reference.update({
                "streak": new_streak,
                "longest_streak": longest_streak,
                "last_streak_check": today,
                "app_opened_today": False,  # Reset for tomorrow
                "updated_at": datetime.utcnow()
            })
            
            updated_count += 1
            self.logger.debug(f"Updated user {user_id}: streak={new_streak}")
        
        self.logger.info(f"Processed {updated_count} users for streak update")
        return {
            "processed": updated_count,
            "date": today,
            "status": "success"
        }
    
    async def track_app_open(self, user_id: str) -> Dict[str, str]:
        """Mark user as active for today when they open the app."""
        self.db.collection("users").document(user_id).update({
            "app_opened_today": True,
            "last_app_open": datetime.utcnow()
        })
        self.logger.info(f"Tracked app open for user {user_id}")
        return {"status": "tracked"}
```

### API Endpoints

Add to **`main.py`**:

```python
from services.streak_service import StreakService

# Add to existing verify_api_key for cron endpoints
cron_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_cron_api_key(api_key: str = Security(cron_api_key_header)):
    """Verify API key for internal cron endpoints."""
    if not settings.api_secret or api_key != settings.api_secret:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return api_key

# Daily streak check endpoint (called by external cron)
@app.post("/internal/streak/daily-check")
@limiter.limit("1/minute")  # Strict rate limit for cron
async def daily_streak_check(
    request: Request,
    api_key: str = Depends(verify_cron_api_key)
):
    """Daily cron endpoint. Triggered by external scheduler at midnight UTC."""
    try:
        streak_service = StreakService()
        result = await streak_service.process_daily_streaks()
        return result
    except Exception as e:
        logger.error(f"Daily streak check failed: {e}")
        raise HTTPException(status_code=500, detail="Streak processing failed")

# Track app open (called by frontend)
@app.post("/internal/streak/track-open")
@limiter.limit("10/minute")
async def track_app_open(
    request: Request,
    user_id: str,  # Or use auth dependency if you have user auth
    api_key: str = Depends(verify_api_key)
):
    """Call when user opens app to mark them active for today."""
    try:
        streak_service = StreakService()
        result = await streak_service.track_app_open(user_id)
        return result
    except Exception as e:
        logger.error(f"Track app open failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to track app open")
```

---

## Implementation Checklist

- [ ] Create `services/streak_service.py` with `StreakService` class
- [ ] Add streak endpoints to `main.py` using existing `verify_api_key` pattern
- [ ] Add streak fields to Firebase User documents: `streak`, `longest_streak`, `last_streak_check`, `app_opened_today`
- [ ] Reuse existing `settings.api_secret` for cron endpoint authentication (no new env var needed)
- [ ] Test `StreakService.process_daily_streaks()` locally
- [ ] Deploy FastAPI app
- [ ] Set up external cron trigger to call `POST /internal/streak/daily-check` with `X-API-Key` header daily at midnight UTC
- [ ] Call `POST /internal/streak/track-open` from frontend when app opens
- [ ] Add streak display to Impact Receipt UI component

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
*Next review: When StreakService is implemented*
