from pydantic import BaseModel
from typing import Optional, List

class ContentUpdate(BaseModel):
    content_json:    Optional[str] = None   # JSON string of text fields
    media_type:      Optional[str] = None   # none | image | video
    media_path:      Optional[str] = None   # URL or server path
    bg_color:        Optional[str] = None
    text_color:      Optional[str] = None
    is_visible:      Optional[bool] = None

class ContentCreate(BaseModel):
    section_key:  str
    lang:         str = "en"
    sort_order:   int = 999
    content_json: Optional[str] = None
    media_type:   str = "none"
    media_path:   Optional[str] = None
    bg_color:     Optional[str] = None
    text_color:   Optional[str] = None
    is_visible:   bool = True

class ReorderItem(BaseModel):
    section_key: str
    sort_order:  int

class ReorderRequest(BaseModel):
    items: List[ReorderItem]
