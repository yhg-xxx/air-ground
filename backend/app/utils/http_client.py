import requests
from typing import Dict, Any, Optional

class HTTPClient:
    """HTTP客户端工具类"""
    
    @staticmethod
    def post(url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """发送POST请求
        
        Args:
            url: 请求URL
            data: 请求数据
            headers: 请求头
            
        Returns:
            requests.Response: 响应对象
        """
        return requests.post(url, json=data, headers=headers)
    
    @staticmethod
    def get(url: str, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """发送GET请求
        
        Args:
            url: 请求URL
            headers: 请求头
            
        Returns:
            requests.Response: 响应对象
        """
        return requests.get(url, headers=headers)
