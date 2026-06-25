from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LiveStreamCreate(BaseModel):
    thumbnail: Optional[str] = None
    title: str
    offer: Optional[str] = None

class LiveStreamResponse(BaseModel):
    id: int
    thumbnail: str
    title: str
    offer: Optional[str]
    endDateTime: Optional[datetime] = None
    isActive: bool
    viewsCount: int
    streamerId: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class LiveTokenResponse(BaseModel):
    token: str
    stream: LiveStreamResponse

class ActiveStreamsListResponse(BaseModel):
    totalActiveStreams: int
    totalViewers: int
    streams: list[LiveStreamResponse]

class FollowedLiveStreamResponse(BaseModel):
    id: int
    title: str
    thumbnail: str
    offer: Optional[str] = None
    endDateTime: Optional[datetime] = None
    isActive: bool
    viewsCount: int
    streamerId: int
    vendorName: Optional[str] = None
    storeName: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class FollowedStreamsListResponse(BaseModel):
    totalActiveStreams: int
    streams: list[FollowedLiveStreamResponse]
