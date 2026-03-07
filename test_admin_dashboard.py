import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.database.db import prisma
from app.admin.services.admin_dashboard_service import AdminDashboardService

async def main():
    print("--- Testing Admin Dashboard Service ---")
    await prisma.connect()
    try:
        stats = await AdminDashboardService.get_dashboard_stats()
        
        print(f"\n0. Total Platform Revenue (All Time): ${stats.totalPlatformRevenue}")

        print("\n1. Revenue Stats (Sliding 12 Months):")
        for stat in stats.revenueStats:
            print(f"  - {stat.month}: ${stat.value}")
            
        print("\n2. Account Creation Stats:")
        for stat in stats.accountCreationStats:
            print(f"  - {stat.month}: {stat.value} users")
            
        print(f"\n3. Pending KYC Count: {stats.pendingKycCount}")
        print(f"4. Active Orders Count: {stats.activeOrdersCount}")
        
        # Verify basic properties
        assert len(stats.revenueStats) == 12, "Should return exactly 12 months of revenue stats"
        assert len(stats.accountCreationStats) == 12, "Should return exactly 12 months of account stats"
        assert stats.pendingKycCount >= 0, "Counter should be non-negative"
        
        print("\nAll Dashboard Verifications Passed!")

    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
