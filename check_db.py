import asyncio
from prisma import Prisma

async def main():
    prisma = Prisma()
    await prisma.connect()
    
    # 1. Check SystemSetting
    s = await prisma.systemsetting.find_unique(where={"id": 1})
    print(f"SystemSetting table (id=1): {s}")
    
    # 2. Check MarketingProduct
    p = await prisma.marketingproduct.count()
    print(f"Total MarketingProducts: {p}")
    
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
