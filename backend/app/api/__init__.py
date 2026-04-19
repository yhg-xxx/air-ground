from fastapi import APIRouter
from app.api import auth, capture, ws, landing, control

api_router = APIRouter()

# 包含所有路由
api_router.include_router(auth.router)
api_router.include_router(capture.router)
api_router.include_router(ws.router)
api_router.include_router(landing.router)
api_router.include_router(control.router)
api_router.include_router(maze.router)
