import asyncio
from prisma import Prisma

async def main():
    prisma = Prisma()
    await prisma.connect()

    print("--- Starting Database Reset (Deleting All Data) ---")

    # Order of deletion is important to avoid foreign key constraint errors
    try:
        # 1. Transactions and Interactions
        print("Cleaning up transactions and ratings...")
        await prisma.rating.delete_many()
        await prisma.orderitem.delete_many()
        await prisma.suborder.delete_many()
        await prisma.order.delete_many()
        
        # 2. User specific data
        print("Cleaning up user data (Cart, OTP, KYC)...")
        await prisma.deliveryaddress.delete_many()
        await prisma.cartitem.delete_many()
        await prisma.searchhistory.delete_many()
        await prisma.refreshtoken.delete_many()
        await prisma.otp.delete_many()
        await prisma.kycfile.delete_many()
        
        # 3. Core Business Entities
        print("Cleaning up products and stores...")
        await prisma.marketingproduct.delete_many()
        await prisma.product.delete_many()
        await prisma.store.delete_many()
        
        # 4. Master Data
        print("Cleaning up categories and users...")
        await prisma.subcategory.delete_many()
        await prisma.maincategory.delete_many()
        await prisma.user.delete_many()
        
        # 5. System Data
        print("Cleaning up banners and settings...")
        await prisma.banner.delete_many()
        await prisma.systemsetting.delete_many()
        await prisma.marketingproductsetting.delete_many()
        
        print("--- Database Reset Completed Successfully ---")
    except Exception as e:
        print(f"Error during reset: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
