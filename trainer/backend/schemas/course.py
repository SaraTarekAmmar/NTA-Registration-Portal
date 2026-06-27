from pydantic import BaseModel
from typing import List, Optional, Any

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    duration_weeks: Optional[int] = 6
    total_sessions: Optional[int] = 12
    skill_level: Optional[str] = "متوسط"
    status: Optional[str] = "قادم"
    has_active_quiz: Optional[bool] = False
    quiz_json: Optional[Any] = None

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int

    class Config:
        from_attributes = True
