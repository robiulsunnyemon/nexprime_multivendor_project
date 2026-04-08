import asyncio
from app.database.db import prisma
from app.live.services import LiveStreamService

async def test_followed_live():
    print("Connecting to database...")
    await prisma.connect()
    
    try:
        # 1. Setup Test Data
        email_customer = "test_customer_followed_live@example.com"
        email_vendor = "test_vendor_followed_live@example.com"
        
        # Cleanup
        await prisma.livestream.delete_many(where={"title": "Verification Stream"})
        await prisma.store.delete_many(where={"name": "Verification Store"})
        await prisma.user.delete_many(where={"email": {"in": [email_customer, email_vendor]}})
        
        print("Creating test users...")
        vendor = await prisma.user.create(
            data={
                "fullname": "Verification Vendor",
                "email": email_vendor,
                "phonenumber": "0999999991",
                "password": "hashed_password",
                "role": "VENDOR",
                "status": "ACTIVE",
                "is_verified": True,
                "residentcard_frontside": "url",
                "residentcard_backside": "url",
                "store": {
                    "create": {
                        "name": "Verification Store",
                        "bio": "Bio",
                        "address": "Address",
                        "photo": "photo_url"
                    }
                }
            }
        )
        
        customer = await prisma.user.create(
            data={
                "fullname": "Verification Customer",
                "email": email_customer,
                "phonenumber": "0999999992",
                "password": "hashed_password",
                "role": "CUSTOMER",
                "status": "ACTIVE",
                "is_verified": True,
                "residentcard_frontside": "url",
                "residentcard_backside": "url"
            }
        )
        
        store = await prisma.store.find_unique(where={"vendorId": vendor.id})
        
        # 2. Make Customer follow Vendor's Store
        print(f"Customer {customer.id} following Store {store.id}...")
        await prisma.user.update(
            where={"id": customer.id},
            data={"followedStores": {"connect": [{"id": store.id}]}}
        )
        
        # 3. Vendor starts a Live Stream
        print(f"Vendor {vendor.id} starting a live stream...")
        stream = await prisma.livestream.create(
            data={
                "title": "Verification Stream",
                "thumbnail": "thumb_url",
                "streamerId": vendor.id,
                "isActive": True
            }
        )
        
        # 4. Call Service and Verify
        print("Calling LiveStreamService.get_followed_active_streams...")
        result = await LiveStreamService.get_followed_active_streams(customer.id)
        
        # 5. Assertions
        print("\n--- Verification Results ---")
        print(f"Total Streams found: {result['totalActiveStreams']}")
        
        if result['totalActiveStreams'] > 0:
            found_stream = result['streams'][0]
            print(f"Stream Title: {found_stream['title']}")
            print(f"Vendor Name: {found_stream['vendorName']}")
            print(f"Store Name: {found_stream['storeName']}")
            
            assert found_stream['title'] == "Verification Stream"
            assert found_stream['vendorName'] == "Verification Vendor"
            assert found_stream['storeName'] == "Verification Store"
            print("\nSUCCESS: Enriched followed streams data is correct!")
        else:
            print("\nFAILURE: No streams found for followed vendor.")
            
    except Exception as e:
        print(f"\nERROR during verification: {e}")
    finally:
        print("\nCleaning up...")
        # Optional cleanup
        await prisma.livestream.delete_many(where={"id": stream.id})
        await prisma.user.delete_many(where={"id": {"in": [vendor.id, customer.id]}})
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(test_followed_live())
