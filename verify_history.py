import asyncio
from app.database.db import prisma
from app.product.services import ProductService

async def verify_history():
    await prisma.connect()
    print("--- Testing Search History System ---")
    
    # Fetch a real user
    user = await prisma.user.find_first()
    if not user:
        print("No users found. Please seed the database.")
        await prisma.disconnect()
        return
        
    user_id = user.id
    print(f"Testing with User: {user.email} (ID: {user_id})")
    
    # 1. Perform some searches
    queries = ["Rice", "Oil", "Jacket"]
    for q in queries:
        await ProductService.search_products(q, user_id=user_id)
        print(f"Searched for: {q}")
    
    # 2. Get history
    history = await ProductService.get_search_history(user_id=user_id)
    print(f"Retrieved History (Count: {len(history)}):")
    for item in history:
        print(f" - {item.query} (at {item.createdAt})")
    
    # 3. Clear history
    await ProductService.clear_search_history(user_id=user_id)
    print("History cleared.")
    
    # 4. Verify cleared
    history_after = await ProductService.get_search_history(user_id=user_id)
    if len(history_after) == 0:
        print("SUCCESS: Search history system is working correctly.")
    else:
        print("FAILURE: History not cleared.")

    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_history())
