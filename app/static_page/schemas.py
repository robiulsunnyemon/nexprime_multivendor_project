from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StaticPageBase(BaseModel):
    key: str
    title: str
    content: str # Can be plain text or HTML

class StaticPageCreate(StaticPageBase):
    pass

class StaticPageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class StaticPageResponse(StaticPageBase):
    id: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
