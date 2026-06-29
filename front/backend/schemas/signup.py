from pydantic import BaseModel, field_validator
from typing import Optional
import re

class SignupStep1(BaseModel):
    national_id: str

    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, v):
        v = v.strip()
        if not re.match(r"^\d{10,20}$", v):
            raise ValueError("National ID must be 10–20 digits")
        return v

class SignupCreate(BaseModel):
    national_id: str
    full_name:   str
    phone:       str
    email:       Optional[str] = None
    password:    str

    @field_validator("national_id")
    @classmethod
    def validate_nid(cls, v):
        v = v.strip()
        if not re.match(r"^\d{10,20}$", v):
            raise ValueError("National ID must be 10–20 digits")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Full name must be at least 3 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        v = v.strip()
        if not re.match(r"^[\d\+\-\s\(\)]{7,20}$", v):
            raise ValueError("Invalid phone number format")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is None or v.strip() == "":
            return None
        v = v.strip().lower()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email address")
        return v

class SignupResponse(BaseModel):
    id:          int
    national_id: str
    full_name:   str
    phone:       str
    email:       Optional[str]
    status:      str
    created_at:  str
