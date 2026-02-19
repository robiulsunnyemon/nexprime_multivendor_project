from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.current_user import get_admin
from app.database.db import prisma

router = APIRouter(prefix="/admin/settings", tags=["Admin - Settings"])

class RegistrationToggleRequest(BaseModel):
    isRegistrationEnabled: bool

@router.patch("/registration", summary="Toggle user registration")
async def toggle_registration(
    body: RegistrationToggleRequest,
    admin=Depends(get_admin)
):
    setting = await prisma.systemsetting.upsert(
        where={"id": 1},
        data={
            "create": {"id": 1, "isRegistrationEnabled": body.isRegistrationEnabled},
            "update": {"isRegistrationEnabled": body.isRegistrationEnabled}
        }
    )
    status_str = "Enabled" if setting.isRegistrationEnabled else "Disabled"
    return {"message": f"User registration {status_str} successfully."}

@router.get("", summary="Get system settings")
async def get_settings(admin=Depends(get_admin)):
    setting = await prisma.systemsetting.find_unique(where={"id": 1})
    return setting
