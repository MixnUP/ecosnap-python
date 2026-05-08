from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from core.database import async_session, InventoryItem

logger = logging.getLogger(__name__)

class InventoryService:
    """Service for managing inventory items."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_expiring_items(self, hours: int = 48, user_id: Optional[str] = None) -> List[dict]:
        """Get items expiring within specified hours."""
        cutoff_time = datetime.utcnow() + timedelta(hours=hours)
        
        async with async_session() as session:
            query = select(InventoryItem).where(
                and_(
                    InventoryItem.estimated_expiry <= cutoff_time,
                    InventoryItem.is_consumed == False
                )
            )
            
            if user_id:
                query = query.where(InventoryItem.user_id == user_id)
            
            query = query.order_by(InventoryItem.estimated_expiry)
            
            result = await session.execute(query)
            items = result.scalars().all()
            
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "expires_at": item.estimated_expiry.isoformat() if item.estimated_expiry else None,
                    "hours_until_expiry": max(0, int((item.estimated_expiry - datetime.utcnow()).total_seconds() / 3600)) if item.estimated_expiry else None
                }
                for item in items
            ]
    
    async def mark_item_consumed(self, item_id: str, user_id: str) -> bool:
        """Mark an inventory item as consumed."""
        async with async_session() as session:
            query = select(InventoryItem).where(
                and_(InventoryItem.id == item_id, InventoryItem.user_id == user_id)
            )
            result = await session.execute(query)
            item = result.scalar_one_or_none()
            
            if not item:
                return False
            
            item.is_consumed = True
            await session.commit()
            self.logger.info(f"Item {item_id} marked as consumed")
            return True
