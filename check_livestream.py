import asyncio
from app.database.db import prisma

async def main():
    try:
        await prisma.connect()
        print("Attributes of prisma object:")
        attrs = [a for a in dir(prisma) if not a.startswith("_")]
        print(attrs)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
