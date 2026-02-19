import asyncio
import bcrypt
from prisma import Prisma

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def main():
    prisma = Prisma()
    await prisma.connect()

    print("Seeding database...")

    # Clear existing data to avoid conflicts during seeding if needed
    # await prisma.otp.delete_many()
    # await prisma.user.delete_many()

    users = [
        {
            "fullname": "Admin User",
            "email": "admin@nexprime.com",
            "phonenumber": "01700000000",
            "password": hash_password("admin123"),
            "role": "ADMIN",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
            "residentcard_backside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
        },
        {
            "fullname": "Vendor User",
            "email": "vendor@nexprime.com",
            "phonenumber": "01711111111",
            "password": hash_password("vendor123"),
            "role": "VENDOR",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
            "residentcard_backside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
        },
        {
            "fullname": "Customer User",
            "email": "customer@nexprime.com",
            "phonenumber": "01722222222",
            "password": hash_password("customer123"),
            "role": "CUSTOMER",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
            "residentcard_backside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
        },
    ]

    for user_data in users:
        existing = await prisma.user.find_unique(where={"email": user_data["email"]})
        if not existing:
            await prisma.user.create(data=user_data)
            print(f"Created user: {user_data['email']}")
        else:
            print(f"User already exists: {user_data['email']}")

    # Initialize SystemSetting
    setting = await prisma.systemsetting.find_unique(where={"id": 1})
    if not setting:
        await prisma.systemsetting.create(data={"id": 1, "isRegistrationEnabled": True})
        print("Initialized SystemSetting: Registration Enabled")
    else:
        print("SystemSetting already exists.")

    print("Seeding completed.")
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
