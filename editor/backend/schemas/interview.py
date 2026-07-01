from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class InterviewCriterion(BaseModel):
    key: str
    title_ar: str
    title_en: str
    weight: int = 1
    scale_min: int = 1
    scale_max: int = 5
    required: bool = True

class InterviewTemplateBase(BaseModel):
    name: str
    program_type: str = "Custom"
    criteria_json: List[InterviewCriterion]
    is_active: bool = True

class InterviewTemplateCreate(InterviewTemplateBase):
    pass

class InterviewTemplateUpdate(InterviewTemplateBase):
    pass

class InterviewTemplate(InterviewTemplateBase):
    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True
