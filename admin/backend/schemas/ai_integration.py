from pydantic import BaseModel
from typing import Optional, Dict

class FaceActionRequest(BaseModel):
    image_b64: str
    label: Optional[str] = None

class TopicSortRequest(BaseModel):
    topic_map_path: str
    clusters_path: str

class QuizGenerateTextRequest(BaseModel):
    text: str
    question_type: str = "mcq"
    num_questions: int = 10
    difficulty: str = "medium"
    source_name: str = "transcript"
    output_dir: Optional[str] = None
