from pydantic import BaseModel
from typing import List

class DailyEarning(BaseModel):
    day: str
    earnings: float

class VendorStatsResponse(BaseModel):
    storeName: str
    totalEarnings: float
    earningsOverTime: List[DailyEarning]
    totalPendingOrders: int
    totalProducts: int
    totalFollowers: int
    filterType: str
