"""
HTTP API客户端模块

负责与地面站的HTTP API通信。
"""

import requests
import json
import base64
from typing import Optional, Dict, Any, Tuple
from loguru import logger

from config.constants import CommunicationConstants


class APIClient:
    """HTTP API客户端"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or CommunicationConstants.HOST
        self.port = port or CommunicationConstants.HTTP_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        
        # 认证令牌
        self.token: Optional[str] = None
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # 超时设置
        self.timeout = 30
    
    def set_token(self, token: str):
        """设置认证令牌"""
        self.token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Dict = None, files: Dict = None) -> Tuple[bool, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method == 'POST':
                if files:
                    response = self.session.post(url, files=files, timeout=self.timeout)
                else:
                    response = self.session.post(url, json=data, timeout=self.timeout)
            else:
                return False, f"不支持的HTTP方法: {method}"
            
            response.raise_for_status()
            return True, response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[API] 请求失败: {e}")
            return False, str(e)
        except json.JSONDecodeError:
            return True, response.text
        except Exception as e:
            logger.error(f"[API] 请求异常: {e}")
            return False, str(e)
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """用户认证"""
        logger.info(f"[API] 用户认证: {username}")
        
        data = {
            'username': username,
            'password': password
        }
        
        success, result = self._make_request('POST', '/api/auth/token', data)
        
        if success and isinstance(result, dict):
            if result.get('code') == '1':
                token = result.get('data', {}).get('token')
                if token:
                    self.set_token(token)
                    logger.info("[API] 认证成功")
                    return True, token
        
        logger.error(f"[API] 认证失败: {result}")
        return False, str(result)
    
    def capture_image(self) -> Tuple[bool, Optional[bytes]]:
        """抓拍图像"""
        logger.info("[API] 请求抓拍图像")
        
        success, result = self._make_request('GET', '/api/gimbal/capture')
        
        if success:
            # 假设返回的是base64编码的图像
            if isinstance(result, dict) and 'image' in result:
                try:
                    image_data = base64.b64decode(result['image'])
                    return True, image_data
                except Exception as e:
                    logger.error(f"[API] 图像解码失败: {e}")
                    return False, None
        
        return False, None
    
    def process_landing(self, image_data: str) -> Tuple[bool, Dict]:
        """处理降落图像识别"""
        logger.info("[API] 请求降落图像处理")
        
        data = {'image': image_data}
        
        success, result = self._make_request('POST', '/api/landing/process', data)
        
        if success and isinstance(result, dict):
            if result.get('code') == '1':
                return True, result.get('data', {})
        
        return False, result if isinstance(result, dict) else {}
    
    def detect_arch(self, image_data: str) -> Tuple[bool, Dict]:
        """拱门识别"""
        logger.info("[API] 请求拱门识别")
        
        data = {'image': image_data}
        
        success, result = self._make_request('POST', '/api/arch/detect', data)
        
        if success and isinstance(result, dict):
            if result.get('code') == '1':
                return True, result.get('data', {})
        
        return False, result if isinstance(result, dict) else {}
    
    def detect_aruco(self, image_data: str) -> Tuple[bool, Dict]:
        """ArUco标记识别"""
        logger.info("[API] 请求ArUco识别")
        
        data = {'image': image_data}
        
        success, result = self._make_request('POST', '/api/aruco/detect', data)
        
        if success and isinstance(result, dict):
            if result.get('code') == '1':
                return True, result.get('data', {})
        
        return False, result if isinstance(result, dict) else {}
    
    def start_auto_mission(self) -> Tuple[bool, str]:
        """启动自动化任务"""
        logger.info("[API] 请求启动自动化任务")
        
        success, result = self._make_request('POST', '/api/auto/start')
        
        if success and isinstance(result, dict):
            if result.get('code') == '1':
                return True, result.get('msg', '任务已启动')
        
        return False, str(result)
    
    def upload_map(self, map_data: Dict) -> Tuple[bool, str]:
        """上传地图数据"""
        logger.info("[API] 上传地图数据")
        
        success, result = self._make_request('POST', '/api/map/upload', map_data)
        
        if success and isinstance(result, dict):
            if result.get('code') == '1':
                return True, "地图上传成功"
        
        return False, str(result)
    
    def get_status(self) -> Tuple[bool, Dict]:
        """获取系统状态"""
        success, result = self._make_request('GET', '/api/status')
        
        if success and isinstance(result, dict):
            return True, result
        
        return False, {}


class APIService:
    """API服务"""
    
    def __init__(self):
        self.client = APIClient()
        self.authenticated = False
    
    async def authenticate(self, username: str = None, password: str = None) -> bool:
        """认证"""
        if username is None:
            username = CommunicationConstants.AUTH_USERNAME
        if password is None:
            password = CommunicationConstants.AUTH_PASSWORD
        
        success, token = self.client.authenticate(username, password)
        self.authenticated = success
        return success
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.authenticated
    
    def get_client(self) -> APIClient:
        """获取API客户端"""
        return self.client
