from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class CommitteeScoreSubmit(BaseModel):
    application_id: int
    step_id: int
    criteria_scores_json: Dict[str, int]
    recommendation: str
    notes: Optional[str] = None

class CommitteeFinalSummarySubmit(BaseModel):
    application_id: int
    step_id: int
    final_recommendation: str
    reasons: str
    notes: Optional[str] = None
