import os
from datetime import datetime
from typing import Optional

from backend.app.config.settings import CAPTURE_ENDPOINT, CAPTURE_DIR
from backend.app.services.auth_service import TokenService
from backend.app.utils.http_client import HTTPClient

class CaptureService:
    """图像抓拍服务类"""
    
    @classmethod
    def capture_image(cls, save_to_file: bool = True) -> Optional[bytes]:
        """抓拍图像
        
        Args:
            save_to_file: 是否保存到文件
            
        Returns:
            Optional[bytes]: 图像二进制数据，如果失败返回None
        """
        # 获取Token
        token = TokenService.get_token()
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = HTTPClient.post(CAPTURE_ENDPOINT, headers=headers)
        
        # 检查响应
        if response.status_code != 200:
            print(f"抓拍失败，状态码：{response.status_code}")
            return None
        
        # 检查是否是图像
        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type:
            print(f"返回内容不是图像，Content-Type: {content_type}")
            print(f"响应内容：{response.text}")
            return None
        
        # 保存图像
        if save_to_file:
            cls._save_image(response.content)
        
        return response.content
    
    @classmethod
    def _save_image(cls, image_data: bytes) -> str:
        """保存图像到文件
        
        Args:
            image_data: 图像二进制数据
            
        Returns:
            str: 保存的文件路径
        """
        # 创建保存目录
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        
        # 生成文件名
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = os.path.join(CAPTURE_DIR, filename)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        print(f"图像保存成功：{file_path}")
        return file_path
