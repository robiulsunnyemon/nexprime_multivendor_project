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

    @staticmethod
    async def toggle_follow_store(store_id: int, user_id: int):
        # Check if store exists
        store = await prisma.store.find_unique(where={"id": store_id})
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

        # Check if already following
        user = await prisma.user.find_unique(
            where={"id": user_id},
            include={"followedStores": {"where": {"id": store_id}}}
        )
        
        is_following = len(user.followedStores) > 0 if user.followedStores else False
        
        if is_following:
            # Unfollow
            await prisma.user.update(
                where={"id": user_id},
                data={"followedStores": {"disconnect": [{"id": store_id}]}}
            )
            return {"message": "Unfollowed successfully", "following": False}
        else:
            # Follow
            await prisma.user.update(
                where={"id": user_id},
                data={"followedStores": {"connect": [{"id": store_id}]}}
            )
            return {"message": "Followed successfully", "following": True}

    @staticmethod
    async def get_followed_stores(user_id: int):
        user = await prisma.user.find_unique(
            where={"id": user_id},
            include={
                "followedStores": {
                    "include": {
                        "vendor": True,
                        "products": {"include": {"categories": True}}
                    }
                }
            }
        )
        return user.followedStores if user else []
