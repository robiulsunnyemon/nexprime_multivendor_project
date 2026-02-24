from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import List, Optional
from app.core.current_user import get_current_user
from app.marketing_product.schemas import (
    MarketingProductCreate, 
    MarketingProductWithCreatorResponse,
    ShippingResponsibility
)
from app.marketing_product.services import MarketingProductService

router = APIRouter(prefix="/marketing-products", tags=["Marketing Product Management"])

@router.post("", response_model=MarketingProductWithCreatorResponse, summary="Create a new marketing product (Customers only)")
async def create_marketing_product(
    name: str = Form(...),
    shippingCharge: float = Form(...),
    publishingFee: float = Form(...),
    goodsType: str = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    shippingResponsibility: ShippingResponsibility = Form(...),
    images: List[UploadFile] = File(...),
    current_user = Depends(get_current_user)
):
    # Depending on how the Role enum is handled in the User object, 
    # it might be a string or the enum itself. Usually it's a string from Prisma.
    if str(current_user.role) != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create marketing products"
        )
    
    product_data = MarketingProductCreate(
        name=name,
        goodsType=goodsType,
        location=location,
        description=description,
        price=price,
        publishingFee=publishingFee,
        shippingResponsibility=shippingResponsibility,
        shippingCharge=shippingCharge
    )
    
    return await MarketingProductService.create_marketing_product(
        product_data=product_data,
        creator_id=current_user.id,
        image_files=images
    )

@router.get("", response_model=List[MarketingProductWithCreatorResponse], summary="Get all marketing products")
async def get_all_marketing_products():
    return await MarketingProductService.get_all_marketing_products()

@router.get("/my", response_model=List[MarketingProductWithCreatorResponse], summary="Get my marketing products")
async def get_my_marketing_products(current_user = Depends(get_current_user)):
    return await MarketingProductService.get_my_marketing_products(creator_id=current_user.id)

@router.get("/{product_id}", response_model=MarketingProductWithCreatorResponse, summary="Get marketing product details")
async def get_marketing_product_by_id(product_id: int):
    return await MarketingProductService.get_marketing_product_by_id(product_id)
