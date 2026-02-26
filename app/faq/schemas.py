from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime

class FaqStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class FaqBase(BaseModel):
    question: str
    answer: str
    status: FaqStatus = FaqStatus.ACTIVE

class FaqCreate(FaqBase):
    pass

class FaqUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    status: Optional[FaqStatus] = None

class FaqResponse(FaqBase):
    id: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
