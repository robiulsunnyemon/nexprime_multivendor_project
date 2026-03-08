import asyncio
import bcrypt
import random
import os
from dotenv import load_dotenv
from prisma import Prisma

load_dotenv()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def main():
    prisma = Prisma()
    await prisma.connect()

    print("--- Starting Comprehensive Seed ---")

    # # 1. Cleanup ALL existing data for a fresh start
    # print("Cleaning up all existing data...")
    # # Delete in order of dependencies
    # await prisma.rating.delete_many()
    # await prisma.orderitem.delete_many()
    # await prisma.suborder.delete_many()
    # await prisma.order.delete_many()
    # await prisma.deliveryaddress.delete_many()
    # await prisma.cartitem.delete_many()
    # await prisma.searchhistory.delete_many()
    # await prisma.refreshtoken.delete_many()
    # await prisma.otp.delete_many()
    # await prisma.marketingproduct.delete_many()
    # await prisma.kycfile.delete_many()
    # await prisma.product.delete_many()
    # await prisma.store.delete_many()
    # await prisma.subcategory.delete_many()
    # await prisma.user.delete_many()
    # await prisma.maincategory.delete_many()
    # await prisma.banner.delete_many()
    # await prisma.systemsetting.delete_many()
    # await prisma.marketingproductsetting.delete_many()
    # print("Cleanup completed.")

    # 2. Map Main Categories
    print("Mapping Main Categories...")
    required_main_cats = [
        "Grocery",
        "Wardrobe",
        "Marketplace Management",
        "Grocery Country",
        "Wardrobe Country"
    ]
    
    main_cat_map = {}
    for cat_name in required_main_cats:
        cat = await prisma.maincategory.upsert(
            where={"name": cat_name},
            data={
                "create": {"name": cat_name},
                "update": {}
            }
        )
        main_cat_map[cat_name.lower()] = cat.id
        print(f"Upserted MainCategory: {cat_name}")

    # 3. Create SubCategories
    print("Creating SubCategories...")
    sub_cats_data = {
        "grocery": ["Rice", "Oil", "Fish Sauce", "Milk", "Soy Sauce", "Chili Sauce"],
        "wardrobe": ["Hoodie", "Sweatsuits", "T-shirt", "Pant", "Jacket"],
        "grocery country": ["Bangladesh", "Pakistan", "Nepal", "Vietnam"],
        "wardrobe country": ["Bangladesh", "Pakistan", "Nepal", "Vietnam"]
    }
    
    created_sub_cats_map = {} 
    for main_name, subs in sub_cats_data.items():
        main_id = main_cat_map[main_name]
        created_sub_cats_map[main_name] = []
        for sub_name in subs:
            sc = await prisma.subcategory.create(data={
                "name": sub_name,
                "mainCategoryId": main_id,
                "image": f"https://picsum.photos/seed/{sub_name}/200"
            })
            created_sub_cats_map[main_name].append(sc)
            print(f"Created SubCategory: {sub_name} under {main_name}")

    # 4. Create Users (1 Admin, 10 Vendors, 10 Customers)
    print("Creating Users & Stores...")
    
    # Create Admin
    admin_email = "admin@nexprime.com"
    await prisma.user.create(data={
        "fullname": "Head Admin",
        "email": admin_email,
        "phonenumber": "01700000000",
        "password": hash_password("admin123"),
        "role": "ADMIN",
        "status": "ACTIVE",
        "is_verified": True,
        "profileImageUrl": "https://i.pravatar.cc/150?u=admin",
        "coverImageUrl": "https://picsum.photos/seed/admincover/800/300",
        "residentcard_frontside": "https://picsum.photos/seed/adminfront/400",
        "residentcard_backside": "https://picsum.photos/seed/adminback/400",
    })
    print(f"Created Admin: {admin_email}")

    vendor_stores = []
    for i in range(1, 11):
        email = f"vendor{i}@nexprime.com"
        user = await prisma.user.create(data={
            "fullname": f"Vendor {i}",
            "email": email,
            "phonenumber": f"018000000{i:02d}",
            "password": hash_password("password123"),
            "role": "VENDOR",
            "status": "ACTIVE",
            "is_verified": True,
            "profileImageUrl": f"https://i.pravatar.cc/150?u=vendor{i}",
            "coverImageUrl": f"https://picsum.photos/seed/vcover{i}/800/300",
            "residentcard_frontside": "https://picsum.photos/seed/vfront{i}/400",
            "residentcard_backside": "https://picsum.photos/seed/vback{i}/400",
        })
        
        store = await prisma.store.create(data={
            "name": f"Shop {i} Emporium",
            "bio": f"Quality products from Shop {i}",
            "address": f"Address {i}, Marketplace",
            "photo": f"https://picsum.photos/seed/shop{i}/400",
            "vendorId": user.id
        })
        vendor_stores.append(store)
        print(f"Created Vendor & Store: {email}")

    customers = []
    for i in range(1, 11):
        email = f"customer{i}@nexprime.com"
        user = await prisma.user.create(data={
            "fullname": f"Customer {i}",
            "email": email,
            "phonenumber": f"019000000{i:02d}",
            "password": hash_password("password123"),
            "role": "CUSTOMER",
            "status": "ACTIVE",
            "is_verified": True,
            "profileImageUrl": f"https://i.pravatar.cc/150?u=customer{i}",
            "coverImageUrl": f"https://picsum.photos/seed/ccover{i}/800/300",
            "residentcard_frontside": "https://picsum.photos/seed/cfront{i}/400",
            "residentcard_backside": "https://picsum.photos/seed/cback{i}/400",
        })
        customers.append(user)
        
        # # 4a. Create Delivery Address for each customer
        # addr = await prisma.deliveryaddress.create(data={
        #     "fullName": user.fullname,
        #     "phoneNumber": user.phonenumber,
        #     "postcode": f"100{i}",
        #     "fullAddress": f"House {i*10}, Road {i}, Dhaka, Bangladesh",
        #     "buildingNameRoomNumber": f"Building {i}, Flat {i}A",
        #     "userId": user.id
        # })
        # print(f"Created Customer & Address: {email}")

    # 5. Create 30 Products
    print("Creating 30 Products...")
    sizes = ["S", "M", "L", "XL", "XXL", "FREE_SIZE"]
    colors_pool = ["Red", "Blue", "Green", "Black", "White", "Yellow"]
    
    all_products = []
    for i in range(1, 31):
        store = random.choice(vendor_stores)
        group = random.choice(["grocery", "wardrobe"])
        main_subs = created_sub_cats_map[group]
        country_subs = created_sub_cats_map[f"{group} country"]
        
        subs_to_link = [random.choice(main_subs), random.choice(country_subs)]
        
        base_price = round(random.uniform(10.0, 500.0), 2)
        is_discount_sale = (i % 3 == 0)
        sale_price = round(base_price * 0.8, 2) if is_discount_sale else base_price
        discount_percentage = 20.0 if is_discount_sale else 0.0

        prod = await prisma.product.create(data={
            "name": f"Product Item {i}",
            "description": f"Quality {group} item from {store.name}.",
            "basePrice": base_price,
            "stockUnits": random.randint(50, 200),
            "size": random.sample(sizes, k=random.randint(1, 3)),
            "colors": random.sample(colors_pool, k=random.randint(1, 3)),
            "isDiscountSale": is_discount_sale,
            "salePrice": sale_price,
            "discountPercentage": discount_percentage,
            "shippingResponsibility": random.choice(["CUSTOMER", "VENDOR"]),
            "shippingCharge": random.randint(0, 50),
            "total_payable_amount": sale_price + 20, # dummy total
            "images": [f"https://picsum.photos/seed/prod{i}/500"],
            "storeId": store.id,
            "categories": {"connect": [{"id": sc.id} for sc in subs_to_link]}
        })
        all_products.append(prod)
        print(f"Created Product {i}")

    # # 6. Create Example Orders
    # print("Creating Example Orders...")
    # for i in range(1, 6):
    #     customer = random.choice(customers)
    #     addr = await prisma.deliveryaddress.find_first(where={"userId": customer.id})
        
    #     # Pick 3 random products from different stores
    #     order_prods = random.sample(all_products, 3)
    #     total_amount = sum(p.salePrice for p in order_prods)
        
    #     # Create Main Order
    #     order = await prisma.order.create(data={
    #         "userId": customer.id,
    #         "deliveryAddressId": addr.id,
    #         "totalAmount": total_amount,
    #         "isPaid": i % 2 == 0,
    #         "status": "PENDING"
    #     })
        
    #     # Group by store for SubOrders
    #     store_groups = {}
    #     for p in order_prods:
    #         if p.storeId not in store_groups:
    #             store_groups[p.storeId] = []
    #         store_groups[p.storeId].append(p)
            
    #     for store_id, prods in store_groups.items():
    #         sub_total = sum(p.salePrice for p in prods)
    #         sub_order = await prisma.suborder.create(data={
    #             "orderId": order.id,
    #             "storeId": store_id,
    #             "subTotal": sub_total,
    #             "isFulfield": False,
    #             "isComplete": False
    #         })
            
    #         for p in prods:
    #             await prisma.orderitem.create(data={
    #                 "subOrderId": sub_order.id,
    #                 "productId": p.id,
    #                 "quantity": 1,
    #                 "price": p.salePrice
    #             })
    #     print(f"Created Order {i} for {customer.email}")

    # 7. Create KYC Files & Banners
    print("Finalizing Seeding...")
    vendors_users = await prisma.user.find_many(where={"role": "VENDOR"})
    for v_user in vendors_users:
        await prisma.kycfile.create(data={
            "title": f"KYC for {v_user.fullname}",
            "fileUrl": "https://picsum.photos/seed/kyc/400",
            "status": "ACTIVE",
            "vendorId": v_user.id
        })
    
    for i in range(1, 4):
        await prisma.banner.create(data={
            "imageUrl": f"https://picsum.photos/seed/banner{i}/1200/400",
            "link": "https://nexprime.com"
        })

    print("--- Seeding Completed Successfully ---")
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
