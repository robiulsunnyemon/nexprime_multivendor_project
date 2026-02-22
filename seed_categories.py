import asyncio
from app.database.db import prisma

async def seed_categories():
    await prisma.connect()
    
    main_categories = [
        "Grocery",
        "Wardrobe",
        "Marketplace Management",
        "Country"
    ]
    
    for cat_name in main_categories:
        await prisma.maincategory.upsert(
            where={"name": cat_name},
            data={
                "create": {"name": cat_name},
                "update": {}
            }
        )
    
    print("Main categories seeded successfully.")
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_categories())
