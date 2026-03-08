import asyncio
from app.database.db import prisma

async def get_vendor():
    try:
        await prisma.connect()
        v = await prisma.user.find_first(where={'role': 'VENDOR'})
        if v:
            print(f"VENDOR_EMAIL={v.email}")
        else:
            print("NO_VENDOR_FOUND")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(get_vendor())
