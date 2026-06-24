from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    nationalId: str = Field(..., min_length=14, max_length=14)
    role: str
    password: Optional[str] = None

class AdminLoginRequest(BaseModel):
    email: EmailStr
    nationalId: str = Field(..., min_length=14, max_length=14)
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    fullName: str
    userId: int
