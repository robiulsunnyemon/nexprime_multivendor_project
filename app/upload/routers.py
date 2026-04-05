from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
import cloudinary
import cloudinary.uploader

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/image", summary="Upload an image and get a live URL")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Form("general", description="Cloudinary folder name (optional)")
):
    """
    Dedicated endpoint to upload a single image to Cloudinary.
    Returns the live URL and public ID of the uploaded image.
    """
    contents = await file.read()
    try:
        result = cloudinary.uploader.upload(contents, folder=folder, resource_type="image")
        return {
            "message": "Image uploaded successfully",
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}",
        )
