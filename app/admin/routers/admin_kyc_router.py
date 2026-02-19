from fastapi import APIRouter, Depends, status
from app.core.current_user import get_admin
from pydantic import BaseModel
from app.vendor.services.vendor_kyc_service import (
    get_vendor_kyc_files_service,
    delete_kyc_file_admin_service,
    update_kyc_status_service,
)

router = APIRouter(prefix="/admin/kyc", tags=["Admin - KYC"])

class KYCStatusUpdate(BaseModel):
    status: str # Ideally validated against the enum PENDING, ACTIVE, REJECTED

@router.get("/vendor/{vendor_id}", summary="Get KYC documents of a specific vendor")
async def get_vendor_kyc(
    vendor_id: int,
    admin=Depends(get_admin),
):
    return await get_vendor_kyc_files_service(vendor_id=vendor_id)

@router.patch("/{file_id}/status", summary="Update KYC document status")
async def update_kyc_status(
    file_id: int,
    body: KYCStatusUpdate,
    admin=Depends(get_admin),
):
    return await update_kyc_status_service(file_id=file_id, status=body.status.upper())

@router.delete("/{file_id}", summary="Delete any KYC document")
async def delete_kyc_admin(
    file_id: int,
    admin=Depends(get_admin),
):
    return await delete_kyc_file_admin_service(file_id=file_id)
