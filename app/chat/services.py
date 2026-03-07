from datetime import datetime
from typing import List, Dict, Optional
from fastapi import WebSocket, HTTPException
from app.database.db import prisma
from app.chat.schemas import MessageCreate, MessageResponse, ActiveUserResponse
import json

class ConnectionManager:
    def __init__(self):
        # user_id -> List of active WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        # Mark user as active
        await prisma.user.update(
            where={"id": user_id},
            data={"lastActiveAt": datetime.now()}
        )

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(json.dumps(message))

manager = ConnectionManager()

class ChatService:
    @staticmethod
    async def save_message(sender_id: int, data: MessageCreate):
        # 1. Create message in DB
        db_message = await prisma.message.create(
            data={
                "content": data.content,
                "type": data.type,
                "senderId": sender_id,
                "receiverId": data.receiverId,
                "replyToId": data.replyToId,
            }
        )
        
        # 2. Update sender's activity
        await prisma.user.update(
            where={"id": sender_id},
            data={"lastActiveAt": datetime.now()}
        )
        
        return db_message

    @staticmethod
    async def get_chat_history(user_id: int, other_user_id: int):
        # Mark all unread messages from the other user as read
        await prisma.message.update_many(
            where={
                "senderId": other_user_id,
                "receiverId": user_id,
                "isRead": False
            },
            data={
                "isRead": True
            }
        )

        return await prisma.message.find_many(
            where={
                "OR": [
                    {"senderId": user_id, "receiverId": other_user_id},
                    {"senderId": other_user_id, "receiverId": user_id}
                ]
            },
            order={"createdAt": "asc"},
            include={"replyTo": True}
        )

    @staticmethod
    async def get_active_users_for_customer(current_user_id: int):
        # 1. Get users the current user has chatted with (Priority)
        interacted_messages = await prisma.message.find_many(
            where={
                "OR": [
                    {"senderId": current_user_id},
                    {"receiverId": current_user_id}
                ]
            },
            order={"createdAt": "desc"}
        )
        
        interacted_user_ids = []
        user_last_messages = {}
        unread_counts = {}

        for m in interacted_messages:
            other_id = m.receiverId if m.senderId == current_user_id else m.senderId
            if other_id not in interacted_user_ids:
                interacted_user_ids.append(other_id)
                user_last_messages[other_id] = {
                    "content": m.content if m.type == "TEXT" else f"Sent {m.type.lower()}",
                    "time": m.createdAt
                }
            
            # Count unread messages sent TO the current user BY the other user
            if m.receiverId == current_user_id and not m.isRead:
                unread_counts[other_id] = unread_counts.get(other_id, 0) + 1

        # 2. Get all users (except self)
        all_users = await prisma.user.find_many(
            where={"NOT": {"id": current_user_id}},
            order={"lastActiveAt": "desc"}
        )

        user_dict = {user.id: user for user in all_users}

        # 3. Build response with priority
        interacted_list = []
        others_list = []
        
        online_ids = manager.active_connections.keys()

        # Build list for users we have interacted with
        for uid in interacted_user_ids:
            if uid in user_dict:
                user = user_dict[uid]
                res = ActiveUserResponse(
                    id=user.id,
                    fullname=user.fullname,
                    email=user.email,
                    isOnline=user.id in online_ids,
                    lastActiveAt=user.lastActiveAt,
                    lastMessage=user_last_messages[uid]["content"],
                    lastMessageTime=user_last_messages[uid]["time"],
                    unreadCount=unread_counts.get(uid, 0),
                    profileImageUrl=user.profileImageUrl
                )
                interacted_list.append(res)
                # Remove so they don't appear in others_list
                del user_dict[uid]

        # Sort interacted_list strictly by lastMessageTime desc
        interacted_list.sort(key=lambda x: x.lastMessageTime, reverse=True)

        for user in user_dict.values():
            res = ActiveUserResponse(
                id=user.id,
                fullname=user.fullname,
                email=user.email,
                isOnline=user.id in online_ids,
                lastActiveAt=user.lastActiveAt,
                unreadCount=0,
                profileImageUrl=user.profileImageUrl
            )
            others_list.append(res)
                
        return interacted_list + others_list

    @staticmethod
    async def get_online_users_for_admin():
        online_ids = list(manager.active_connections.keys())
        users = await prisma.user.find_many(
            where={"id": {"in": online_ids}},
            order={"lastActiveAt": "desc"}
        )
        return users
