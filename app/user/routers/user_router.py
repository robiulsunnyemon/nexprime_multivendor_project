from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.current_user import get_admin
from app.user.services.user_service import UserService
from app.user.schemas.user_schemas import UserResponse, StatusUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/all", response_model=List[UserResponse])
async def get_all_users(admin=Depends(get_admin)):
    """
    Get all users. Restricted to Admin.
    """
    return await UserService.get_all_users()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, admin=Depends(get_admin)):
    """
    Get user by ID. Restricted to Admin.
    """
    user = await UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(user_id: int, data: StatusUpdate, admin=Depends(get_admin)):
    """
    Update user account status. Restricted to Admin.
    """
    try:
        return await UserService.update_user_status(user_id, data.status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(user_id: int, admin=Depends(get_admin)):
    """
    Delete user. Restricted to Admin.
    """
    try:
        await UserService.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
