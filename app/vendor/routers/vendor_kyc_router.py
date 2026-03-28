from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from app.core.current_user import get_vendor
from app.vendor.services.vendor_kyc_service import (
    upload_kyc_service,
    get_my_kyc_files_service,
    delete_my_kyc_file_service,
)

router = APIRouter(prefix="/vendor/kyc", tags=["Vendor - KYC"])

# @router.post("", status_code=status.HTTP_201_CREATED, summary="Upload a KYC document")
# async def upload_kyc(
#     file: UploadFile = File(...),
#     current_vendor=Depends(get_vendor),
# ):
#     return await upload_kyc_service(
#         vendor_id=current_vendor.id,
#         file=file,
#         title="vendor_kyc"
#     )

@router.get("/me", summary="Get my KYC documents")
async def get_my_kyc(current_vendor=Depends(get_vendor)):
    return await get_my_kyc_files_service(vendor_id=current_vendor.id)

@router.delete("/{file_id}", summary="Delete a KYC document")
async def delete_my_kyc(
    file_id: int,
    current_vendor=Depends(get_vendor),
):
    return await delete_my_kyc_file_service(
        vendor_id=current_vendor.id,
        file_id=file_id
    )
