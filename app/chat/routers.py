from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, HTTPException
from typing import List
from app.core.current_user import get_customer, get_admin, get_current_user
from app.chat.services import manager, ChatService
from app.chat.schemas import MessageResponse, MessageCreate, ActiveUserResponse, ChatUserResponse
from app.auth.services.auth_service import get_user_by_token
import cloudinary.uploader
import json

router = APIRouter(prefix="/chat", tags=["Real-time Messaging"])

@router.websocket("/ws/{token}")
async def websocket_chat(websocket: WebSocket, token: str):
    # 1. Authenticate via token
    try:
        user = await get_user_by_token(token)
        if not user:
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(user.id, websocket)
    try:
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            try:
                message_data = MessageCreate.model_validate_json(data)
                
                # Save to DB
                saved_msg = await ChatService.save_message(user.id, message_data)
                
                # Broadcast to receiver (and sender for sync)
                msg_dict = MessageResponse.model_validate(saved_msg).model_dump(mode="json")
                await manager.send_personal_message(msg_dict, message_data.receiverId)
                
                # Send back the saved message as acknowledgement
                await websocket.send_text(json.dumps(msg_dict))
                
            except Exception as e:
                print(f"Chat Message Error for user {user.id}: {str(e)}")
                try:
                    await websocket.send_text(json.dumps({"error": str(e)}))
                except:
                    pass
            
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)
    except Exception as e:
        print(f"WebSocket Connection Fatal Error: {str(e)}")
        manager.disconnect(user.id, websocket)

@router.get("/history/{other_user_id}", response_model=List[MessageResponse])
async def get_chat_history(
    other_user_id: int, 
    current_user = Depends(get_customer)
):
    return await ChatService.get_chat_history(current_user.id, other_user_id)

@router.get("/active-users", response_model=List[ActiveUserResponse])
async def get_active_users(current_user = Depends(get_customer)):
    return await ChatService.get_active_users_for_customer(current_user.id)

@router.get("/admin/online-users", response_model=List[ChatUserResponse])
async def get_online_users(current_admin = Depends(get_admin)):
    return await ChatService.get_online_users_for_admin()

@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    # Check file type
    content_type = file.content_type or ""
    resource_type = "auto"
    if content_type.startswith("image/"):
        resource_type = "image"
    elif content_type.startswith("video/"):
        resource_type = "video"
    elif content_type.startswith("audio/"):
        resource_type = "video" # Cloudinary treats audio as video for resource_type
        
    try:
        upload_result = cloudinary.uploader.upload(
            file.file, 
            folder="nexprime_chat",
            resource_type=resource_type
        )
        return {"url": upload_result.get("url"), "type": resource_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
