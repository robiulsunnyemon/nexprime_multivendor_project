from fastapi import Depends, HTTPException
from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.database.db import prisma
import jwt
from app.core.config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user = await prisma.user.find_unique(where={"id": user_id})

    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    # Status check
    status_errors = {
        "SUSPEND": "Account suspended. Please contact admin.",
        "INACTIVE": "Account inactive. Please contact admin.",
    }
    if user.status in status_errors:
        raise HTTPException(status_code=403, detail=status_errors[user.status])

    # Maintenance mode check
    setting = await prisma.systemsetting.find_unique(where={"id": 1})
    if setting and setting.isMaintenanceModeEnabled and user.role != "ADMIN":
        raise HTTPException(
            status_code=503,
            detail="System is currently under maintenance. Only administrators are allowed access."
        )

    return user


async def get_admin(user=Depends(get_current_user)):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admission denied. Admin only.")
    return user


async def get_vendor(user=Depends(get_current_user)):
    if user.role != "VENDOR":
        raise HTTPException(status_code=403, detail="Admission denied. Vendor only.")
    return user


async def get_customer(user=Depends(get_current_user)):
    if user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Admission denied. Customer only.")
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
):
    if not credentials:
        return None
        
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except Exception:
        return None

    user = await prisma.user.find_unique(where={"id": user_id})
    if user:
        if user.status in ["SUSPEND", "INACTIVE"]:
            return None
        setting = await prisma.systemsetting.find_unique(where={"id": 1})
        if setting and setting.isMaintenanceModeEnabled and user.role != "ADMIN":
            return None
    return user