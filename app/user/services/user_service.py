from app.database.db import prisma
from fastapi import BackgroundTasks
from app.user.schemas.user_schemas import AccountStatus
from fastapi import HTTPException
from app.core.send_email import send_email
from app.core.config import settings

class UserService:
    @staticmethod
    async def get_all_customers():
        return await prisma.user.find_many(
            where={
                "role": "CUSTOMER",
            }
        )

    @staticmethod
    async def get_user_by_id(user_id: int):
        return await prisma.user.find_unique(where={"id": user_id,"role":"CUSTOMER"})

    @staticmethod
    async def update_user_status(user_id: int,background_tasks:BackgroundTasks, status: AccountStatus):
        db_user= await prisma.user.find_unique(where={"id":user_id})
        if not db_user:
            raise HTTPException(status_code=404, detail="User account is not found")

        background_tasks.add_task(
            send_email,
            db_user.email,
            settings.EMAIL_FROM,
            status,
            settings.SMTP_PASS
        )
        return await prisma.user.update(
            where={"id": user_id},
            data={"status": status}
        )

    @staticmethod
    async def delete_user(user_id: int):
        return await prisma.user.delete(where={"id": user_id})

    @staticmethod
    async def active_vendors_with_valid_kyc():
        vendors = await prisma.user.find_many(
            where={
                "role": "VENDOR",
                "kycFiles": {
                    "some": {  # 👈 at least one KYC matches
                        "status": {
                            "in": ["ACTIVE", "SUSPEND"]
                        }
                    }
                }
            },
            include={
                "store": True,
                "kycFiles": True
            }
        )

        return vendors


    @staticmethod
    async def pending_vendors_with_valid_kyc():
        vendors = await prisma.user.find_many(
            where={
                "role": "VENDOR",
                "kycFiles": {
                    "some": {
                        "status": {
                            "in": ["PENDING"]
                        }
                    }
                }
            },
            include={
                "store": True,
                "kycFiles": True
            }
        )

        return vendors

    @staticmethod
    async def update_kyc_status_service(vendor_id: int,background_tasks: BackgroundTasks,  status: str) -> dict:
        if status == "REJECTED":
            db_vendor = await prisma.user.find_unique(where={"id": vendor_id})
            if not db_vendor:
                raise HTTPException(status_code=404, detail="Vendor account is not found")

            background_tasks.add_task(
                send_email,
                db_vendor.email,
                settings.EMAIL_FROM,
                status,
                settings.SMTP_PASS
            )
            await prisma.user.delete(where={"id": vendor_id})
            return {"message": f"KYC file status updated to {status}."}
        kyc_file = await prisma.kycfile.find_first(where={"vendorId": vendor_id})
        if not kyc_file:
            raise HTTPException(status_code=404, detail="KYC file not found.")
        updated = await prisma.kycfile.update(
            where={"id": kyc_file.id},
            data={"status": status}
        )
        return {"message": f"KYC file status updated to {status}.", "kyc_file": updated}

    @staticmethod
    async def update_user_profile(user_id: int, update_data: dict) -> dict:
        db_user = await prisma.user.find_unique(where={"id": user_id})
        if not db_user:
            raise HTTPException(status_code=404, detail="User account is not found")

        # Prepare update dictionary removing None values
        data_to_update = {k: v for k, v in update_data.items() if v is not None}
        
        if not data_to_update:
            return db_user

        # Hash password if it's being updated
        if "password" in data_to_update:
            import bcrypt
            hashed_pw = bcrypt.hashpw(data_to_update["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            data_to_update["password"] = hashed_pw

        updated_user = await prisma.user.update(
            where={"id": user_id},
            data=data_to_update
        )
        return updated_user