from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.db import prisma
from app.auth.routers.auth_router import router as auth_router
from app.user.routers.user_router import router as user_router

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