from pydantic import BaseModel
from typing import Optional


class CoordinatorLoginRequest(BaseModel):
    email: str
    nationalId: str
    password: str
