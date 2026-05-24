#!/usr/bin/env python3
"""
Admin Account Creation Script
==============================
Run this script to interactively create an Admin account.

Usage:
    python scripts/create_admin.py

Or from the project root using Poetry:
    poetry run python scripts/create_admin.py
"""

import asyncio
import sys
import os
import getpass

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


def print_banner():
    print("\n" + "=" * 55)
    print("   🛡️  Nexprime - Admin Account Creation Script")
    print("=" * 55 + "\n")


def get_input(prompt: str, required: bool = True) -> str:
    """Prompt for input and re-ask if empty."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        if not required:
            return ""
        print("   ⚠️  This field is required. Please try again.\n")


def get_password() -> str:
    """Securely prompt for password (input will not be visible on screen)."""
    while True:
        password = getpass.getpass("   🔑 Password (hidden): ").strip()
        if len(password) < 6:
            print("   ⚠️  Password must be at least 6 characters long.\n")
            continue
        confirm = getpass.getpass("   🔑 Confirm Password: ").strip()
        if password != confirm:
            print("   ❌ Passwords do not match. Please try again.\n")
            continue
        return password


async def create_admin():
    print_banner()

    print("📋 Please provide the Admin account details:\n")

    # Collect input
    fullname    = get_input("   👤 Full Name: ")
    email       = get_input("   📧 Email: ")
    phonenumber = get_input("   📞 Phone Number: ")
    password    = get_password()

    print("\n" + "-" * 55)
    print("📝 Account Details Summary:")
    print(f"   Name         : {fullname}")
    print(f"   Email        : {email}")
    print(f"   Phone Number : {phonenumber}")
    print(f"   Role         : ADMIN")
    print(f"   Status       : ACTIVE")
    print(f"   Verified     : Yes")
    print("-" * 55 + "\n")

    confirm = input("✅ Create Admin account with the above details? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("\n❌ Operation cancelled.\n")
        return

    print("\n⏳ Connecting to the database...\n")

    await prisma.connect()

    try:
        # Check if email or phone number already exists
        existing = await prisma.user.find_first(
            where={"OR": [{"email": email}, {"phonenumber": phonenumber}]}
        )
        if existing:
            print(f"❌ Error: An account with this email or phone number already exists.")
            print(f"   Existing account: {existing.email} | Role: {existing.role}\n")
            return

        # Create the Admin account
        admin_user = await prisma.user.create(
            data={
                "fullname":               fullname,
                "email":                  email,
                "phonenumber":            phonenumber,
                "password":               hash_password(password),
                "role":                   "ADMIN",
                "status":                 "ACTIVE",
                "is_verified":            True,
                # Placeholder values for admin (no resident card required)
                "residentcard_frontside": "admin_placeholder",
                "residentcard_backside":  "admin_placeholder",
            }
        )

        print("\n" + "=" * 55)
        print("🎉 Admin account created successfully!")
        print("=" * 55)
        print(f"   🆔 User ID     : {admin_user.id}")
        print(f"   👤 Name        : {admin_user.fullname}")
        print(f"   📧 Email       : {admin_user.email}")
        print(f"   📞 Phone       : {admin_user.phonenumber}")
        print(f"   🛡️  Role        : {admin_user.role}")
        print(f"   ✅ Status      : {admin_user.status}")
        print(f"   🗓️  Created At  : {admin_user.createdAt}")
        print("=" * 55 + "\n")

    except Exception as e:
        print(f"\n❌ Failed to create account: {e}\n")
        raise
    finally:
        await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(create_admin())
