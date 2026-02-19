from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from app.core.current_user import get_vendor
from app.vendor.services.vendor_store_service import (
    create_store_service,
    get_my_store_service,
    update_store_service,
)

from app.auth.services.auth_service import vendor_signup_service

router = APIRouter(prefix="/vendor", tags=["Vendor"])

@router.post("/signup", status_code=status.HTTP_201_CREATED, summary="Combined Vendor & Store Signup")
async def vendor_signup(
    fullname: str = Form(...),
    email: str = Form(...),
    phonenumber: str = Form(...),
    password: str = Form(..., min_length=6),
    store_name: str = Form(...),
    store_bio: str = Form(...),
    store_address: str = Form(...),
    residentcard_frontside: UploadFile = File(...),
    residentcard_backside: UploadFile = File(...),
    store_photo: UploadFile = File(...),
    kyc_document: UploadFile = File(...),
):
    return await vendor_signup_service(
        fullname=fullname,
        email=email,
        phonenumber=phonenumber,
        password=password,
        store_name=store_name,
        store_bio=store_bio,
        store_address=store_address,
        front_file=residentcard_frontside,
        back_file=residentcard_backside,
        store_photo=store_photo,
        kyc_file=kyc_document,
    )

@router.post("/store", status_code=status.HTTP_201_CREATED, summary="Create a new store")
async def create_store(
    name: str = Form(...),
    bio: str = Form(None),
    address: str = Form(...),
    photo: UploadFile = File(...),
    current_vendor=Depends(get_vendor),
):
    return await create_store_service(
        name=name,
        bio=bio,
        address=address,
        photo_file=photo,
        vendor_id=current_vendor.id
    )

@router.get("/store/me", summary="Get my store details")
async def get_my_store(current_vendor=Depends(get_vendor)):
    return await get_my_store_service(vendor_id=current_vendor.id)

@router.patch("/store/me", summary="Update my store details")
async def update_my_store(
    name: str = Form(None),
    bio: str = Form(None),
    address: str = Form(None),
    photo: UploadFile = File(None),
    current_vendor=Depends(get_vendor),
):
    return await update_store_service(
        vendor_id=current_vendor.id,
        name=name,
        bio=bio,
        address=address,
        photo_file=photo
    )
