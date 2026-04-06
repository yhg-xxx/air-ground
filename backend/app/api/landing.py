from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.app.services.landing_service import LandingService

router = APIRouter(prefix="/api/landing", tags=["landing"])

# 创建全局LandingService实例
landing_service = LandingService()

@router.post("/start")
async def start_landing(target_aruco_id: int = 0) -> Dict[str, Any]:
    """开始降落过程
    
    Args:
        target_aruco_id: 目标Aruco码ID
        
    Returns:
        Dict[str, Any]: 降落状态信息
    """
    try:
        result = await landing_service.start_landing(target_aruco_id)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始降落失败: {str(e)}")

@router.get("/status")
async def get_landing_status() -> Dict[str, Any]:
    """获取降落状态
    
    Returns:
        Dict[str, Any]: 降落状态信息
    """
    try:
        return landing_service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.post("/cancel")
async def cancel_landing() -> Dict[str, Any]:
    """取消降落过程
    
    Returns:
        Dict[str, Any]: 取消状态信息
    """
    try:
        result = await landing_service.cancel_landing()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消降落失败: {str(e)}")
