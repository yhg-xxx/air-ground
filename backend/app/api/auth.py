from fastapi import APIRouter

from backend.app.services.auth_service import TokenService

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/token")
async def get_token():
    """获取Token
    
    Returns:
        dict: 包含Token的响应
    """
    try:
        token = TokenService.get_token()
        return {"code": "1", "data": {"token": token}, "msg": "获取Token成功"}
    except Exception as e:
        return {"code": "0", "msg": str(e)}
