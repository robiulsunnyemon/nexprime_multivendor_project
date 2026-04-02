import asyncio
import bcrypt
from app.database.db import prisma

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def seed():
    await prisma.connect()
    
    # 1. Clean up existing test data (Optional, but safer for re-runs)
    test_emails = ["admin_test@nexprime.com", "customer_test@nexprime.com", "vendor1_test@nexprime.com", "vendor2_test@nexprime.com"]
    await prisma.user.delete_many(where={"email": {"in": test_emails}})
    await prisma.maincategory.delete_many(where={"name": "Test Main Category"})

    print("Seeding test data...")

    # 2. Create Admin
    admin = await prisma.user.create(
        data={
            "fullname": "Test Admin",
            "email": "admin_test@nexprime.com",
            "phonenumber": "01000000001",
            "password": hash_password("Admin123!"),
            "role": "ADMIN",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://via.placeholder.com/150",
            "residentcard_backside": "https://via.placeholder.com/150",
        }
    )

    # 3. Create Vendors and Stores
    vendor1 = await prisma.user.create(
        data={
            "fullname": "Vendor One",
            "email": "vendor1_test@nexprime.com",
            "phonenumber": "01000000002",
            "password": hash_password("Vendor123!"),
            "role": "VENDOR",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://via.placeholder.com/150",
            "residentcard_backside": "https://via.placeholder.com/150",
            "store": {
                "create": {
                    "name": "Test Store 1",
                    "bio": "Test Bio 1",
                    "address": "Test Address 1",
                    "photo": "https://via.placeholder.com/150",
                }
            }
        }
    )

    vendor2 = await prisma.user.create(
        data={
            "fullname": "Vendor Two",
            "email": "vendor2_test@nexprime.com",
            "phonenumber": "01000000003",
            "password": hash_password("Vendor123!"),
            "role": "VENDOR",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://via.placeholder.com/150",
            "residentcard_backside": "https://via.placeholder.com/150",
            "store": {
                "create": {
                    "name": "Test Store 2",
                    "bio": "Test Bio 2",
                    "address": "Test Address 2",
                    "photo": "https://via.placeholder.com/150",
                }
            }
        }
    )

    # 4. Create Customer
    customer = await prisma.user.create(
        data={
            "fullname": "Test Customer",
            "email": "customer_test@nexprime.com",
            "phonenumber": "01000000004",
            "password": hash_password("Customer123!"),
            "role": "CUSTOMER",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://via.placeholder.com/150",
            "residentcard_backside": "https://via.placeholder.com/150",
        }
    )

    # 5. Follow Store 1
    store1 = await prisma.store.find_unique(where={"vendorId": vendor1.id})
    await prisma.user.update(
        where={"id": customer.id},
        data={"followedStores": {"connect": [{"id": store1.id}]}}
    )

    # 6. Create Live Streams
    stream1 = await prisma.livestream.create(
        data={
            "title": "Vendor 1 Live Stream",
            "thumbnail": "https://via.placeholder.com/150",
            "streamerId": vendor1.id,
            "isActive": True
        }
    )

    stream2 = await prisma.livestream.create(
        data={
            "title": "Vendor 2 Live Stream",
            "thumbnail": "https://via.placeholder.com/150",
            "streamerId": vendor2.id,
            "isActive": True
        }
    )

    # 7. Create Category
    main_cat = await prisma.maincategory.create(
        data={
            "name": "Test Main Category",
            "subCategories": {
                "create": [
                    {
                        "name": "Test Sub Category",
                        "image": "https://via.placeholder.com/150"
                    }
                ]
            }
        }
    )

    print("Seeding completed successfully!")
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(seed())
