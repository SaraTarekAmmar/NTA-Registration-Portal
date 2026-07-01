from pydantic import BaseModel
from typing import Optional

class CareerCreate(BaseModel):
    title:        str
    type:         str = "Full Time"
    location:     Optional[str] = None
    description:  Optional[str] = None
    requirements: Optional[str] = None
    is_active:    bool = True

class CareerUpdate(BaseModel):
    title:        Optional[str] = None
    type:         Optional[str] = None
    location:     Optional[str] = None
    description:  Optional[str] = None
    requirements: Optional[str] = None
    is_active:    Optional[bool] = None

class ApplicationStatusUpdate(BaseModel):
    status: str  # new | reviewed | shortlisted | rejected
