from app.database.db import prisma
from app.user.schemas.user_schemas import AccountStatus

class UserService:
    @staticmethod
    async def get_all_users():
        return await prisma.user.find_many()

    @staticmethod
    async def get_user_by_id(user_id: int):
        return await prisma.user.find_unique(where={"id": user_id})

    @staticmethod
    async def update_user_status(user_id: int, status: AccountStatus):
        return await prisma.user.update(
            where={"id": user_id},
            data={"status": status}
        )

    @staticmethod
    async def delete_user(user_id: int):
        return await prisma.user.delete(where={"id": user_id})
