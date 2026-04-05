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
        # 1. Mark previous messages FROM the recipient TO this sender as read
        # because if the sender is now replying/sending a message, they must have seen the other's messages.
        await prisma.message.update_many(
            where={
                "senderId": data.receiverId,
                "receiverId": sender_id,
                "isRead": False
            },
            data={"isRead": True}
        )

        # 2. Create message in DB
        db_message = await prisma.message.create(
            data={
                "content": data.content,
                "type": data.type,
                "senderId": sender_id,
                "receiverId": data.receiverId,
                "replyToId": data.replyToId,
            }
        )
        
        # 3. Update sender's activity
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
    async def get_conversations(current_user_id: int):
        # 1. Get unique user IDs from messages (sender or receiver)
        messages = await prisma.message.find_many(
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

        for m in messages:
            other_id = m.receiverId if m.senderId == current_user_id else m.senderId
            if other_id == current_user_id: continue # Should not happen, but safety first
            
            if other_id not in interacted_user_ids:
                interacted_user_ids.append(other_id)
                user_last_messages[other_id] = {
                    "content": m.content if m.type == "TEXT" else f"Sent {m.type.lower()}",
                    "time": m.createdAt
                }
            
            # Count unread messages sent TO the current user BY the other user
            if m.receiverId == current_user_id and not m.isRead:
                unread_counts[other_id] = unread_counts.get(other_id, 0) + 1

        if not interacted_user_ids:
            return []

        # 2. Get user details
        users = await prisma.user.find_many(
            where={"id": {"in": interacted_user_ids}}
        )
        user_dict = {user.id: user for user in users}
        
        online_ids = manager.active_connections.keys()

        # 3. Build response
        result = []
        from app.chat.schemas import ConversationResponse
        for uid in interacted_user_ids:
            if uid in user_dict:
                user = user_dict[uid]
                res = ConversationResponse(
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
                result.append(res)
        
        return result

    @staticmethod
    async def get_online_users(current_user_id: int):
        online_ids = list(manager.active_connections.keys())
        if current_user_id in online_ids:
            online_ids.remove(current_user_id)
        
        if not online_ids:
            return []

        users = await prisma.user.find_many(
            where={"id": {"in": online_ids}},
            order={"lastActiveAt": "desc"}
        )
        
        from app.chat.schemas import ActiveUserResponse
        return [
            ActiveUserResponse(
                id=u.id,
                fullname=u.fullname,
                email=u.email,
                isOnline=True,
                lastActiveAt=u.lastActiveAt,
                profileImageUrl=u.profileImageUrl
            ) for u in users
        ]

    @staticmethod
    async def mark_messages_as_read(current_user_id: int, sender_id: int):
        await prisma.message.update_many(
            where={
                "senderId": sender_id,
                "receiverId": current_user_id,
                "isRead": False
            },
            data={
                "isRead": True
            }
        )
        return {"message": "Messages marked as read"}

    @staticmethod
    async def get_active_users_for_customer(current_user_id: int):
        # Keep for backward compatibility if needed, but point to new endpoints
        # This currently combined logic can stay as is if the user hasn't explicitly asked to DELETE it.
        # But I'll optimize it to use the same logic as get_conversations + online users.
        conversations = await ChatService.get_conversations(current_user_id)
        online_users = await ChatService.get_online_users(current_user_id)
        
        # Merge lists, avoiding duplicates
        conv_ids = {c.id for c in conversations}
        for o in online_users:
            if o.id not in conv_ids:
                # Add to end
                conversations.append(o)
        
        return conversations

    @staticmethod
    async def get_online_users_for_admin():
        online_ids = list(manager.active_connections.keys())
        users = await prisma.user.find_many(
            where={"id": {"in": online_ids}},
            order={"lastActiveAt": "desc"}
        )
        return users
