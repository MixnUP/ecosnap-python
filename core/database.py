from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, ForeignKey
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Convert PostgreSQL URL to async version if needed
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default="now()")
    sachet_balance = Column(Integer, default=0)

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    quantity = Column(Float, default=1.0)
    unit = Column(String, default="item")
    estimated_expiry = Column(DateTime, nullable=False)
    added_at = Column(DateTime, server_default="now()")
    is_consumed = Column(Boolean, default=False)

class TransactionHistory(Base):
    __tablename__ = "transaction_history"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(String, nullable=False)  # 'sachet_purchase', 'sachet_use', 'credit'
    amount = Column(Integer, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, server_default="now()")

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")

async def get_db_session() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        yield session
