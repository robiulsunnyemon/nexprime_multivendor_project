from app.database.db import prisma
from fastapi import HTTPException

class StorePublicService:
    @staticmethod
    async def get_all_stores():
        stores = await prisma.store.find_many(
            include={
                "vendor": True,
                "products": {
                    "include": {"categories": True}
                }
            },
            order={"createdAt": "desc"}
        )
        
        results = []
        for store in stores:
            count = await prisma.user.count(
                where={"followedStores": {"some": {"id": store.id}}}
            )
            store_dict = store.model_dump()
            store_dict["followerCount"] = count
            results.append(store_dict)
        return results

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
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        results = []
        for store in user.followedStores:
            count = await prisma.user.count(
                where={"followedStores": {"some": {"id": store.id}}}
            )
            store_dict = store.model_dump()
            store_dict["followerCount"] = count
            results.append(store_dict)
        return results

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
        
        count = await prisma.user.count(
            where={"followedStores": {"some": {"id": store.id}}}
        )
        store_dict = store.model_dump()
        store_dict["followerCount"] = count
        return store_dict

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
    async def get_store_follower_count(store_id: int):
        # First check if store exists
        store = await prisma.store.find_unique(where={"id": store_id})
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Use prisma count for followers relationship
        count = await prisma.user.count(
            where={"followedStores": {"some": {"id": store_id}}}
        )
        return {"store_id": store_id, "followerCount": count}
