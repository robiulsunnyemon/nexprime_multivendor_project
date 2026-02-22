from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SubCategoryBase(BaseModel):
    name: str
    image: Optional[str] = None

class SubCategoryCreate(SubCategoryBase):
    mainCategoryId: int

class SubCategoryResponse(SubCategoryBase):
    id: int
    mainCategoryId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class MainCategoryBase(BaseModel):
    name: str

class MainCategoryResponse(MainCategoryBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    subCategories: List[SubCategoryResponse] = []

    class Config:
        from_attributes = True
