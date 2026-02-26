from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.db import prisma
from app.auth.routers.auth_router import router as auth_router
from app.user.routers.user_router import customer_router,vendor_router
from app.admin.routers.admin_settings_router import router as admin_settings_router
from app.vendor.routers.vendor_store_router import router as vendor_store_router
from app.vendor.routers.vendor_kyc_router import router as vendor_kyc_router
from app.advertisement.routers import router as advertisement_router
from app.category.routers import router as category_router
from app.product.routers import router as product_router
from app.product.search_routers import router as search_router
from app.store.routers import router as store_router
from app.cart.routers import router as cart_router
from app.static_page.routers import router as static_page_router
from app.faq.routers import router as faq_router
from app.marketing_product.routers import router as marketing_product_router
from app.admin.routers.admin_marketing_setting_router import router as admin_marketing_setting_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(
    title="NexPrime API",
    description="E-commerce API with FastAPI and Prisma",
    version="1.0.0",
    lifespan=lifespan
)



@app.get("/")
async def root():
    return {
        "message": "Welcome to NexPrime API",
        "status": "Running",
        "database": "Connected"
    }


app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(vendor_router)
app.include_router(admin_settings_router)
app.include_router(advertisement_router)
app.include_router(category_router)
app.include_router(search_router)
app.include_router(product_router)
app.include_router(vendor_store_router)
app.include_router(vendor_kyc_router)
app.include_router(store_router)
app.include_router(cart_router)
app.include_router(static_page_router)
app.include_router(faq_router)
app.include_router(marketing_product_router)
app.include_router(admin_marketing_setting_router)