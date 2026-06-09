from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class PermissionBase(BaseModel):
    course_id: int
    type: str
    date: date
    reason: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    status: str

class Permission(PermissionBase):
    id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
