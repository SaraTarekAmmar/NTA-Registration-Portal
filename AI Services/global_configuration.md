# Global AI Services Configuration

> **Last Updated:** 2026-05-12
> This file is the **master reference** for all AI-powered microservices integrated into the NTA Academy system. All new services must be registered here. Ports and URLs must stay in sync with the `.env` file and the `SERVICE_REGISTRY` in `superadmin/backend/routers/ai_proxy.py`.

---

## Shared vLLM Server

All LLM-based services (Requirement Analyzer, Class Trainer Matrix) share a single local inference server.

| Setting | Value |
| :--- | :--- |
| **VLLM_BASE_URL** | `http://localhost:7834` |
| **VLLM_MODEL** | `google/gemma-4-31B-it` |
| **API Path** | `/v1/chat/completions` |
| **Max Tokens** | `4096` |
| **Temperature** | `0.05` (deterministic JSON mode) |

---

## Registered Microservices

All services are dispatched through the **Super Admin AI Proxy** (`POST /api/ai/dispatch`) with the service name as the `service` field.

| Service Name | Port | Base URL / Endpoint | Dispatch Mechanism | Purpose |
| :--- | :---: | :--- | :--- | :--- |
| **Face Engine** | `2341` | `http://localhost:2341` | Batch HTTP (multipart) | Biometric enrollment & attendance check-in |
| **Electronic Sorting** | `2343` | `http://localhost:2343/extract` | Batch HTTP (multipart) | 4-phase AI audit (Identity, CV, Certificates, Synthesis) |
| **Quiz Engine** | `2345` | `http://localhost:2345` | HTTP (multipart + form) | Automatic quiz generation from course materials |
| **Course Analytics** | `2346` | `http://localhost:2346` | HTTP JSON | Course-level analytics & statistics |
| **Requirement Analyzer** | `7834` | `http://localhost:7834` (vLLM) | Background thread (fire & forget) | LLM-based trainee skill analysis vs. course requirements |
| **Chat Assistant** | *(provider-agnostic)* | External API (OpenAI / Gemini) | HTTP JSON | Persona-based conversational assistant |
| **Class Trainer Matrix** | `8002` (Admin) | Loaded directly in-process | Background thread (fire & forget) | AI-driven trainer–trainee assignment matrix |

---

## Environment Variables Reference

Add all of these to the project `.env` file:

```bash
# ── vLLM Shared Server ─────────────────────────────────────────
VLLM_BASE_URL=http://localhost:7834
VLLM_MODEL=google/gemma-4-31B-it

# ── Microservice Ports ──────────────────────────────────────────
PORT_FACE_REC=2341
PORT_OCR_EXTRACTION=2343
PORT_QUIZ_GEN=2345
PORT_COURSE_ANALYTICS=2346
PORT_ADMIN_BACKEND=8002

# ── External API Keys ───────────────────────────────────────────
LLM_API_KEY=your_api_key_here        # Used by Chat Assistant

# ── Legacy / Direct URL Variables ──────────────────────────────
FACE_SERVICE_URL=http://localhost:7832
OCR_SERVICE_URL=http://localhost:2343/extract
QUIZ_SERVICE_URL=http://localhost:8001
```

---

## Database Tables Used by AI Services

| Service | Table(s) Written |
| :--- | :--- |
| **Electronic Sorting** | `admission_sorting_results`, `stage_reviews` |
| **Face Engine** | `attendance_logs` |
| **Quiz Engine** | `quizzes`, `questions`, `answers`, `courses.quiz_json` |
| **Requirement Analyzer** | `cv_matching_results` |
| **Class Trainer Matrix** | `class_matrix_recommendations`, `class_matrix_summary`, `course_ai_analysis` |

---

## Dispatch Patterns

### Standard HTTP Dispatch
Most services are called synchronously via `POST /api/ai/dispatch`:
```json
{
  "service": "Quiz Engine",
  "endpoint": "/generate",
  "data": { "course_id": 10, "count": 15, "type": "mcq" }
}
```

### Background Thread (Fire & Forget)
Long-running services (**Requirement Analyzer**, **Class Trainer Matrix**) are launched in a daemon thread and return immediately:
```json
{ "status": "processing", "message": "...", "course_id": 10 }
```
Poll for completion:
- **Requirement Analyzer** progress: `GET /api/ai/progress`
- **Class Trainer Matrix** status: `GET /api/ai/matrix-status/{course_id}`

---

## 🔒 Security & Authentication

### AI Proxy Authorization
As of the 2026-05-12 security update, the **Super Admin AI Proxy** enforces strict **SuperAdmin-only** access for all dispatch operations.

*   **Endpoint**: `POST /api/ai/dispatch`
*   **Requirement**: Must include a valid **Bearer Token** in the `Authorization` header.
*   **Role**: The JWT payload `role` claim must be exactly `superadmin`.
*   **Bypass**: Internal microservices (called from the proxy) do not require secondary auth but are protected by firewalling to `localhost`.

### CORS Policy (Production)
The system is configured to reject cross-origin requests from unauthorized domains. Whitelisted origins:
*   `https://reg.nta.eg/` (User/Trainee/Trainer Portal)
*   `https://academy.nta.eg/` (Admin/Editor Portal)
*   `http://localhost:*` (Development)

---

## Integration Guide for New Services

To register a new AI service:
1. **Add an entry** to `SERVICE_REGISTRY` in `superadmin/backend/routers/ai_proxy.py`.
2. **Add a port variable** to the `.env` file and reference it with `os.getenv(...)`.
3. **Implement special handling** inside the `/dispatch` endpoint if the service requires batch processing, file uploads, or background execution.
4. **Persist results** to the appropriate DB table and document it in the table above.
5. **Create a subdirectory** under `AI Services/` with `configuration.md` and `details.md`.
6. **Register the service endpoint** in this file to maintain the centralized registry.

> **Request Protocol**: HTTP POST with JSON (or multipart for file-based services).
> **Authentication**: Include `LLM_API_KEY` in the `Authorization` header if required by the external provider.
> **Payload Schemas**: See `AI Services/API Schemas/ai_service_payloads.json` for detailed request/response structures.
