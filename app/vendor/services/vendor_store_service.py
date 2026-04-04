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
        where={"vendorId": vendor_id},
        include={"products": {"include": {"categories": True}}}
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

async def get_vendor_stats_service(vendor_id: int) -> dict:
    from datetime import datetime
    
    # 1. Get vendor's store
    store = await prisma.store.find_unique(where={"vendorId": vendor_id})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found for this vendor.")
    
    # 2. Total Earnings and Pending Orders
    suborders = await prisma.suborder.find_many(
        where={"storeId": store.id}
    )
    
    total_earnings = sum(so.vendorEarnings for so in suborders)
    total_pending = sum(1 for so in suborders if not so.isFulfield)
    
    # 3. Total Products
    total_products = await prisma.product.count(where={"storeId": store.id})
    
    # 4. Total Followers
    total_followers = await prisma.user.count(
        where={"followedStores": {"some": {"id": store.id}}}
    )
    
    # 5. Last 7 Days Earnings
    from datetime import datetime, timedelta
    now = datetime.now()
    last_7_days = []
    
    for i in range(7):
        target_date = now - timedelta(days=i)
        day_label = target_date.strftime("%A") # Monday, Tuesday, etc.
        
        # Sum earnings for this specific day
        day_sum = sum(
            so.vendorEarnings for so in suborders 
            if so.createdAt.year == target_date.year and 
               so.createdAt.month == target_date.month and 
               so.createdAt.day == target_date.day
        )
        
        last_7_days.append({
            "day": day_label,
            "earnings": day_sum
        })
    
    # Reverse to chronological order
    last_7_days.reverse()
    
    return {
        "storeName": store.name,
        "totalEarnings": total_earnings,
        "last7DaysEarnings": last_7_days,
        "totalPendingOrders": total_pending,
        "totalProducts": total_products,
        "totalFollowers": total_followers
    }
