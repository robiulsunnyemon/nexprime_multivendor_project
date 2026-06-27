import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from app.database.db import prisma
from datetime import date

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

async def get_vendor_stats_service(
    vendor_id: int, 
    filter_type: str = "last_7_days", 
    start_date: date | None = None, 
    end_date: date | None = None
) -> dict:
    from datetime import datetime, timedelta, date, timezone
    
    # 1. Get vendor's store
    store = await prisma.store.find_unique(where={"vendorId": vendor_id})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found for this vendor.")
    
    # 2. Determine start and end datetime based on filter (UTC)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    if filter_type == "today":
        start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == "yesterday":
        yesterday = now - timedelta(days=1)
        start_datetime = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == "last_7_days":
        start_datetime = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == "last_30_days":
        start_datetime = (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == "this_month":
        start_datetime = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_datetime = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == "last_1_year":
        start_datetime = (now - timedelta(days=364)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == "custom":
        if not start_date:
            raise HTTPException(status_code=400, detail="start_date is required for custom filter.")
        start_datetime = datetime.combine(start_date, datetime.min.time())
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
        else:
            end_datetime = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        raise HTTPException(status_code=400, detail="Invalid filter type.")
        
    # 3. Query suborders within the date range
    suborders = await prisma.suborder.find_many(
        where={
            "storeId": store.id,
            "createdAt": {
                "gte": start_datetime,
                "lte": end_datetime
            }
        }
    )
    
    # 4. Filtered Earnings and Pending Orders
    total_earnings = sum(so.vendorEarnings for so in suborders)
    total_pending = sum(1 for so in suborders if not so.isFulfield)
    
    # 5. Total Products and Followers
    total_products = await prisma.product.count(where={"storeId": store.id})
    total_followers = await prisma.user.count(
        where={"followedStores": {"some": {"id": store.id}}}
    )
    
    # 6. Generate earningsOverTime
    earnings_over_time = []
    
    if filter_type in ("today", "yesterday"):
        # Hourly breakdown
        for hour in range(24):
            hour_start = start_datetime + timedelta(hours=hour)
            hour_end = start_datetime + timedelta(hours=hour, minutes=59, seconds=59, microseconds=999999)
            hour_label = hour_start.strftime("%I %p") # e.g., "12 AM", "01 PM"
            
            hour_earnings = sum(
                so.vendorEarnings for so in suborders
                if hour_start <= so.createdAt <= hour_end
            )
            earnings_over_time.append({
                "day": hour_label,
                "earnings": hour_earnings
            })
    elif filter_type == "last_1_year":
        # Monthly breakdown
        for i in range(12):
            current_month_val = now.month
            current_year_val = now.year
            
            months_to_subtract = 11 - i
            target_month = current_month_val - months_to_subtract
            target_year = current_year_val
            while target_month <= 0:
                target_month += 12
                target_year -= 1
                
            month_start = datetime(target_year, target_month, 1)
            if target_month == 12:
                next_month_start = datetime(target_year + 1, 1, 1)
            else:
                next_month_start = datetime(target_year, target_month + 1, 1)
            month_end = next_month_start - timedelta(microseconds=1)
            
            # Boundary checks
            if month_end > end_datetime:
                month_end = end_datetime
            if month_start < start_datetime:
                month_start = start_datetime
                
            month_label = month_start.strftime("%b %Y") # e.g., "Jun 2026"
            
            month_earnings = sum(
                so.vendorEarnings for so in suborders
                if month_start <= so.createdAt <= month_end
            )
            earnings_over_time.append({
                "day": month_label,
                "earnings": month_earnings
            })
    else:
        # Daily breakdown
        delta = end_datetime - start_datetime
        days_count = delta.days + 1
        for i in range(days_count):
            day_start = start_datetime + timedelta(days=i)
            day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if days_count <= 7:
                day_label = day_start.strftime("%A") # e.g., "Monday", "Tuesday"
            else:
                day_label = day_start.strftime("%d %b") # e.g., "27 Jun"
                
            day_earnings = sum(
                so.vendorEarnings for so in suborders
                if day_start <= so.createdAt <= day_end
            )
            earnings_over_time.append({
                "day": day_label,
                "earnings": day_earnings
            })
            
    return {
        "storeName": store.name,
        "totalEarnings": total_earnings,
        "earningsOverTime": earnings_over_time,
        "totalPendingOrders": total_pending,
        "totalProducts": total_products,
        "totalFollowers": total_followers,
        "filterType": filter_type
    }
