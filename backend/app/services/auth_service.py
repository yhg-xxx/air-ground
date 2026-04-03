import json
import os
from datetime import datetime, timedelta
from typing import Optional

from backend.app.config.settings import TOKEN_ENDPOINT, USERNAME, PASSWORD
from backend.app.utils.http_client import HTTPClient

class TokenService:
    """Token服务类"""
    
    TOKEN_FILE = "token.json"
    
    @classmethod
    def get_token(cls) -> str:
        """获取Token，如果Token不存在或已过期则自动刷新
        
        Returns:
            str: Token字符串
        """
        token_data = cls._load_token()
        if token_data and not cls._is_token_expired(token_data):
            return token_data["token"]
        
        # Token不存在或已过期，重新获取
        return cls._refresh_token()
    
    @classmethod
    def _load_token(cls) -> Optional[dict]:
        """从文件加载Token
        
        Returns:
            Optional[dict]: Token数据，如果文件不存在返回None
        """
        if os.path.exists(cls.TOKEN_FILE):
            with open(cls.TOKEN_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return None
        return None
    
    @classmethod
    def _save_token(cls, token: str, expires_in: int = 7200):
        """保存Token到文件
        
        Args:
            token: Token字符串
            expires_in: Token有效期（秒），默认7200秒（2小时）
        """
        token_data = {
            "token": token,
            "timestamp": datetime.now().isoformat(),
            "expires_in": expires_in
        }
        with open(cls.TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def _is_token_expired(cls, token_data: dict) -> bool:
        """判断Token是否已过期
        
        Args:
            token_data: Token数据
            
        Returns:
            bool: 是否过期
        """
        timestamp_str = token_data.get("timestamp")
        if not timestamp_str:
            return True
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            # 使用接口返回的expires_in值，默认7200秒（2小时）
            expires_in = token_data.get("expires_in", 7200)
            return datetime.now() - timestamp > timedelta(seconds=expires_in)
        except ValueError:
            return True
    
    @classmethod
    def _refresh_token(cls) -> str:
        """刷新Token
        
        Returns:
            str: 新的Token
            
        Raises:
            Exception: 获取Token失败时抛出异常
        """
        headers = {"Content-Type": "application/json"}
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        response = HTTPClient.post(TOKEN_ENDPOINT, data=data, headers=headers)
        result = response.json()
        
        if result.get("code") == "1":
            token = result["data"]["token"]
            expires_in = result["data"].get("expires_in", 7200)
            cls._save_token(token, expires_in)
            return token
        else:
            raise Exception(f"获取Token失败：{result.get('msg', '未知错误')}")
