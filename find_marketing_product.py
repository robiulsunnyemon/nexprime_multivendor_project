import asyncio
from app.database.db import prisma

async def main():
    await prisma.connect()
    products = await prisma.marketingproduct.find_many(include={"creator": True})
    if not products:
        print("No marketing products found in database.")
    for p in products:
        print(f"Product ID: {p.id}, Creator Email: {p.creator.email}")
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
