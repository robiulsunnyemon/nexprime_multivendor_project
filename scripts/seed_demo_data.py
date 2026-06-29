#!/usr/bin/env python3
"""
Seed Demo Data Script
======================
Run this script to automatically seed the database with:
- 1 Customer User
- 2 Vendor Users (each with a Store)
- 3 Grocery products for Vendor 1
- 3 Wardrobe products for Vendor 2

Usage:
    poetry run python scripts/seed_demo_data.py
Or:
    python scripts/seed_demo_data.py
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.database.db import prisma


def hash_password(password: str) -> str:
    """Hash the given password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def main():
    print("\n" + "=" * 60)
    print("Nexprime - Database Seeding Script")
    print("=" * 60 + "\n")

    print("Connecting to the database...")
    await prisma.connect()

    try:
        # ----------------------------------------------------
        # 1. CREATE CATEGORIES
        # ----------------------------------------------------
        print("\nEnsuring Categories exist...")

        # A. Grocery Main Category
        grocery_main = await prisma.maincategory.find_unique(where={"name": "Grocery"})
        if not grocery_main:
            grocery_main = await prisma.maincategory.create(data={"name": "Grocery"})
            print(f"   Created Main Category: {grocery_main.name} (ID: {grocery_main.id})")
        else:
            print(f"   Main Category 'Grocery' already exists (ID: {grocery_main.id})")

        # Grocery Sub Category
        grocery_sub = await prisma.subcategory.find_first(
            where={"name": "Grocery Items", "mainCategoryId": grocery_main.id}
        )
        if not grocery_sub:
            grocery_sub = await prisma.subcategory.create(
                data={
                    "name": "Grocery Items",
                    "mainCategoryId": grocery_main.id,
                    "image": "https://example.com/grocery_category.jpg"
                }
            )
            print(f"   Created Sub Category: {grocery_sub.name} under Grocery")
        else:
            print(f"   Sub Category 'Grocery Items' already exists (ID: {grocery_sub.id})")

        # B. Wardrobe Main Category
        wardrobe_main = await prisma.maincategory.find_unique(where={"name": "Wardrobe"})
        if not wardrobe_main:
            wardrobe_main = await prisma.maincategory.create(data={"name": "Wardrobe"})
            print(f"   Created Main Category: {wardrobe_main.name} (ID: {wardrobe_main.id})")
        else:
            print(f"   Main Category 'Wardrobe' already exists (ID: {wardrobe_main.id})")

        # Wardrobe Sub Category
        wardrobe_sub = await prisma.subcategory.find_first(
            where={"name": "Wardrobe Items", "mainCategoryId": wardrobe_main.id}
        )
        if not wardrobe_sub:
            wardrobe_sub = await prisma.subcategory.create(
                data={
                    "name": "Wardrobe Items",
                    "mainCategoryId": wardrobe_main.id,
                    "image": "https://example.com/wardrobe_category.jpg"
                }
            )
            print(f"   Created Sub Category: {wardrobe_sub.name} under Wardrobe")
        else:
            print(f"   Sub Category 'Wardrobe Items' already exists (ID: {wardrobe_sub.id})")

        # ----------------------------------------------------
        # 2. CREATE CUSTOMER USER
        # ----------------------------------------------------
        print("\nChecking Customer User...")
        customer_email = "customer@example.com"
        customer = await prisma.user.find_unique(where={"email": customer_email})
        if not customer:
            customer = await prisma.user.create(
                data={
                    "fullname": "Demo Customer",
                    "email": customer_email,
                    "phonenumber": "+8801711111111",
                    "password": hash_password("password123"),
                    "role": "CUSTOMER",
                    "status": "ACTIVE",
                    "is_verified": True,
                    "residentcard_frontside": "customer_placeholder",
                    "residentcard_backside": "customer_placeholder",
                }
            )
            # Create wallet
            await prisma.wallet.create(data={"userId": customer.id, "balance": 10000.0})
            print(f"   Created Customer: {customer.fullname} ({customer.email})")
            print(f"      Wallet initialized with balance: 10000.0")
        else:
            print(f"   Customer '{customer.fullname}' already exists")

        # ----------------------------------------------------
        # 3. CREATE VENDOR 1 & STORE 1 (Grocery)
        # ----------------------------------------------------
        print("\nChecking Vendor 1 & Store 1...")
        vendor1_email = "vendor1@example.com"
        vendor1 = await prisma.user.find_unique(where={"email": vendor1_email})
        if not vendor1:
            vendor1 = await prisma.user.create(
                data={
                    "fullname": "Demo Vendor One",
                    "email": vendor1_email,
                    "phonenumber": "+8801722222222",
                    "password": hash_password("password123"),
                    "role": "VENDOR",
                    "status": "ACTIVE",
                    "is_verified": True,
                    "residentcard_frontside": "vendor1_placeholder",
                    "residentcard_backside": "vendor1_placeholder",
                }
            )
            await prisma.wallet.create(data={"userId": vendor1.id, "balance": 0.0})
            print(f"   Created Vendor 1: {vendor1.fullname} ({vendor1.email})")
        else:
            print(f"   Vendor 1 '{vendor1.fullname}' already exists")

        store1 = await prisma.store.find_unique(where={"vendorId": vendor1.id})
        if not store1:
            store1 = await prisma.store.create(
                data={
                    "name": "Fresh Grocery Hub",
                    "bio": "All fresh organic groceries in one place.",
                    "address": "123 Green Road, Dhaka, Bangladesh",
                    "photo": "https://example.com/grocery_store.jpg",
                    "vendorId": vendor1.id
                }
            )
            print(f"   Created Store 1: {store1.name} (ID: {store1.id})")
        else:
            print(f"   Store 1 '{store1.name}' already exists (ID: {store1.id})")

        # ----------------------------------------------------
        # 4. CREATE VENDOR 2 & STORE 2 (Wardrobe)
        # ----------------------------------------------------
        print("\nChecking Vendor 2 & Store 2...")
        vendor2_email = "vendor2@example.com"
        vendor2 = await prisma.user.find_unique(where={"email": vendor2_email})
        if not vendor2:
            vendor2 = await prisma.user.create(
                data={
                    "fullname": "Demo Vendor Two",
                    "email": vendor2_email,
                    "phonenumber": "+8801733333333",
                    "password": hash_password("password123"),
                    "role": "VENDOR",
                    "status": "ACTIVE",
                    "is_verified": True,
                    "residentcard_frontside": "vendor2_placeholder",
                    "residentcard_backside": "vendor2_placeholder",
                }
            )
            await prisma.wallet.create(data={"userId": vendor2.id, "balance": 0.0})
            print(f"   Created Vendor 2: {vendor2.fullname} ({vendor2.email})")
        else:
            print(f"   Vendor 2 '{vendor2.fullname}' already exists")

        store2 = await prisma.store.find_unique(where={"vendorId": vendor2.id})
        if not store2:
            store2 = await prisma.store.create(
                data={
                    "name": "Elegant Wardrobe",
                    "bio": "Find your perfect style and fit.",
                    "address": "456 Fashion Ave, Chittagong, Bangladesh",
                    "photo": "https://example.com/wardrobe_store.jpg",
                    "vendorId": vendor2.id
                }
            )
            print(f"   Created Store 2: {store2.name} (ID: {store2.id})")
        else:
            print(f"   Store 2 '{store2.name}' already exists (ID: {store2.id})")

        # ----------------------------------------------------
        # 5. CREATE PRODUCTS FOR STORE 1 (Grocery)
        # ----------------------------------------------------
        print(f"\nAdding Products for {store1.name}...")
        grocery_products = [
            {
                "name": "Fresh Red Apples",
                "description": "Juicy organic premium red apples imported from local farms.",
                "basePrice": 200.0,
                "stockUnits": 100,
                "size": ["FREE_SIZE"],
                "colors": ["Red"],
                "isDiscountSale": False,
                "salePrice": 200.0,
                "discountPercentage": 0.0,
                "shippingResponsibility": "CUSTOMER",
                "shippingCharge": 50.0,
                "total_payable_amount": 250.0,
                "images": ["https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6"]
            },
            {
                "name": "Organic Spinach Bunch",
                "description": "Freshly harvested organic green spinach rich in vitamins.",
                "basePrice": 40.0,
                "stockUnits": 150,
                "size": ["FREE_SIZE"],
                "colors": ["Green"],
                "isDiscountSale": True,
                "salePrice": 30.0,
                "discountPercentage": 25.0,
                "shippingResponsibility": "VENDOR",
                "shippingCharge": 0.0,
                "total_payable_amount": 30.0,
                "images": ["https://images.unsplash.com/photo-1576045057995-568f588f82fb"]
            },
            {
                "name": "Fresh Milk 1L",
                "description": "Pure, pasteurized cow milk from a premium local dairy farm.",
                "basePrice": 90.0,
                "stockUnits": 80,
                "size": ["FREE_SIZE"],
                "colors": ["White"],
                "isDiscountSale": False,
                "salePrice": 90.0,
                "discountPercentage": 0.0,
                "shippingResponsibility": "CUSTOMER",
                "shippingCharge": 20.0,
                "total_payable_amount": 110.0,
                "images": ["https://images.unsplash.com/photo-1550583724-b2692b85b150"]
            }
        ]

        for p in grocery_products:
            # Check if product exists in this store
            existing_p = await prisma.product.find_first(
                where={"name": p["name"], "storeId": store1.id}
            )
            if not existing_p:
                prod = await prisma.product.create(
                    data={
                        "name": p["name"],
                        "description": p["description"],
                        "basePrice": p["basePrice"],
                        "stockUnits": p["stockUnits"],
                        "size": p["size"],
                        "colors": p["colors"],
                        "isDiscountSale": p["isDiscountSale"],
                        "salePrice": p["salePrice"],
                        "discountPercentage": p["discountPercentage"],
                        "shippingResponsibility": p["shippingResponsibility"],
                        "shippingCharge": p["shippingCharge"],
                        "total_payable_amount": p["total_payable_amount"],
                        "images": p["images"],
                        "storeId": store1.id,
                        "categories": {
                            "connect": [{"id": grocery_sub.id}]
                        }
                    }
                )
                print(f"   Created Product: {prod.name} (ID: {prod.id})")
            else:
                print(f"   Product '{p['name']}' already exists in Store 1")

        # ----------------------------------------------------
        # 6. CREATE PRODUCTS FOR STORE 2 (Wardrobe)
        # ----------------------------------------------------
        print(f"\nAdding Products for {store2.name}...")
        wardrobe_products = [
            {
                "name": "Slim Fit Blue Jeans",
                "description": "Comfortable, stretchable, and durable denim jeans for everyday wear.",
                "basePrice": 1200.0,
                "stockUnits": 50,
                "size": ["S", "M", "L", "XL"],
                "colors": ["Blue"],
                "isDiscountSale": True,
                "salePrice": 999.0,
                "discountPercentage": 16.75,
                "shippingResponsibility": "CUSTOMER",
                "shippingCharge": 60.0,
                "total_payable_amount": 1059.0,
                "images": ["https://images.unsplash.com/photo-1542272604-787c3835535d"]
            },
            {
                "name": "Classic Cotton T-Shirt",
                "description": "100% premium combed cotton t-shirt with active cooling technology.",
                "basePrice": 500.0,
                "stockUnits": 120,
                "size": ["S", "M", "L", "XL", "XXL"],
                "colors": ["Black", "White", "Grey"],
                "isDiscountSale": False,
                "salePrice": 500.0,
                "discountPercentage": 0.0,
                "shippingResponsibility": "VENDOR",
                "shippingCharge": 0.0,
                "total_payable_amount": 500.0,
                "images": ["https://images.unsplash.com/photo-1521572267360-ee0c2909d518"]
            },
            {
                "name": "Casual Summer Dress",
                "description": "Lightweight, stylish floral print cotton dress ideal for summer outings.",
                "basePrice": 1800.0,
                "stockUnits": 30,
                "size": ["M", "L"],
                "colors": ["Yellow", "Blue"],
                "isDiscountSale": True,
                "salePrice": 1500.0,
                "discountPercentage": 16.67,
                "shippingResponsibility": "CUSTOMER",
                "shippingCharge": 80.0,
                "total_payable_amount": 1580.0,
                "images": ["https://images.unsplash.com/photo-1572804013309-59a88b7e92f1"]
            }
        ]

        for p in wardrobe_products:
            # Check if product exists in this store
            existing_p = await prisma.product.find_first(
                where={"name": p["name"], "storeId": store2.id}
            )
            if not existing_p:
                prod = await prisma.product.create(
                    data={
                        "name": p["name"],
                        "description": p["description"],
                        "basePrice": p["basePrice"],
                        "stockUnits": p["stockUnits"],
                        "size": p["size"],
                        "colors": p["colors"],
                        "isDiscountSale": p["isDiscountSale"],
                        "salePrice": p["salePrice"],
                        "discountPercentage": p["discountPercentage"],
                        "shippingResponsibility": p["shippingResponsibility"],
                        "shippingCharge": p["shippingCharge"],
                        "total_payable_amount": p["total_payable_amount"],
                        "images": p["images"],
                        "storeId": store2.id,
                        "categories": {
                            "connect": [{"id": wardrobe_sub.id}]
                        }
                    }
                )
                print(f"   Created Product: {prod.name} (ID: {prod.id})")
            else:
                print(f"   Product '{p['name']}' already exists in Store 2")

        print("\n" + "=" * 60)
        print("Database seeded successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError seeding database: {e}\n")
        raise
    finally:
        await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
