from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from app.core.current_user import get_admin
from app.faq.services import FaqService
from app.faq.schemas import FaqCreate, FaqUpdate, FaqResponse

router = APIRouter(prefix="/faqs", tags=["FAQ Management"])

@router.post("", response_model=FaqResponse, status_code=status.HTTP_201_CREATED, summary="Create new FAQ (Admin only)")
async def create_faq(
    faq_data: FaqCreate,
    current_admin = Depends(get_admin)
):
    return await FaqService.create_faq(faq_data)

@router.get("", response_model=List[FaqResponse], summary="Get all active FAQs")
async def get_active_faqs():
    return await FaqService.get_active_faqs()

@router.get("/admin", response_model=List[FaqResponse], summary="Get all FAQs for admin (including inactive)")
async def get_all_faqs_admin(current_admin = Depends(get_admin)):
    return await FaqService.get_all_faqs_admin()

@router.patch("/{faq_id}", response_model=FaqResponse, summary="Update FAQ or change status (Admin only)")
async def update_faq(
    faq_id: int,
    update_data: FaqUpdate,
    current_admin = Depends(get_admin)
):
    return await FaqService.update_faq(faq_id, update_data)

@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete FAQ (Admin only)")
async def delete_faq(faq_id: int, current_admin = Depends(get_admin)):
    await FaqService.delete_faq(faq_id)
    return None
