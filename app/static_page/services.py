from app.database.db import prisma
from app.static_page.schemas import StaticPageCreate, StaticPageUpdate
from fastapi import HTTPException

class StaticPageService:
    @staticmethod
    async def create_or_update_page(page_data: StaticPageCreate):
        # We use upsert so admins can easily re-submit the same key
        return await prisma.staticpage.upsert(
            where={"key": page_data.key},
            data={
                "create": {
                    "key": page_data.key,
                    "title": page_data.title,
                    "content": page_data.content
                },
                "update": {
                    "title": page_data.title,
                    "content": page_data.content
                }
            }
        )

    @staticmethod
    async def get_page_by_key(key: str):
        page = await prisma.staticpage.find_unique(where={"key": key})
        if not page:
            raise HTTPException(status_code=404, detail=f"Page with key '{key}' not found")
        return page

    @staticmethod
    async def get_all_pages():
        return await prisma.staticpage.find_many(order={"title": "asc"})

    @staticmethod
    async def delete_page(key: str):
        page = await prisma.staticpage.find_unique(where={"key": key})
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        await prisma.staticpage.delete(where={"key": key})
        return True
