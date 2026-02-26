from app.database.db import prisma
from app.faq.schemas import FaqCreate, FaqUpdate, FaqStatus
from fastapi import HTTPException

class FaqService:
    @staticmethod
    async def create_faq(faq_data: FaqCreate):
        return await prisma.faq.create(
            data={
                "question": faq_data.question,
                "answer": faq_data.answer,
                "status": faq_data.status
            }
        )

    @staticmethod
    async def get_active_faqs():
        return await prisma.faq.find_many(
            where={"status": FaqStatus.ACTIVE},
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def get_all_faqs_admin():
        return await prisma.faq.find_many(
            order={"createdAt": "desc"}
        )

    @staticmethod
    async def update_faq(faq_id: int, update_data: FaqUpdate):
        faq = await prisma.faq.find_unique(where={"id": faq_id})
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        return await prisma.faq.update(
            where={"id": faq_id},
            data=update_dict
        )

    @staticmethod
    async def delete_faq(faq_id: int):
        faq = await prisma.faq.find_unique(where={"id": faq_id})
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        await prisma.faq.delete(where={"id": faq_id})
        return True
