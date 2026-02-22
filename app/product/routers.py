from fastapi import APIRouter, Depends, File, Form, UploadFile, status, HTTPException, Query
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

@router.get("/products/filter", response_model=List[ProductResponse], summary="Advanced product filtering")
async def filter_products(
    shop_id: Optional[int] = Query(None),
    subcategory_ids: Optional[List[int]] = Query(None),
    size: Optional[str] = Query(None),
    color: Optional[str] = Query(None)
):
    return await ProductService.get_products_filtered(
        shop_id=shop_id,
        subcategory_ids=subcategory_ids,
        size=size,
        color=color
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

@router.patch("/vendor/products/{product_id}", response_model=ProductResponse, summary="Update product (Vendor only)")
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    basePrice: Optional[float] = Form(None),
    stockUnits: Optional[int] = Form(None),
    size: Optional[str] = Form(None),
    colors: Optional[str] = Form(None),
    isOnSale: Optional[bool] = Form(None),
    salePrice: Optional[float] = Form(None),
    discountPercentage: Optional[float] = Form(None),
    shippingResponsibility: Optional[ShippingResponsibility] = Form(None),
    shippingCharge: Optional[float] = Form(None),
    category_ids: Optional[str] = Form(None), 
    images: Optional[List[UploadFile]] = File(None),
    current_vendor=Depends(get_vendor)
):
    store = await prisma.store.find_unique(where={"vendorId": current_vendor.id})
    if not store:
        raise HTTPException(status_code=400, detail="Vendor store not found")

    update_dict = {}
    if name is not None: update_dict["name"] = name
    if description is not None: update_dict["description"] = description
    if basePrice is not None: update_dict["basePrice"] = basePrice
    if stockUnits is not None: update_dict["stockUnits"] = stockUnits
    if size is not None: update_dict["size"] = size
    if colors is not None: update_dict["colors"] = colors
    if isOnSale is not None: update_dict["isOnSale"] = isOnSale
    if salePrice is not None: update_dict["salePrice"] = salePrice
    if discountPercentage is not None: update_dict["discountPercentage"] = discountPercentage
    if shippingResponsibility is not None: update_dict["shippingResponsibility"] = shippingResponsibility
    if shippingCharge is not None: update_dict["shippingCharge"] = shippingCharge

    cat_ids = None
    if category_ids:
        try:
            cat_ids = json.loads(category_ids)
            if not isinstance(cat_ids, list): raise ValueError
        except ValueError:
            raise HTTPException(status_code=400, detail="categoryIds must be a JSON array of integers e.g. '[1, 2]'")

    return await ProductService.update_product(
        product_id=product_id,
        store_id=store.id,
        product_data=update_dict,
        category_ids=cat_ids,
        image_files=images
    )
