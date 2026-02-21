import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from app.database.db import prisma

async def _upload_kyc_file(file: UploadFile, folder: str = "vendor_kyc") -> str:
    contents = await file.read()
    try:
        # We use resource_type="auto" to allow PDFs or images if needed
        result = cloudinary.uploader.upload(contents, folder=folder, resource_type="auto")
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KYC file upload failed: {str(e)}",
        )

async def upload_kyc_service(
    vendor_id: int,
    file: UploadFile,
    title: str = "vendor_kyc"
) -> dict:
    file_url = await _upload_kyc_file(file)
    
    kyc_file = await prisma.kycfile.create(
        data={
            "title": title,
            "fileUrl": file_url,
            "vendorId": vendor_id
        }
    )
    return {"message": "KYC file uploaded successfully.", "kyc_file": kyc_file}

async def get_my_kyc_files_service(vendor_id: int) -> list:
    return await prisma.kycfile.find_many(
        where={"vendorId": vendor_id},
        order={"createdAt": "desc"}
    )

async def delete_my_kyc_file_service(vendor_id: int, file_id: int) -> dict:
    # Ensure it belongs to the vendor
    kyc_file = await prisma.kycfile.find_first(
        where={"id": file_id, "vendorId": vendor_id}
    )
    if not kyc_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_SERVER_ERROR,
            detail="KYC file not found or you don't have permission to delete it."
        )
    
    await prisma.kycfile.delete(where={"id": file_id})
    return {"message": "KYC file deleted successfully."}

# Admin Services
async def get_vendor_kyc_files_service(vendor_id: int) -> list:
    return await prisma.kycfile.find_many(
        where={"vendorId": vendor_id},
        order={"createdAt": "desc"}
    )

async def delete_kyc_file_admin_service(file_id: int) -> dict:
    kyc_file = await prisma.kycfile.find_unique(where={"id": file_id})
    if not kyc_file:
        raise HTTPException(status_code=404, detail="KYC file not found.")
    
    await prisma.kycfile.delete(where={"id": file_id})
    return {"message": "KYC file deleted by admin successfully."}





