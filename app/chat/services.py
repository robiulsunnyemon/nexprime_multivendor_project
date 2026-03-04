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
        for m in interacted_messages:
            other_id = m.receiverId if m.senderId == current_user_id else m.senderId
            if other_id not in interacted_user_ids:
                interacted_user_ids.append(other_id)
                user_last_messages[other_id] = {
                    "content": m.content,
                    "time": m.createdAt
                }

        # 2. Get all users (except self)
        all_users = await prisma.user.find_many(
            where={"NOT": {"id": current_user_id}},
            order={"lastActiveAt": "desc"}
        )

        # 3. Build response with priority
        interacted_list = []
        others_list = []
        
        online_ids = manager.active_connections.keys()

        for user in all_users:
            res = ActiveUserResponse(
                id=user.id,
                fullname=user.fullname,
                email=user.email,
                isOnline=user.id in online_ids,
                lastActiveAt=user.lastActiveAt
            )
            
            if user.id in interacted_user_ids:
                res.lastMessage = user_last_messages[user.id]["content"]
                res.lastMessageTime = user_last_messages[user.id]["time"]
                interacted_list.append(res)
            else:
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
