import asyncio
from app.database.db import prisma

async def debug():
    await prisma.connect()
    try:
        # Find the test customer
        user = await prisma.user.find_unique(
            where={"email": "customer_test@nexprime.com"},
            include={"followedStores": True}
        )
        print(f"User: {user.email if user else 'Not found'}")
        if user:
            vendor_ids = [store.vendorId for store in user.followedStores]
            print(f"Vendor IDs: {vendor_ids}")
            
            # This is where it likely fails
            streams = await prisma.livestream.find_many(
                where={
                    "isActive": True,
                    "streamerId": {"in": vendor_ids}
                }
            )
            print(f"Streams found: {len(streams)}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(debug())
