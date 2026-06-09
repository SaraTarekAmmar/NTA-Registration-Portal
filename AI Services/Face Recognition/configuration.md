# Face Recognition Configuration

## Service Integration
- **Backend Router**: `admin/backend/routers/ai_services.py`
- **Endpoints**: `/api/ai/face/enroll`, `/api/ai/face/checkin`

## Configuration Steps
1. **Service URL**: Set `FACE_SERVICE_URL` in the `.env` file.
2. **Timeout**: Standard 30-second timeout for rapid check-ins.

## Environment Variables
```bash
FACE_SERVICE_URL=http://localhost:7832
```

## Data Storage
- Face matching scores are stored in the `attendance_logs` table.
