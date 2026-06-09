# Quiz Generator Configuration

## Service Integration
- **Backend Router**: `admin/backend/routers/ai_services.py`
- **Endpoint**: `/api/ai/quiz/generate`

## Configuration Steps
1. **Service URL**: Ensure the Quiz Microservice is running (typically on port 8001).
2. **Environment Variable**: Update `QUIZ_SERVICE_URL` in the `.env` file to point to the service.

## Environment Variables
```bash
QUIZ_SERVICE_URL=http://localhost:8001
```

## Database Mapping
- Generated questions are mapped to the `quizzes`, `questions`, and `answers` tables in the MySQL database.
