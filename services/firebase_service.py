from typing import List, Dict, Any, Optional
import logging
import json
import base64
from datetime import datetime, timedelta
from google.cloud import firestore
from core.config import settings

logger = logging.getLogger(__name__)

class FirebaseService:
    """Service for interacting with Firebase Firestore."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = self._get_firestore_db()
    
    def _get_firestore_db(self) -> firestore.Client:
        """Initialize Firestore client from base64 service account."""
        try:
            # Decode base64 service account
            service_account_json = base64.b64decode(settings.firebase_service_account).decode('utf-8')
            service_account_dict = json.loads(service_account_json)
            
            # Initialize Firestore
            return firestore.Client.from_service_account_info(service_account_dict)
        except Exception as e:
            self.logger.error(f"Failed to initialize Firestore: {e}")
            raise
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Fetch user preferences from Firebase."""
        try:
            doc_ref = self.db.collection("users").document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                self.logger.info(f"No preferences found for user {user_id}")
                return {}
            
            user_data = doc.to_dict()
            preferences = user_data.get("preferences", {})
            
            self.logger.info(f"Retrieved preferences for user {user_id}: {preferences}")
            return preferences
            
        except Exception as e:
            self.logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return {}
    
    async def get_user_pantry(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch user's pantry items from Firebase."""
        try:
            pantry_ref = self.db.collection("users").document(user_id).collection("pantry")
            docs = pantry_ref.stream()
            
            pantry_items = []
            for doc in docs:
                item_data = doc.to_dict()
                item_data["id"] = doc.id  # Include document ID
                pantry_items.append(item_data)
            
            self.logger.info(f"Retrieved {len(pantry_items)} pantry items for user {user_id}")
            return pantry_items
            
        except Exception as e:
            self.logger.error(f"Failed to get user pantry for {user_id}: {e}")
            return []
    
    async def get_recent_recipes(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch recent recipe history for deduplication."""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            query = (self.db.collection("recipe_history")
                    .where("user_id", "==", user_id)
                    .where("generated_at", ">=", cutoff)
                    .order_by("generated_at", direction="DESCENDING"))
            
            docs = query.stream()
            recent_recipes = []
            
            for doc in docs:
                recipe_data = doc.to_dict()
                recipe_data["id"] = doc.id
                recent_recipes.append(recipe_data)
            
            self.logger.info(f"Retrieved {len(recent_recipes)} recent recipes for user {user_id}")
            return recent_recipes
            
        except Exception as e:
            self.logger.error(f"Failed to get recent recipes for {user_id}: {e}")
            return []
    
    async def store_recipe_history(self, user_id: str, recipe_data: Dict[str, Any], chosen: bool = True) -> str:
        """Store recipe in history for future deduplication."""
        try:
            history_data = {
                "user_id": user_id,
                "title": recipe_data.get("title", ""),
                "ingredients": recipe_data.get("ingredients", []),
                "generated_at": datetime.now(),
                "chosen": chosen,
                "expiring_items_used": recipe_data.get("expiring_items_used", []),
                "categorized_items": recipe_data.get("categorized_items", {}),
                "urgent_items": recipe_data.get("urgent_items", [])
            }
            
            # Add to recipe_history collection
            doc_ref = self.db.collection("recipe_history").add(history_data)
            
            self.logger.info(f"Stored recipe history for user {user_id}: {recipe_data.get('title', 'Unknown')}")
            return doc_ref[1].id
            
        except Exception as e:
            self.logger.error(f"Failed to store recipe history for {user_id}: {e}")
            return ""
