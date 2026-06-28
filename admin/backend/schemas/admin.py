from pydantic import BaseModel, field_validator, Field
from typing import List, Optional, Literal
from datetime import date

class TraineeSummary(BaseModel):
    id: int
    name: str
    email: str
    stage: Optional[int] = None
    status: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    category: Optional[str] = None
    course_id: Optional[int] = None
    ai_match_score: Optional[int] = 0
    progress_percentage: Optional[int] = 0
    image_url: Optional[str] = None
    role: Optional[str] = None
    age: Optional[int] = None
    education: Optional[str] = None
    att_rate: Optional[float] = 0.0

class StageReviewCreate(BaseModel):
    trainee_id: int
    stage_id: int
    reviewer_id: int
    result: str
    reviewer_name: str
    notes: str
    attachment_path: str
    details: Optional[dict] = None

    @field_validator('result')
    @classmethod
    def normalize_result(cls, v: str) -> str:
        """BUG 17 FIX: Normalize result to canonical casing before it reaches the router.
        A bare 'active'/'ACTIVE'/'accepted' would otherwise fall into the rejection
        branch and trigger account deletion — a catastrophic silent failure."""
        normalized = v.strip().lower()
        if normalized in ('active', 'accepted', 'approved'):
            return 'Active'
        if normalized in ('rejected', 'reject', 'denied'):
            return 'Rejected'
        raise ValueError(f"result must be 'Active' or 'Rejected', got: '{v}'")

class SecurityDecisionCreate(BaseModel):
    decision: Literal["clear", "hold", "silent_reject", "block_future"]
    internal_reason: Optional[str] = Field(default=None, max_length=5000)
    # Public, masked (technical) reason shown to the applicant on a silent reject —
    # NEVER reveals the real security reason. Defaults to a generic technical reason.
    masked_reason: Optional[str] = Field(default=None, max_length=1000)
    course_id: Optional[int] = None
