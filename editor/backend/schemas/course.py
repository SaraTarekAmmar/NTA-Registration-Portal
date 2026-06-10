from pydantic import BaseModel
from typing import List, Optional, Any, Dict


class CourseBase(BaseModel):
    title: str
    title_ar: Optional[str] = None
    short_name: Optional[str] = None
    classification: Optional[str] = None
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    duration_weeks: Optional[int] = 6
    total_sessions: Optional[int] = 12
    skill_level: Optional[str] = "متوسط"
    status: Optional[str] = "قادم"
    is_public: Optional[bool] = True
    stages: Optional[List[Dict[str, Any]]] = None
    batch_data: Optional[Dict[str, Any]] = None
    course_type: Optional[str] = None


class Course(CourseBase):
    id: int

    class Config:
        from_attributes = True
        populate_by_name = True
