from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import List, Optional
from app.core.current_user import get_current_user
from app.database.db import prisma
from app.marketing_product.schemas import (
    MarketingProductCreate,
    MarketingProductUpdate,
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
    current_user=Depends(get_current_user)
):

    if str(current_user.role) != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create marketing products"
        )

    setting = await prisma.marketingproductsetting.find_unique(where={"id": 1})


    if not setting:
        setting = await prisma.marketingproductsetting.create(
            data={"id": 1, "isPublishingEnabled": True, "publishingFee": 0.50}
        )


    if not setting.isPublishingEnabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Product publishing is currently restricted from the admin side. Please try again later."
        )

    if round(publishingFee, 2) != round(setting.publishingFee, 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Please provide the correct publishing fee. Current publishing fee: ${setting.publishingFee:.2f}"
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
async def get_all_marketing_products(goodsType: Optional[str] = None, location: Optional[str] = None):
    return await MarketingProductService.get_all_marketing_products(goodsType, location)

@router.get("/my", response_model=List[MarketingProductWithCreatorResponse], summary="Get my marketing products")
async def get_my_marketing_products(current_user=Depends(get_current_user)):
    return await MarketingProductService.get_my_marketing_products(creator_id=current_user.id)

@router.get("/{product_id}", response_model=MarketingProductWithCreatorResponse, summary="Get marketing product details")
async def get_marketing_product_by_id(product_id: int):
    return await MarketingProductService.get_marketing_product_by_id(product_id)

@router.delete("/{product_id}", summary="Delete a marketing product (Creator or Admin only)")
async def delete_marketing_product(
    product_id: int, 
    current_user=Depends(get_current_user)
):
    return await MarketingProductService.delete_marketing_product(
        product_id=product_id,
        user_id=current_user.id,
        user_role=str(current_user.role)
    )

@router.patch("/{product_id}", response_model=MarketingProductWithCreatorResponse, summary="Update a marketing product (Creator only)")
async def update_marketing_product(
    product_id: int,
    name: Optional[str] = Form(None),
    shippingCharge: Optional[float] = Form(None),
    goodsType: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    shippingResponsibility: Optional[ShippingResponsibility] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    current_user=Depends(get_current_user)
):
    update_data = MarketingProductUpdate(
        name=name,
        shippingCharge=shippingCharge,
        goodsType=goodsType,
        location=location,
        description=description,
        price=price,
        shippingResponsibility=shippingResponsibility
    )

    return await MarketingProductService.update_marketing_product(
        product_id=product_id,
        user_id=current_user.id,
        update_data=update_data,
        image_files=images
    )
