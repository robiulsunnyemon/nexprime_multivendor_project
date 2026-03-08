import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from app.database.db import prisma

async def _upload_image(file: UploadFile, folder: str = "stores") -> str:
    contents = await file.read()
    try:
        result = cloudinary.uploader.upload(contents, folder=folder, resource_type="image")
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Store photo upload failed: {str(e)}",
        )

async def create_store_service(
    name: str,
    bio: str | None,
    address: str,
    photo_file: UploadFile,
    cover_file: UploadFile | None,
    vendor_id: int
) -> dict:
    # 1. Check if vendor already has a store
    existing = await prisma.store.find_unique(where={"vendorId": vendor_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vendor already has a store. One vendor can have only one store."
        )

    # 2. Upload photos
    photo_url = await _upload_image(photo_file)
    cover_url = None
    if cover_file:
        cover_url = await _upload_image(cover_file)

    # 3. Create store
    store = await prisma.store.create(
        data={
            "name": name,
            "bio": bio,
            "address": address,
            "photo": photo_url,
            "coverImgUrl": cover_url,
            "vendorId": vendor_id
        }
    )

    return {"message": "Store created successfully.", "store": store}

async def get_my_store_service(vendor_id: int) -> dict:
    store = await prisma.store.find_unique(
        where={"vendorId": vendor_id}
    )
    if not store:
        raise HTTPException(status_code=404, detail="Store not found for this vendor.")
    
    follower_count = await prisma.user.count(
        where={"followedStores": {"some": {"id": store.id}}}
    )
    
    store_dict = store.model_dump()
    store_dict["followerCount"] = follower_count
    return store_dict

async def update_store_service(
    vendor_id: int,
    name: str | None = None,
    bio: str | None = None,
    address: str | None = None,
    photo_file: UploadFile | None = None,
    cover_file: UploadFile | None = None
) -> dict:
    store = await prisma.store.find_unique(where={"vendorId": vendor_id})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found.")

    update_data = {}
    if name is not None: update_data["name"] = name
    if bio is not None: update_data["bio"] = bio
    if address is not None: update_data["address"] = address
    if photo_file:
        update_data["photo"] = await _upload_image(photo_file)
    if cover_file:
        update_data["coverImgUrl"] = await _upload_image(cover_file)

    updated_store = await prisma.store.update(
        where={"vendorId": vendor_id},
        data=update_data
    )

    follower_count = await prisma.user.count(
        where={"followedStores": {"some": {"id": updated_store.id}}}
    )

    store_dict = updated_store.model_dump()
    store_dict["followerCount"] = follower_count
    return {"message": "Store updated successfully.", "store": store_dict}
