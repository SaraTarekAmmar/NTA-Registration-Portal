from pydantic import BaseModel
from typing import Optional

class FaceActionRequest(BaseModel):
    image_b64: str

# Note: OCR typically takes multipart/form-data with a file, so it doesn't need a strict BaseModel here,
# but we can declare a response model if we want strict typing.
class OcrResponseModel(BaseModel):
    national_id_number: Optional[str] = None
    full_name_arabic: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    governorate: Optional[str] = None
    address: Optional[str] = None
    extracted_at: Optional[float] = None
