from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.db import prisma
from app.auth.routers.auth_router import router as auth_router
from app.user.routers.user_router import router as user_router
from app.admin.routers.admin_settings_router import router as admin_settings_router
from app.vendor.routers.vendor_store_router import router as vendor_store_router
from app.vendor.routers.vendor_kyc_router import router as vendor_kyc_router
from app.admin.routers.admin_kyc_router import router as admin_kyc_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(
    title="NexPrime API",
    description="E-commerce API with FastAPI and Prisma",
    version="1.0.0",
    lifespan=lifespan
)



@app.get("/")
async def root():
    return {
        "message": "Welcome to NexPrime API",
        "status": "Running",
        "database": "Connected"
    }


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_settings_router)
app.include_router(vendor_store_router)
app.include_router(vendor_kyc_router)
app.include_router(admin_kyc_router)