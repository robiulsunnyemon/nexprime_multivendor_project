from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.current_user import get_admin
from app.database.db import prisma

router = APIRouter(prefix="/admin/system-settings", tags=["Admin - System Settings"])

class SystemSettingUpdate(BaseModel):
    isRegistrationEnabled: Optional[bool] = None
    isLiveStreamingEnabled: Optional[bool] = None

@router.get("", summary="Get global system settings")
async def get_system_settings():
    setting = await prisma.systemsetting.find_unique(where={"id": 1})
    if not setting:
        # Default settings if none found
        return {
            "id": 1, 
            "isRegistrationEnabled": True, 
            "isLiveStreamingEnabled": True
        }
    return setting

@router.patch("", summary="Update global system settings (Admin only)")
async def update_system_settings(
    body: SystemSettingUpdate,
    admin=Depends(get_admin)
):
    update_data = {}
    if body.isRegistrationEnabled is not None:
        update_data["isRegistrationEnabled"] = body.isRegistrationEnabled
    if body.isLiveStreamingEnabled is not None:
        update_data["isLiveStreamingEnabled"] = body.isLiveStreamingEnabled

    setting = await prisma.systemsetting.find_unique(where={"id": 1})
    if not setting:
        setting = await prisma.systemsetting.create(
            data={
                "id": 1,
                "isRegistrationEnabled": body.isRegistrationEnabled if body.isRegistrationEnabled is not None else True,
                "isLiveStreamingEnabled": body.isLiveStreamingEnabled if body.isLiveStreamingEnabled is not None else True
            }
        )
    else:
        setting = await prisma.systemsetting.update(
            where={"id": 1},
            data=update_data
        )
    return {
        "message": "System settings updated successfully.",
        "settings": setting
    }
