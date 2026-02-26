import asyncio
import bcrypt
import random
from prisma import Prisma

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def main():
    prisma = Prisma()
    await prisma.connect()

    print("--- Starting Comprehensive Seed ---")

    # 1. Cleanup existing dynamic data (optional but recommended for clean testing)
    print("Cleaning up old data...")
    await prisma.product.delete_many()
    await prisma.subcategory.delete_many()
    await prisma.store.delete_many()
    
    # Keep the Admin user if it exists, but we can clean others
    # await prisma.user.delete_many(where={"role": {"not": "ADMIN"}})

    # 2. Map Main Categories
    print("Mapping Main Categories...")
    
    # categories from seed_categories.py + original ones
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
        "grocery country": ["Bangladesh", "Pakistan", "Nepal", "Vietnam"],
        "wardrobe country": ["Hoodie", "Sweatsuits", "T-shirt", "Pant", "Jacket"]
    }
    
    created_sub_cats = []
    for main_name, subs in sub_cats_data.items():
        main_id = main_cat_map[main_name]
        for sub_name in subs:
            sc = await prisma.subcategory.create(data={
                "name": sub_name,
                "mainCategoryId": main_id,
                "image": f"https://picsum.photos/seed/{sub_name}/200"
            })
            created_sub_cats.append(sc)
            print(f"Created SubCategory: {sub_name} under {main_name}")

    # 4. Create Users (1 Admin, 10 Vendors, 10 Customers)
    print("Creating Users & Stores...")
    
    # Create Admin
    admin_email = "admin@nexprime.com"
    existing_admin = await prisma.user.find_unique(where={"email": admin_email})
    if not existing_admin:
        await prisma.user.create(data={
            "fullname": "Head Admin",
            "email": admin_email,
            "phonenumber": "01700000000",
            "password": hash_password("admin123"),
            "role": "ADMIN",
            "status": "ACTIVE",
            "is_verified": True,
            "residentcard_frontside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
            "residentcard_backside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
        })
        print(f"Created Admin: {admin_email}")
    else:
        print(f"Admin already exists: {admin_email}")

    vendors = []
    for i in range(1, 11):
        email = f"vendor{i}@nexprime.com"
        existing = await prisma.user.find_unique(where={"email": email})
        if not existing:
            user = await prisma.user.create(data={
                "fullname": f"Vendor {i}",
                "email": email,
                "phonenumber": f"018000000{i:02d}",
                "password": hash_password("password123"),
                "role": "VENDOR",
                "status": "ACTIVE",
                "is_verified": True,
                "residentcard_frontside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
                "residentcard_backside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
            })
            print(f"Created Vendor: {email}")
        else:
            user = existing
        
        # Create Store for each vendor
        store = await prisma.store.find_unique(where={"vendorId": user.id})
        if not store:
            store = await prisma.store.create(data={
                "name": f"Shop {i} Emporium",
                "bio": f"Quality products from Shop {i}",
                "address": f"Address {i}, Marketplace",
                "photo": f"https://picsum.photos/seed/shop{i}/400",
                "vendorId": user.id
            })
            print(f"Created Store for Vendor {i}")
        vendors.append(store)

    for i in range(1, 11):
        email = f"customer{i}@nexprime.com"
        existing = await prisma.user.find_unique(where={"email": email})
        if not existing:
            await prisma.user.create(data={
                "fullname": f"Customer {i}",
                "email": email,
                "phonenumber": f"019000000{i:02d}",
                "password": hash_password("password123"),
                "role": "CUSTOMER",
                "status": "ACTIVE",
                "is_verified": True,
                "residentcard_frontside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
                "residentcard_backside": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
            })
            print(f"Created Customer: {email}")

    # 5. Create 20 Products
    print("Creating 20 Products...")
    sizes = ["S", "M", "L", "XL", "2XL"]
    colors = ["Red", "Blue", "Green", "Black", "White"]
    
    for i in range(1, 21):
        store = random.choice(vendors)
        # Link to 1-3 random subcategories
        num_subs = random.randint(1, 3)
        subs_to_link = random.sample(created_sub_cats, num_subs)
        
        price = round(random.uniform(10.0, 500.0), 2)
        
        await prisma.product.create(data={
            "name": f"Product Item {i}",
            "description": f"This is an amazing description for product item {i}. Very high quality.",
            "basePrice": price,
            "stockUnits": random.randint(10, 100),
            "size": random.choice(sizes),
            "colors": random.choice(colors),
            "isOnSale": random.choice([True, False]),
            "salePrice": price * 0.8,
            "discountPercentage": 20.0,
            "shippingCharge": random.randint(0, 50),
            "images": [f"https://picsum.photos/seed/prod{i}/500", f"https://picsum.photos/seed/prod{i}alt/500"],
            "storeId": store.id,
            "categories": {
                "connect": [{"id": sc.id} for sc in subs_to_link]
            }
        })
        print(f"Created Product {i} in Store {store.id}")

    # 6. Create KYC Files for Vendors
    print("Creating KYC Files for Vendors...")
    vendors_users = await prisma.user.find_many(where={"role": "VENDOR"})
    for v_user in vendors_users:
        existing_kyc = await prisma.kycfile.find_first(where={"vendorId": v_user.id})
        if not existing_kyc:
            await prisma.kycfile.create(data={
                "title": f"KYC for {v_user.fullname}",
                "fileUrl": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
                "status": "ACTIVE",
                "vendorId": v_user.id
            })
            print(f"Created KYC for Vendor: {v_user.email}")

    # 7. Create Banners
    print("Creating Banners...")
    await prisma.banner.delete_many() # Refresh banners
    for i in range(1, 4):
        await prisma.banner.create(data={
            "imageUrl": f"https://picsum.photos/seed/banner{i}/1200/400",
            "link": f"https://example.com/promo{i}"
        })
        print(f"Created Banner {i}")

    print("--- Seeding Completed Successfully ---")
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
