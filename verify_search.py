import asyncio
from app.database.db import prisma
from app.product.services import ProductService

async def verify_search():
    await prisma.connect()
    print("--- Testing Global Product Search ---")
    
    test_queries = ["Rice", "High Quality", "XL", "Emporium", "Bangladesh"]
    
    for q in test_queries:
        results = await ProductService.search_products(q)
        print(f"Search Query: '{q}' -> Found {len(results)} results")
        if len(results) > 0:
            # Print first result details to verify it matches
            top = results[0]
            print(f"  - First Result: {top.name} | Store: {top.store.name} | Categories: {[c.name for c in top.categories]}")
        else:
            print(f"  - No results for '{q}'")
    
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_search())
