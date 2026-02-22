from fastapi import APIRouter, Depends, File, Form, UploadFile, status, HTTPException
from typing import List, Optional
import json
from app.core.current_user import get_vendor
from app.product.services import ProductService
from app.product.schemas import ProductCreate, ProductResponse, ShippingResponsibility
from app.database.db import prisma

router = APIRouter(tags=["Product Management"])

@router.post("/vendor/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Create new product (Vendor only)")
async def create_product(
    name: str = Form(...),
    description:str = Form(...),
    basePrice: float = Form(...),
    stockUnits: int = Form(...),
    size: Optional[str] = Form(None),
    colors: Optional[str] = Form(None),
    isOnSale: bool = Form(...),
    salePrice: float = Form(...),
    discountPercentage: float = Form(...),
    shippingResponsibility: ShippingResponsibility = Form(ShippingResponsibility.CUSTOMER),
    shippingCharge: float = Form(...),
    category_ids: str = Form(...), # JSON string of IDs e.g. "[1, 2]"
    images: List[UploadFile] = File(...),
    current_vendor=Depends(get_vendor)
):
    # Get vendor's store
    store = await prisma.store.find_unique(where={"vendorId": current_vendor.id})
    if not store:
        raise HTTPException(status_code=400, detail="Vendor must have a store to create products")
    
    try:
        cat_ids = json.loads(category_ids)
        if not isinstance(cat_ids, list):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="categoryIds must be a JSON array of integers e.g. '[1, 2]'")

    product_data = ProductCreate(
        name=name,
        description=description,
        basePrice=basePrice,
        stockUnits=stockUnits,
        size=size,
        colors=colors,
        isOnSale=isOnSale,
        salePrice=salePrice,
        discountPercentage=discountPercentage,
        shippingResponsibility=shippingResponsibility,
        shippingCharge=shippingCharge,
        categoryIds=cat_ids
    )
    
    return await ProductService.create_product(
        product_data=product_data,
        store_id=store.id,
        image_files=images
    )

@router.get("/products", response_model=List[ProductResponse], summary="Get all products with filters")
async def get_products(
    main_category_id: Optional[int] = None,
    sub_category_id: Optional[int] = None,
    store_id: Optional[int] = None
):
    return await ProductService.get_products(
        main_category_id=main_category_id,
        sub_category_id=sub_category_id,
        store_id=store_id
    )

@router.get("/products/{product_id}", response_model=ProductResponse, summary="Get product details")
async def get_product(product_id: int):
    return await ProductService.get_product_by_id(product_id)

@router.delete("/vendor/products/{product_id}", summary="Delete product (Vendor only)")
async def delete_product(
    product_id: int,
    current_vendor=Depends(get_vendor)
):
    store = await prisma.store.find_unique(where={"vendorId": current_vendor.id})
    if not store:
        raise HTTPException(status_code=400, detail="Vendor store not found")
        
    await ProductService.delete_product(product_id=product_id, store_id=store.id)
    return {"message": "Product deleted successfully"}
