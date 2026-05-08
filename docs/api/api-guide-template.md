# API Guide Template

A template for creating comprehensive API documentation. Use this structure to document REST API endpoints, authentication, rate limits, and usage examples.

---

## Document Structure

### 1. Title & Overview

Start with a clear title and brief description of what the API does.

```markdown
# [Project Name]: API Guide & Reference

This document serves as the master guide for interacting with the [Project] backend.
```

---

### 2. Authentication Section

Document all authentication requirements clearly.

**Include:**
- Authentication method (API Key, OAuth, JWT, etc.)
- Header names and values
- Where to obtain credentials (env vars, dashboard, etc.)
- Which endpoints require auth

```markdown
## Authentication

All mutation endpoints (POST/PUT/DELETE) require an API Key passed via the `X-API-KEY` header.

*   **Header Name**: `X-API-KEY`
*   **Local Value**: Defined in your `.env` as `API_SECRET_KEY`
*   **Production Value**: Configured in [deployment platform] environment variables
```

---

### 3. Local Development Setup

Provide clear instructions for running the API locally.

**Include:**
- Prerequisites (dependencies, env setup)
- Commands to start the server
- Default URL and port

```markdown
## Local Development Setup

### Prerequisites
Ensure you have the virtual environment prepared:
```bash
# Install dependencies
pip install -r requirements.txt
```

### Run the Server
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`.
```

---

### 4. Rate Limits

Document rate limiting policies per endpoint group.

```markdown
## Global Rate Limits

Rate limits are enforced per-IP to prevent abuse and protect resources.

| Endpoint Group | Limit |
| :--- | :--- |
| **Health/Info** | 120 requests / minute |
| **Read Operations** | 60 requests / minute |
| **Write Operations** | 10 requests / minute |
| **Heavy Processing** | 5 requests / minute |
```

---

### 5. Endpoint Reference

The core of the document. Use a consistent format for each endpoint.

**Standard Endpoint Template:**

```markdown
### [Number]. [Endpoint Name]
`[METHOD] /path`

Brief description of what this endpoint does and its purpose in the system.

*   **Auth**: Required/None
*   **Rate Limit**: X/min
*   **Parameters**:
    *   `param_name` (Query/Body, Required/Optional): Description
*   **Flow** (for complex endpoints):
    1. Step 1
    2. Step 2
    3. Step 3
*   **Response**:
    ```json
    {
      "status": "success",
      "data": { ... }
    }
    ```
```

**Types of Endpoints to Document:**

| Type | What to Include |
| :--- | :--- |
| **Health Checks** | Simple status response, no auth |
| **Cron/Worker Endpoints** | Trigger mechanisms, scheduling info |
| **Data Processing Jobs** | Step-by-step flow, AI/model details |
| **Aggregation Jobs** | Data sources, output format |
| **External Integrations** | Third-party APIs used, rate limits |
| **Maintenance Jobs** | Safety flags (dry_run), scope |

---

### 6. Testing with cURL

Provide copy-pasteable examples for common operations.

**Organize by:**
- Local development examples first
- Staging/production examples
- Group by endpoint type

```markdown
## Testing with cURL

### Local Development
Ensure your server is running (`uvicorn main:app --reload`).

**Test Health:**
```bash
curl http://localhost:8000/health
```

**Trigger Job:**
```bash
curl -X POST "http://localhost:8000/process-job" \
     -H 'X-API-KEY: your-local-secret'
```

**With Query Parameters:**
```bash
curl -X POST "http://localhost:8000/job?backfill=true&dry_run=false" \
     -H 'X-API-KEY: your-local-secret'
```

**With JSON Body:**
```bash
curl -X POST "http://localhost:8000/remove-item" \
     -H 'X-API-KEY: your-local-secret' \
     -H 'Content-Type: application/json' \
     -d '{"item_id": "abc123", "reason": "user_request"}'
```
```

---

### 7. Development Tips

Include practical commands for developers.

```markdown
## Development Tips

### Checking Syntax
Before running the server, verify your changes compile:

```bash
# Check a single file
python3 -m py_compile services/my_service.py && echo "Syntax OK"

# Check main entry point
python3 -m py_compile main.py && echo "Syntax OK"
```

### Viewing Logs
```bash
tail -f logs/app.log
```

### Database Migrations
```bash
alembic upgrade head
```
```

---

### 8. Security Notes

Document security measures and best practices.

```markdown
## Security Notes

*   **Input Sanitization**: All user inputs are validated before processing
*   **Timeouts**: External API calls have [X]s timeouts to prevent hanging
*   **Error Masking**: Internal exceptions are logged but generic messages returned
*   **Secrets Management**: Never commit API keys; use environment variables
```

---

## Formatting Guidelines

### Use Consistent Visual Cues

| Element | Format | Example |
| :--- | :--- | :--- |
| HTTP Methods | ALL CAPS | `GET`, `POST`, `DELETE` |
| Endpoints | Backticks | `/health`, `/process-job` |
| Headers | `X-Header-Name` | `X-API-KEY` |
| JSON Keys | camel_case | `processedCount`, `isComplete` |
| Environment Vars | ALL_CAPS | `API_SECRET_KEY` |
| File Paths | Backticks | `main.py`, `services/job_service.py` |

### Use Tables for Reference Data

Good for rate limits, parameter lists, response fields, or any structured comparison.

### Use Emojis for Section Headers

Optional but helps visual scanning:
- 🔐 Authentication
- 💻 Local Development
- 🚦 Rate Limits
- 🛠 Endpoint Reference
- 🧪 Testing
- 🛡 Security

### Code Blocks

- Use `bash` for shell commands
- Use `json` for API responses
- Use `python` for code examples

---

## Checklist: Before Publishing

- [ ] All endpoints are documented
- [ ] Authentication requirements are clear
- [ ] Rate limits are specified per endpoint
- [ ] cURL examples are tested and working
- [ ] Response schemas include all fields
- [ ] Environment variables are documented
- [ ] Error responses are described
- [ ] Security considerations are noted
