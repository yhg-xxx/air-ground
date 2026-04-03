from fastapi import APIRouter, Response

from backend.app.services.capture_service import CaptureService

router = APIRouter(prefix="/api/gimbal", tags=["capture"])

@router.post("/capture")
async def capture_image():
    """抓拍图像
    
    Returns:
        Response: 图像二进制数据
    """
    try:
        image_data = CaptureService.capture_image(save_to_file=True)
        if image_data:
            return Response(content=image_data, media_type="image/jpeg")
        else:
            return {"code": "0", "msg": "抓拍失败"}
    except Exception as e:
        return {"code": "0", "msg": str(e)}
