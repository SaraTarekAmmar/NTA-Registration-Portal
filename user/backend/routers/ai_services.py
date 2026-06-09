from fastapi import APIRouter, HTTPException, UploadFile, File
import requests
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/ai", tags=["AI Services"])

# OCR port (User ID Review)
OCR_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:8000/extract")
# Face Rec port
FACE_URL = os.getenv("FACE_SERVICE_URL", "http://localhost:7832")

class FaceActionRequest(BaseModel):
    image_b64: str

@router.post("/extract-id")
async def extract_national_id(file: UploadFile = File(...)):
    """ Proxy to the OCR AI Microservice running on port 8000 """
    try:
        # Pass the file directly to the external service
        files = {"file": (file.filename, await file.read(), file.content_type)}
        response = requests.post(OCR_URL, files=files, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"OCR Service error: {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to OCR service: {str(e)}")

@router.post("/face/checkin")
async def face_checkin(request: FaceActionRequest):
    """ Proxy to Face Check-in AI Microservice running on port 7832 """
    try:
        response = requests.post(
            f"{FACE_URL}/checkin",
            json={"image_b64": request.image_b64},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Face Check-in Service error: {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Face service: {str(e)}")
