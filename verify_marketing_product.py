import asyncio
from app.database.db import prisma
from app.marketing_product.services import MarketingProductService
from app.marketing_product.schemas import MarketingProductCreate, ShippingResponsibility

async def verify_marketing_product():
    await prisma.connect()
    
    # 1. Get a customer user
    customer = await prisma.user.find_first(where={"role": "CUSTOMER"})
    if not customer:
        print("No customer found. Please seed the database.")
        await prisma.disconnect()
        return
    
    print(f"Testing with Customer: {customer.email}")

    # 2. Create a marketing product
    product_data = MarketingProductCreate(
        name="Test Marketing Product",
        goodsType="Home appliance",
        location="Tokyo",
        description="A great test product",
        price=500.0,
        publishingFee=0.5,
        shippingResponsibility=ShippingResponsibility.CUSTOMER,
        shippingCharge=5.0
    )
    
    print("Creating marketing product...")
    # Mocking image files as we are testing the service layer structure
    # In a real API call, these would be UploadFile objects
    # For service layer testing, we'll pass empty list or mock URLs if the service handles them
    # Based on my implementation, services.py expects List[UploadFile].
    # I should adjust the script to test the database part directly or mock the upload.
    
    # Let's test the database part directly to ensure schema is correct
    new_product = await prisma.marketingproduct.create(
        data={
            **product_data.model_dump(),
            "creatorId": customer.id,
            "images": ["http://example.com/image.jpg"]
        }
    )
    print(f"Product created with ID: {new_product.id}")

    # 3. Get all marketing products
    all_products = await MarketingProductService.get_all_marketing_products()
    print(f"Total marketing products: {len(all_products)}")
    
    if any(p.id == new_product.id for p in all_products):
        print("SUCCESS: New product found in all products list.")
    else:
        print("FAILURE: New product not found.")

    # 4. Clean up
    await prisma.marketingproduct.delete(where={"id": new_product.id})
    print("Test product deleted.")
    
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_marketing_product())
