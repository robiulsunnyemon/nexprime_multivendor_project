from app.database.db import prisma
from fastapi import HTTPException

class StorePublicService:
    @staticmethod
    async def get_all_stores():
        return await prisma.store.find_many(
            include={
                "vendor": True,
                "products": {
                    "include": {"categories": True}
                }
            },
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def get_store_by_id(store_id: int):
        store = await prisma.store.find_unique(
            where={"id": store_id},
            include={
                "vendor": True,
                "products": {
                    "include": {"categories": True}
                }
            }
        )
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        return store
