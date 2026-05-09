from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from core.config import settings
from services.recipe_service import RecipeService


class TriageRequest(BaseModel):
    expiring_items: List[dict]
    dietary_restrictions: Optional[List[str]] = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="EcoSnap API",
    description="Expiry-first dinner triage API",
    version="1.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints."""
    if not settings.api_secret or api_key != settings.api_secret:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return api_key


@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "ok", "service": "ecosnap-api"}


@app.post("/api/v1/recipes/triage")
@limiter.limit("20/minute")
async def triage_dinner(
    request: Request,
    data: TriageRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate dinner recipe from expiring ingredients."""
    try:
        if not data.expiring_items:
            return {"success": True, "recipe": None, "message": "No items provided"}
        
        recipe_service = RecipeService()
        recipe = await recipe_service.generate_recipe(data.expiring_items, data.dietary_restrictions)
        return {"success": True, "recipe": recipe}
    except Exception as e:
        logger.error(f"Recipe generation failed: {e}")
        raise HTTPException(status_code=500, detail="Recipe generation failed")
