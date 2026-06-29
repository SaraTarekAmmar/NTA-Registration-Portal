from pydantic import BaseModel, Field
from typing import Optional


class CoordinatorLoginRequest(BaseModel):
    email: str
    nationalId: str = Field(..., min_length=14, max_length=14, pattern=r"^\d{14}$")
    password: str

