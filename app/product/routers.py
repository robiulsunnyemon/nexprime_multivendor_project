from fastapi import APIRouter, Depends, File, Form, UploadFile, status, HTTPException, Query
from typing import List, Optional, Any
import json
from app.core.current_user import get_vendor
from app.product.services import ProductService
from app.product.schemas import ProductCreate, ProductResponse, ShippingResponsibility, ProductSize
from app.database.db import prisma

router = APIRouter(tags=["Product Management"])

@router.post("/vendor/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Create new product (Vendor only)")
async def create_product(
    name: str = Form(...),
    description:str = Form(...),
    basePrice: float = Form(...),
    stockUnits: int = Form(...),
    size: Optional[List[str]] = Form(None),
    colors: Optional[List[str]] = Form(None),
    isDiscountSale: bool = Form(...),
    salePrice: Optional[float] = Form(None),
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
        # cat_ids = json.loads(category_ids)
        # if not isinstance(cat_ids, list):
        #     raise ValueError
        raw_data = category_ids.strip("[]")
        cat_ids = [int(id.strip()) for id in raw_data.split(",") if id.strip()]
        if not cat_ids:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="categoryIds must be a JSON array of integers e.g. '[1, 2]'")

    # Handle comma-separated strings for size and colors
    parsed_sizes = []
    if size:
        # If it's a list with one item that has commas, split it
        if len(size) == 1 and "," in size[0]:
            parsed_sizes = [s.strip().upper() for s in size[0].split(",") if s.strip()]
        else:
            parsed_sizes = [s.strip().upper() for s in size if s.strip()]

    parsed_colors = []
    if colors:
        if len(colors) == 1 and "," in colors[0]:
            parsed_colors = [c.strip().upper() for c in colors[0].split(",") if c.strip()]
        else:
            parsed_colors = [c.strip().upper() for c in colors if c.strip()]

    product_data = ProductCreate(
        name=name,
        description=description,
        basePrice=basePrice,
        stockUnits=stockUnits,
        size=parsed_sizes,
        colors=parsed_colors,
        isDiscountSale=isDiscountSale,
        salePrice=salePrice,
        shippingResponsibility=shippingResponsibility,
        shippingCharge=shippingCharge,
        categoryIds=cat_ids
    )
    
    # Filter images to ensure we only have actual files
    valid_images = []
    if images:
        valid_images = [img for img in images if isinstance(img, UploadFile) and img.filename]

    if not valid_images:
        raise HTTPException(status_code=400, detail="At least one product image is required")

    return await ProductService.create_product(
        product_data=product_data,
        store_id=store.id,
        image_files=valid_images
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
    size: Optional[ProductSize] = Query(None),
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
    size: Optional[List[str]] = Form(None),
    colors: Optional[List[str]] = Form(None),
    isDiscountSale: Optional[bool] = Form(None),
    salePrice: Optional[float] = Form(None),
    shippingResponsibility: Optional[ShippingResponsibility] = Form(None),
    shippingCharge: Optional[float] = Form(None),
    category_ids: Optional[str] = Form(None), 
    images: Optional[List[Any]] = File(None),
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
    
    if size is not None:
        processed_size = []
        if len(size) == 1 and "," in size[0]:
            processed_size = [s.strip().upper() for s in size[0].split(",") if s.strip()]
        else:
            processed_size = [s.strip().upper() for s in size if s.strip()]
        
        if processed_size:
            update_dict["size"] = processed_size
            
    if colors is not None:
        processed_colors = []
        if len(colors) == 1 and "," in colors[0]:
            processed_colors = [c.strip().upper() for c in colors[0].split(",") if c.strip()]
        else:
            processed_colors = [c.strip().upper() for c in colors if c.strip()]
            
        if processed_colors:
            update_dict["colors"] = processed_colors
            
    if isDiscountSale is not None: update_dict["isDiscountSale"] = isDiscountSale
    if salePrice is not None: update_dict["salePrice"] = salePrice
    if shippingResponsibility is not None: update_dict["shippingResponsibility"] = shippingResponsibility
    if shippingCharge is not None: update_dict["shippingCharge"] = shippingCharge

    cat_ids = None
    if category_ids:
        try:
            cat_ids = json.loads(category_ids)
            if not isinstance(cat_ids, list): raise ValueError
        except ValueError:
            raise HTTPException(status_code=400, detail="categoryIds must be a JSON array of integers e.g. '[1, 2]'")

    # Filter images to ensure we only have actual files (bypass empty strings from Swagger/Client)
    valid_images = []
    if images:
        valid_images = [img for img in images if isinstance(img, UploadFile) and img.filename]

    return await ProductService.update_product(
        product_id=product_id,
        store_id=store.id,
        product_data=update_dict,
        category_ids=cat_ids,
        image_files=valid_images if valid_images else None
    )
