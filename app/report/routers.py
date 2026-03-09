from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List
from app.core.current_user import get_current_user, get_admin
from app.report.schemas import (
    MarketingProductReportCreate,
    MarketingProductReportResponse,
    AdminUpdateReportStatus,
)
from app.report.services import ReportService

router = APIRouter(prefix="/reports", tags=["Marketing Product Reports"])


@router.post(
    "",
    response_model=MarketingProductReportResponse,
    summary="Report a Marketing Product (Customer only)"
)
async def create_report(
    report_data: MarketingProductReportCreate,
    current_user=Depends(get_current_user)
):
    """
    Allows a Customer to report a Marketing Product belonging to another Customer.
    The report includes details of both the reporter, the target, and the product information.
    """
    return await ReportService.create_report(report_data)


@router.get(
    "",
    response_model=List[MarketingProductReportResponse],
    summary="View all reports (Admin only)"
)
async def get_all_reports(current_admin=Depends(get_admin)):
    """Admin can view all pending and reviewed reports."""
    return await ReportService.get_all_reports()


@router.get(
    "/{report_id}",
    response_model=MarketingProductReportResponse,
    summary="View a specific report (Admin only)"
)
async def get_report_by_id(report_id: int, current_admin=Depends(get_admin)):
    """Admin can view detailed information for a specific report."""
    return await ReportService.get_report_by_id(report_id)


@router.patch(
    "/{report_id}/status",
    summary="Update report status (Admin only)"
)
async def update_report_status(
    report_id: int,
    body: AdminUpdateReportStatus,
    background_tasks: BackgroundTasks,
    current_admin=Depends(get_admin)
):
    """
    Admin can take two types of actions:
    - **DISMISSED**: The report will be deleted.
    - **REVIEWED**: The target user's account will be set to INACTIVE and an email notification will be sent.
    """
    return await ReportService.admin_update_report_status(
        report_id=report_id,
        new_status=body.status,
        background_tasks=background_tasks
    )