from fastapi import APIRouter, Depends
from app.core.current_user import get_admin
from app.admin.schemas.admin_dashboard_schemas import AdminDashboardResponse
from app.admin.services.admin_dashboard_service import AdminDashboardService

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])

@router.get("/stats", response_model=AdminDashboardResponse)
async def get_dashboard_stats(current_admin = Depends(get_admin)):
    """
    Get core statistics for the admin dashboard:
    - Yearly revenue stats (sliding 12 months)
    - Yearly account creation stats
    - Pending KYC count
    - Active global orders count
    """
    return await AdminDashboardService.get_dashboard_stats()
