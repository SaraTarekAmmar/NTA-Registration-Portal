# User Backend — Agent Instructions
# Inherits from project-root AGENTS.md (read that first)

## This Backend's Role
Trainee self-service: register, apply for courses, track admission stages, take exams.  
Port 8000. Entry point: `main.py`.

## Routers in This Backend
- `routers/trainees.py` — registration, profile, document upload
- `routers/exams.py` — trainee exam-taking flow
- `routers/skills.py` — skill assessment endpoints
- `routers/permissions.py` — what the trainee is allowed to do
- `routers/ai_services.py` — AI-powered feedback for trainees
- `routers/chat.py` — trainee chat with AI assistant

## Key Schemas
- `schemas/auth.py` — trainee login/register models
- `schemas/course.py` — course enrollment models
- `schemas/assignment.py` — assignment submission models

## Core Utilities
- `core/auth.py` — trainee JWT (separate secret from admin)
- `core/upload_manager.py` — photo/document upload validation

## User-Specific Rules
- Trainees must NOT have access to any admin routes — the auth systems are completely separate
- National ID is the primary identifier — validate format (14-digit Egyptian national ID)
- Profile photo upload: JPEG/PNG only, max size enforced in upload_manager
- Exam submissions must be timestamped server-side — do not trust client timestamps
