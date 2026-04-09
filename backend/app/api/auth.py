from fastapi import APIRouter, Body

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

@router.post("/token/frontend")
async def set_frontend_token(token: str = Body(..., description="前端传递的Token"), expires_in: int = Body(7200, description="Token有效期（秒）")):
    """设置前端传递的Token
    
    Args:
        token: 前端传递的Token字符串
        expires_in: Token有效期（秒），默认7200秒（2小时）
        
    Returns:
        dict: 操作结果
    """
    try:
        TokenService.set_frontend_token(token, expires_in)
        return {"code": "1", "msg": "Token设置成功"}
    except Exception as e:
        return {"code": "0", "msg": str(e)}
