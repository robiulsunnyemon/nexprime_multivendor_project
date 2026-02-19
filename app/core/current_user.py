from fastapi import Depends, HTTPException
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

    return user


async def get_admin(user=Depends(get_current_user)):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admission denied. Admin only.")
    return user



async def get_vendor(user=Depends(get_current_user)):
    if user.role != "VENDOR":
        raise HTTPException(status_code=403, detail="Admission denied. Vendor only.")
    return user