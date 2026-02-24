from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.current_user import get_admin
from app.database.db import prisma

router = APIRouter(prefix="/admin/marketing-settings", tags=["Admin - Marketing Settings"])

class MarketingSettingUpdate(BaseModel):
    isPublishingEnabled: Optional[bool] = None
    publishingFee: Optional[float] = None

@router.get("", summary="Get marketing product settings")
async def get_marketing_settings():
    setting = await prisma.marketingproductsetting.find_unique(where={"id": 1})
    if not setting:
        # Return defaults if not yet configured
        return {"id": 1, "isPublishingEnabled": True, "publishingFee": 0.50}
    return setting

@router.patch("", summary="Update marketing product settings (toggle & fee)")
async def update_marketing_settings(
    body: MarketingSettingUpdate,
    admin=Depends(get_admin)
):
    update_data = {}
    if body.isPublishingEnabled is not None:
        update_data["isPublishingEnabled"] = body.isPublishingEnabled
    if body.publishingFee is not None:
        update_data["publishingFee"] = body.publishingFee

    setting = await prisma.marketingproductsetting.upsert(
        where={"id": 1},
        data={
            "create": {
                "id": 1,
                "isPublishingEnabled": body.isPublishingEnabled if body.isPublishingEnabled is not None else True,
                "publishingFee": body.publishingFee if body.publishingFee is not None else 0.50
            },
            "update": update_data
        }
    )
    return {
        "message": "Marketing settings updated successfully.",
        "settings": setting
    }
