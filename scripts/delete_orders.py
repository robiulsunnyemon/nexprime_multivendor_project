import asyncio
from prisma import Prisma


async def delete_all_orders():
    # Initialize Prisma Client
    prisma = Prisma()
    
    try:
        # Connect to the database
        print("🔄 Establishing database connection...")
        await prisma.connect()

        # 1. (Optional) Get the count first to see how many orders exist
        order_count = await prisma.order.count()
        print(f"📊 Total orders in database: {order_count}")

        if order_count == 0:
            print("💡 No orders found to delete.")
            return

        # 2. Main query to delete all orders
        # Due to onDelete: Cascade, subOrders, orderItems, and ratings will be deleted automatically
        print("🗑️ Starting deletion of all orders...")
        delete_result = await prisma.order.delete_many()
        
        print(f"✅ Successfully deleted {delete_result} records from the Order table along with their related relations.")

    except Exception as e:
        print(f"❌ An error occurred while deleting orders: {e}")
        
    finally:
        # Disconnect from the database
        if prisma.is_connected():
            await prisma.disconnect()
            print("🔌 Database connection successfully closed.")


# Use asyncio to run the async function
if __name__ == "__main__":
    asyncio.run(delete_all_orders())