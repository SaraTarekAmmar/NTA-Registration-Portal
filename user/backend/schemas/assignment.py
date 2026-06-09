from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AssignmentBase(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    deadline: datetime
    max_grade: float = 10.0

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    id: int
    file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SubmissionBase(BaseModel):
    assignment_id: int
    trainee_id: int

class SubmissionCreate(SubmissionBase):
    pass

class Submission(SubmissionBase):
    id: int
    file_path: str
    submitted_at: datetime
    grade: Optional[float] = None
    feedback: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
