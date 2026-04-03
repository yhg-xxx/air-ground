from fastapi import APIRouter
from app.api import auth, capture, ws

api_router = APIRouter()

# 包含所有路由
api_router.include_router(auth.router)
api_router.include_router(capture.router)
api_router.include_router(ws.router)
