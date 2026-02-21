from app.database.db import prisma
from app.user.schemas.user_schemas import AccountStatus
from fastapi import HTTPException

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
    async def update_user_status(user_id: int, status: AccountStatus):
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
    async def update_kyc_status_service(vendor_id: int, status: str) -> dict:
        if status == "REJECTED":
            db_vendor = await prisma.user.find_unique(where={"id": vendor_id})
            if not db_vendor:
                raise HTTPException(status_code=404, detail="Vendor account is not found")
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