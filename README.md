# EcoSnap FastAPI Backend

FastAPI-based backend for EcoSnap - an expiry-first dinner triage application.

## Quick Start

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables in `.env`:**
   - `DATABASE_URL` - PostgreSQL connection string
   - `GEMINI_API_KEY` - AI API key for recipe generation
   - `BRAIN_API_SECRET` - API security key

4. **Run locally:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Test health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/recipes/triage` | POST | Generate dinner from expiring items |

## Deployment

- **Staging:** Auto-deploy from `staging` branch
- **Production:** Auto-deploy from `main` branch
- **Platform:** Render (configured via `render.yaml`)
