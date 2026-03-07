from pydantic import BaseModel
from typing import List

class MonthlyStat(BaseModel):
    month: str
    value: float

class AdminDashboardResponse(BaseModel):
    totalPlatformRevenue: float
    revenueStats: List[MonthlyStat]
    accountCreationStats: List[MonthlyStat]
    pendingKycCount: int
    activeOrdersCount: int
