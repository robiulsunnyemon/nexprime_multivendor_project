from fastapi import APIRouter, Depends, HTTPException,status
from typing import List
from app.core.current_user import get_admin
from app.user.services.user_service import UserService
from app.user.schemas.user_schemas import UserResponse, StatusUpdate,VendorSchema,KYCStatusUpdate

customer_router = APIRouter(prefix="/customers", tags=["Users"])
vendor_router = APIRouter(prefix="/vendors", tags=["Vendors"])

@customer_router.get("", response_model=List[UserResponse],status_code=status.HTTP_200_OK)
async def get_all_customer(admin=Depends(get_admin)):
    """
    Get all users. Restricted to Admin.
    """
    return await UserService.get_all_customers()

@customer_router.get("/{customer_id}", response_model=UserResponse)
async def get_user_by_id(customer_id: int, admin=Depends(get_admin)):
    """
    Get user by ID. Restricted to Admin.
    """
    user = await UserService.get_user_by_id(customer_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user




@customer_router.patch("/{customer_id}/account_status", response_model=UserResponse)
async def update_user_status(customer_id: int, data: StatusUpdate, admin=Depends(get_admin)):
    """
    Update user account status. Restricted to Admin.
    Status: ACTIVE, SUSPEND, INACTIVE
    """
    try:
        return await UserService.update_user_status(customer_id, data.status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@customer_router.delete("/{customer_id}")
async def delete_user(customer_id: int, admin=Depends(get_admin)):
    """
    Delete user. Restricted to Admin.
    """
    try:
        await UserService.delete_user(customer_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@vendor_router.get("/active",response_model=List[VendorSchema] ,status_code=status.HTTP_200_OK)
async def get_all_active_vendor(admin=Depends(get_admin)):
    return await UserService.active_vendors_with_valid_kyc()


@vendor_router.get("/pending/all",response_model=List[VendorSchema] ,status_code=status.HTTP_200_OK)
async def get_all_pending_vendor(admin=Depends(get_admin)):
    return await UserService.pending_vendors_with_valid_kyc()



@vendor_router.delete("/{vendor_id}")
async def delete_user(vendor_id: int, admin=Depends(get_admin)):
    """
    Delete user. Restricted to Admin.
    """
    try:
        await UserService.delete_user(vendor_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@vendor_router.patch("/{vendor_id}/kyc_status", summary="Update KYC document status")
async def update_kyc_status(
    vendor_id: int,
    body: KYCStatusUpdate,
    admin=Depends(get_admin),
):
    return await UserService.update_kyc_status_service(vendor_id=vendor_id, status=body.status)