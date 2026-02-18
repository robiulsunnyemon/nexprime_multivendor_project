from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.db import prisma


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