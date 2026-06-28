from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any

class LoginRequest(BaseModel):
    email: EmailStr
    nationalId: str = Field(..., min_length=14, max_length=14)
    password: Optional[str] = None
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    fullName: str
    userId: int
