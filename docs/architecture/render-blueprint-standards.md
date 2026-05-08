# Render Blueprint Standards: Staging & Production

## Overview

This document defines the standards for configuring Render blueprints that support both **staging** and **production** environments. These standards ensure consistent deployment practices, proper environment isolation, and secure secret management.

---

## Repository Structure

### Branch Strategy

| Environment | Branch | Purpose |
|-------------|--------|---------|
| Staging | `staging` | Pre-production testing and integration |
| Production | `main` | Live, customer-facing deployment |

**Standard**: All feature work is merged into `staging` first. Once validated, changes are promoted to `main` via pull request.

---

## Render.yaml Structure

### File Location
- **Path**: `render.yaml`
- **Placement**: Repository root (required for Render Blueprints)

### Service Configuration Pattern

Each environment requires a distinct web service with the following structure:

```yaml
services:
  # --- STAGING SERVICE ---
  - type: web
    name: <project>-staging
    branch: staging
    env: python  # or node, go, etc.
    region: <region-code>
    plan: <plan-tier>
    buildCommand: <build-command>
    startCommand: <start-command>
    envVars:
      - key: <SENSITIVE_VAR>
        sync: false  # Must be set in Render Dashboard
      - key: <NON_SENSITIVE_VAR>
        value: <static-value>

  # --- PRODUCTION SERVICE ---
  - type: web
    name: <project>-production
    branch: main
    env: python
    region: <region-code>
    plan: <plan-tier>
    buildCommand: <build-command>
    startCommand: <start-command>
    envVars:
      - key: <SENSITIVE_VAR>
        sync: false
      - key: <NON_SENSITIVE_VAR>
        value: <static-value>
```

### Field Standards

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Service identifier (must be unique) | `brain-staging`, `brain-production` |
| `branch` | Git branch trigger | `staging`, `main` |
| `region` | Deployment region | `singapore`, `oregon`, `frankfurt` |
| `plan` | Compute tier | `free`, `starter`, `standard`, `pro` |
| `sync: false` | Excludes from blueprint sync (secrets) | Required for all credentials |

---

## Environment Variables

### Sensitive Variables (sync: false)

These **must** be configured manually in the Render Dashboard and excluded from `render.yaml`:

| Variable | Purpose | Format |
|----------|---------|--------|
| `GEMINI_API_KEY` | AI/LLM service authentication | Plain string |
| `FIREBASE_SERVICE_ACCOUNT` | GCP service account | Base64-encoded JSON |
| `API_SECRET` | API key for service-to-service auth | Plain string (high entropy) |
| `TAVILY_API_KEY` | External search service auth | Plain string |

### Non-Sensitive Variables

Static values safe to commit in `render.yaml`:

| Variable | Example | Purpose |
|----------|---------|---------|
| `PYTHON_VERSION` | `3.11.0` | Runtime version pinning |
| `NODE_VERSION` | `18.17.0` | Node.js version |

---

## Secret Management

### Base64 Encoding for Service Accounts

For multi-line credentials (e.g., Firebase service account JSON), use Base64 encoding:

**macOS/Linux:**
```bash
base64 -i service-account.json | pbcopy
```

**Render Dashboard Setup:**
1. Navigate to Service → Environment
2. Add key: `FIREBASE_SERVICE_ACCOUNT`
3. Paste Base64 value
4. Save (value is encrypted at rest)

### Local Development

Use `.env.example` as a template for local environments:

```bash
# Copy and fill in
API_SECRET="your-secret-here"
GEMINI_API_KEY="your-key-here"
FIREBASE_SERVICE_ACCOUNT="your-base64-encoded-json"
```

**Never commit `.env` files.**

---

## Security Standards

### API Key Validation

All protected endpoints must implement:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
import os
import secrets

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("API_SECRET")
    if not expected_key:
        raise HTTPException(status_code=500, detail="Security configuration missing")
    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return api_key

# Apply to routes
@app.post("/endpoint", dependencies=[Depends(verify_api_key)])
```

### Requirements

- Use `secrets.compare_digest()` for timing-attack resistance
- Return 500 (not 403) if server config is missing (fail-safe)
- Apply rate limiting to all authenticated endpoints

---

## Deployment Workflow

### Staging Deployment

1. Push feature branch to `staging`
2. Render auto-deploys to staging service
3. Run integration tests against staging URL
4. Validate with production-like data

### Production Deployment

1. Create PR from `staging` → `main`
2. Code review and approval
3. Merge to `main`
4. Render auto-deploys to production service
5. Monitor health checks and logs

### Rollback

In case of failure:
1. Revert commit on `main`
2. Push revert (triggers auto-deploy)
3. Or: Manually deploy previous commit via Render Dashboard

---

## Region Selection Guidelines

| Target Users | Recommended Region |
|--------------|-------------------|
| Asia-Pacific | `singapore` |
| North America | `oregon`, `virginia` |
| Europe | `frankfurt`, `ireland` |

**Standard**: Deploy both staging and production to the same region to minimize latency differences.

---

## Plan Tier Recommendations

| Environment | Minimum Plan | Rationale |
|-------------|--------------|-----------|
| Staging | `free` or `starter` | Cost efficiency for testing |
| Production | `starter` or higher | Reliability and performance |

**Note**: Free tier services spin down after inactivity. Use `starter` for always-on staging if continuous testing is required.

---

## Validation Checklist

Before deploying a new project:

- [ ] `render.yaml` is in repository root
- [ ] Service names include environment suffix (`-staging`, `-production`)
- [ ] Branches correctly mapped (`staging`, `main`)
- [ ] All secrets use `sync: false`
- [ ] Secrets configured in Render Dashboard for both services
- [ ] `.env.example` exists and documents all required variables
- [ ] `.gitignore` excludes `.env` files
- [ ] API key validation implemented on all protected endpoints
- [ ] Health check endpoint exists for monitoring
- [ ] Region selected based on user geography
- [ ] Plan tier appropriate for environment requirements

---

## Example Implementation

See `render.yaml` in this repository for a complete, production-ready configuration.

---

## References

- [Render Blueprints Documentation](https://render.com/docs/blueprint-spec)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
