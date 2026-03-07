from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, model_validator, ConfigDict
from enum import Enum

class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"

class MessageBase(BaseModel):
    content: str
    type: MessageType = MessageType.TEXT
    receiverId: int
    replyToId: Optional[int] = None

class MessageCreate(MessageBase):
    pass

class ChatUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    userId: Optional[int] = None
    fullname: str
    email: str
    isOnline: bool = False
    lastActiveAt: datetime

    @model_validator(mode='after')
    def set_userid(self) -> 'ChatUserResponse':
        if self.userId is None:
            self.userId = self.id
        return self

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    content: str
    type: MessageType
    senderId: int
    receiverId: int
    replyToId: Optional[int]
    isRead: bool
    createdAt: datetime

class ActiveUserResponse(ChatUserResponse):
    lastMessage: Optional[str] = None
    lastMessageTime: Optional[datetime] = None
    unreadCount: int = 0
    profileImageUrl: Optional[str] = None
