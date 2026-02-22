from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BannerBase(BaseModel):
    link: Optional[str] = None

class BannerCreate(BannerBase):
    imageUrl: str

class BannerResponse(BannerBase):
    id: int
    imageUrl: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
