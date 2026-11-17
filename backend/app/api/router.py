from fastapi import APIRouter

from app.api.v1 import auth, blind_boxes, categories, orders, products

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/v1")
api_router.include_router(categories.router, prefix="/v1/categories", tags=["分类管理"])
api_router.include_router(products.router, prefix="/v1/products")
api_router.include_router(blind_boxes.router, prefix="/v1/blind-boxes")
api_router.include_router(orders.customer_router, prefix="/v1")
api_router.include_router(orders.merchant_router, prefix="/v1")
