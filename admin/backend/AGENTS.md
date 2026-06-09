# Admin Backend — Agent Instructions
# Inherits from project-root AGENTS.md (read that first)

## This Backend's Role
Admin operations: manage trainees, courses, exams, permissions, AI services, uploads.  
Port 8001. Entry point: `main.py`.

## Routers in This Backend
- `routers/admin.py` — trainee CRUD, stage reviews, admin users
- `routers/courses.py` — course and material management
- `routers/exams.py` — exam creation and results
- `routers/permissions.py` — role-based access control
- `routers/ai_services.py` — Gemini AI integration
- `routers/chat.py` — admin chat with AI
- `routers/class_matrix.py` — class scheduling matrix

## Key Schemas
- `schemas/auth.py` — login, token models
- `schemas/ai_integration.py` — AI request/response models

## Core Utilities
- `core/auth.py` — JWT encode/decode, get_current_admin dependency
- `core/security.py` — bcrypt hash/verify
- `core/upload_manager.py` — validates MIME type, saves to uploads/
- `core/chat_engine.py` — wraps Gemini API for chat
- `core/exam_analyzer.py` — AI-powered exam analysis

## Admin-Specific Rules
- All routes require `get_current_admin` dependency (JWT-protected)
- File uploads must use `upload_manager.py` — never write to disk directly
- AI calls go through `chat_engine.py` — do not call Gemini API directly in routes
- Stage review logic lives in `admin.py` — keep it there, do not split
