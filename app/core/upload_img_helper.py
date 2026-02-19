
import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status



async def upload_image_helper(file: UploadFile, folder: str = "unnamed_folder") -> str:
    contents = await file.read()
    try:
        result = cloudinary.uploader.upload(contents, folder=folder, resource_type="image")
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}",
        )