# FastAPI Application Architecture

A reference architecture for Python FastAPI services with Firestore, AI integrations, and Render deployment.

---

## 1. Folder Structure

```
.
├── main.py                    # FastAPI entry point
├── render.yaml                # Render deployment blueprint
├── requirements.txt           # Python dependencies
├── firestore.indexes.json     # Firestore composite indexes
├── .env.example               # Environment variable template
├── core/                      # Core infrastructure
│   ├── firebase_client.py     # Firestore client initialization
│   └── submission_tracker.py  # Request/operation tracking
├── services/                  # Business logic services
│   ├── ai_service.py          # AI/LLM integrations
│   ├── data_service.py        # Data processing operations
│   └── external_service.py    # External API integrations
├── utils/                     # Shared utilities
└── tests/                     # Test suite
```

---

## 2. FastAPI Entry Point (`main.py`)

### 2.1 Application Structure

```python
from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# Services
from core.firebase_client import get_firebase_db
from services.ai_service import AIService
from services.data_service import DataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="API Service", version="1.0.0")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
```

### 2.2 Security Pattern

```python
async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints."""
    expected_key = os.getenv("BRAIN_API_SECRET")
    if not expected_key or api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return api_key
```

### 2.3 Standard Endpoint Patterns

```python
@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/v1/process")
@limiter.limit("30/minute")
async def process_data(
    request: Request,
    data: ProcessRequest,
    api_key: str = Depends(verify_api_key)
):
    """Protected processing endpoint with rate limiting."""
    try:
        db = get_firebase_db()
        result = await process_with_services(db, data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")
```

---

## 3. Service Layer Pattern

### 3.1 Service Base Structure

```python
class BaseService:
    """Base class for all services."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

class AIService(BaseService):
    """AI service with API client."""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        raise NotImplementedError
```

### 3.2 Firebase/Firestore Integration

```python
# core/firebase_client.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import logging

logger = logging.getLogger(__name__)
_db = None

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    global _db
    if _db is not None:
        return _db
    
    # Try service account JSON from env first
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if service_account_json:
        try:
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid FIREBASE_SERVICE_ACCOUNT JSON: {e}")
            raise
    else:
        # Fall back to default credentials (for local dev)
        cred = credentials.ApplicationDefault()
    
    firebase_admin.initialize_app(cred)
    _db = firestore.client()
    logger.info("Firebase initialized successfully")
    return _db

def get_firebase_db():
    """Get Firestore database instance."""
    if _db is None:
        return initialize_firebase()
    return _db
```

---

## 4. Configuration Management

### 4.1 Environment Variables Template (`.env.example`)

```bash
# Required: AI/LLM API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Required: Firebase Service Account JSON
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}

# Required: API Security
BRAIN_API_SECRET=your_secure_random_key_here

# Optional: Tavily Search API
TAVILY_API_KEY=your_tavily_key_here

# Optional: HuggingFace Token
HF_TOKEN=your_hf_token_here

# Development
PYTHON_VERSION=3.11.0
```

### 4.2 Settings Class (Pydantic)

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    brain_api_secret: str = Field(..., env="BRAIN_API_SECRET")
    firebase_service_account: str = Field(..., env="FIREBASE_SERVICE_ACCOUNT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 5. Deployment Configuration (`render.yaml`)

### 5.1 Blueprint Structure

```yaml
services:
  # Staging Environment
  - type: web
    name: api-staging
    branch: staging
    env: python
    region: singapore
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: FIREBASE_SERVICE_ACCOUNT
        sync: false
      - key: BRAIN_API_SECRET
        sync: false
      - key: PYTHON_VERSION
        value: 3.11.0

  # Production Environment
  - type: web
    name: api-production
    branch: main
    env: python
    region: singapore
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: FIREBASE_SERVICE_ACCOUNT
        sync: false
      - key: BRAIN_API_SECRET
        sync: false
      - key: PYTHON_VERSION
        value: 3.11.0
```

### 5.2 Field Reference

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Unique service identifier | `api-staging`, `api-production` |
| `branch` | Git branch trigger for auto-deploy | `staging`, `main`, `develop` |
| `region` | Deployment region | `singapore`, `oregon`, `frankfurt`, `ohio` |
| `plan` | Compute tier | `free`, `starter`, `standard`, `pro` |
| `sync: false` | Prevents secret from being synced to blueprint | Required for all credentials |

---

## 6. Key Dependencies (`requirements.txt`)

```
# Web Framework
fastapi==0.110.0
uvicorn==0.27.1
slowapi==0.1.9

# Firebase/Firestore
firebase-admin==6.4.0

# AI/ML
google-genai==0.3.0

# Data Processing
numpy==1.26.4
scikit-learn==1.4.1.post1

# Configuration
pydantic==2.6.3
pydantic-settings==2.2.1
python-dotenv==1.0.1

# HTTP Clients
aiohttp==3.9.3
httpx==0.27.0

# Utilities
better-profanity==0.7.0
tavily-python==0.7.24
```

---

## 7. Common Patterns

### 7.1 Embedding Storage (Compact Base64)

```python
import struct
import base64

def encode_embedding(embedding: list) -> str:
    """Pack float list into compact Base64 string for Firestore."""
    packed = struct.pack(f'{len(embedding)}f', *embedding)
    return base64.b64encode(packed).decode('utf-8')

def decode_embedding(value) -> list | None:
    """Decode stored embedding back to float list."""
    if not value:
        return None
    try:
        if isinstance(value, str):
            packed = base64.b64decode(value)
            count = len(packed) // 4  # float32 = 4 bytes
            return list(struct.unpack(f'{count}f', packed))
        if isinstance(value, list):
            return value  # Legacy format
    except Exception as e:
        logger.warning(f"Failed to decode embedding: {e}")
    return None
```

### 7.2 Cosine Similarity

```python
import numpy as np

def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a, dtype=np.float64)
    b = np.array(vec_b, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
```

### 7.3 Firestore Atomic Updates

```python
from firebase_admin import firestore

def increment_counters(db, collection: str, doc_id: str, fields: dict):
    """Atomically increment multiple counters."""
    ref = db.collection(collection).document(doc_id)
    updates = {
        field: firestore.Increment(amount)
        for field, amount in fields.items()
    }
    updates["last_updated"] = firestore.SERVER_TIMESTAMP
    ref.update(updates)
```

---

## 8. Testing Structure

```
tests/
├── __init__.py
├── test_main.py           # API endpoint tests
├── test_services.py       # Service unit tests
└── conftest.py            # Pytest fixtures
```

### 8.1 Test Pattern

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.fixture
def mock_db():
    # Mock Firestore for testing
    pass
```

---

## 9. Quick Start Checklist

- [ ] Copy this folder structure
- [ ] Create `.env` from `.env.example`
- [ ] Add Firebase service account JSON to `FIREBASE_SERVICE_ACCOUNT`
- [ ] Generate `BRAIN_API_SECRET` for API security
- [ ] Add AI provider API key (Gemini/OpenAI)
- [ ] Configure `render.yaml` with service names
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run locally: `uvicorn main:app --reload`
- [ ] Test health endpoint: `curl http://localhost:8000/health`

---

## 10. Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use `sync: false`** for all secrets in `render.yaml`
3. **Rotate API keys** regularly via Render dashboard
4. **Rate limit all endpoints** - Use `@limiter.limit()`
5. **Validate all inputs** - Use Pydantic models
6. **Sanitize Firestore inputs** - Prevent injection attacks
