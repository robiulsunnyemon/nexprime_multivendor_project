from datetime import datetime, timedelta
from app.database.db import prisma
from app.admin.schemas.admin_dashboard_schemas import AdminDashboardResponse, MonthlyStat
from collections import OrderedDict

class AdminDashboardService:
    @staticmethod
    async def get_dashboard_stats() -> AdminDashboardResponse:
        now = datetime.utcnow()
        # Last 12 months (sliding window)
        start_date = (now.replace(day=1) - timedelta(days=330)).replace(day=1)
        
        # 1. Fetch data from DB
        # Marketing Revenue
        marketing_products = await prisma.marketingproduct.find_many(
            where={"createdAt": {"gte": start_date}}
        )
        
        # Vendor Commission Revenue (from paid orders or completed suborders?)
        # Let's assume all suborders contribute to revenue record when created/completed
        sub_orders = await prisma.suborder.find_many(
            where={"createdAt": {"gte": start_date}}
        )
        
        # User account creations
        users = await prisma.user.find_many(
            where={"createdAt": {"gte": start_date}}
        )
        
        # 2. Process Monthly Stats
        # Initialize last 12 months
        revenue_map = OrderedDict()
        account_map = OrderedDict()
        
        for i in range(12):
            month_date = (start_date + timedelta(days=32 * i)).replace(day=1)
            if month_date > now:
                break
            month_key = month_date.strftime("%b %Y")
            revenue_map[month_key] = 0.0
            account_map[month_key] = 0
            
        # Aggregate Marketing Revenue
        for mp in marketing_products:
            m_key = mp.createdAt.strftime("%b %Y")
            if m_key in revenue_map:
                revenue_map[m_key] += mp.publishingFee
                
        # Aggregate SubOrder Revenue
        for so in sub_orders:
            m_key = so.createdAt.strftime("%b %Y")
            if m_key in revenue_map:
                revenue_map[m_key] += so.commissionAmount

        # Aggregate Account Creations
        for u in users:
            m_key = u.createdAt.strftime("%b %Y")
            if m_key in account_map:
                account_map[m_key] += 1

        # 3. Total Platform Revenue (All Time)
        all_marketing = await prisma.marketingproduct.find_many()
        all_suborders = await prisma.suborder.find_many()
        
        total_revenue = sum(mp.publishingFee for mp in all_marketing) + \
                        sum(so.commissionAmount for so in all_suborders)

        # 4. Static Counts
        pending_kyc = await prisma.kycfile.count(where={"status": "PENDING"})
        active_orders = await prisma.suborder.count(
            where={
                "order": {
                    "status": {"in": ["PENDING", "SHIPPED"]}
                }
            }
        )

        return AdminDashboardResponse(
            totalPlatformRevenue=round(total_revenue, 2),
            revenueStats=[MonthlyStat(month=k, value=round(v, 2)) for k, v in revenue_map.items()],
            accountCreationStats=[MonthlyStat(month=k, value=float(v)) for k, v in account_map.items()],
            pendingKycCount=pending_kyc,
            activeOrdersCount=active_orders
        )
