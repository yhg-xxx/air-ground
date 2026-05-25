"""
消息处理器模块

负责处理WebSocket消息和HTTP请求的消息格式转换。
"""

import json
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from loguru import logger

from config.constants import MessageTypes


@dataclass
class Message:
    """消息数据类"""
    type: str
    device: Optional[str] = None
    timestamp: float = None
    data: Dict = None
    status: str = "ok"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.data is None:
            self.data = {}
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'type': self.type,
            'device': self.device,
            'timestamp': self.timestamp,
            'data': self.data,
            'status': self.status
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """从字典创建消息"""
        return cls(
            type=data.get('type', 'unknown'),
            device=data.get('device'),
            timestamp=data.get('timestamp', time.time()),
            data=data.get('data', {}),
            status=data.get('status', 'ok')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> Optional['Message']:
        """从JSON字符串创建消息"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError:
            return None


class MessageHandler:
    """消息处理器"""
    
    def __init__(self):
        # 消息处理器映射
        self.handlers: Dict[str, List[Callable]] = {}
        
        # 消息过滤器
        self.filters: List[Callable[[Message], bool]] = []
        
        # 统计
        self.message_count = 0
        self.error_count = 0
    
    def register_handler(self, msg_type: str, handler: Callable):
        """注册消息处理器"""
        if msg_type not in self.handlers:
            self.handlers[msg_type] = []
        self.handlers[msg_type].append(handler)
        logger.debug(f"注册消息处理器: {msg_type}")
    
    def register_filter(self, filter_func: Callable[[Message], bool]):
        """注册消息过滤器"""
        self.filters.append(filter_func)
    
    def handle_message(self, message_data: Dict) -> bool:
        """处理消息"""
        self.message_count += 1
        
        try:
            # 解析消息
            msg = Message.from_dict(message_data)
            
            # 应用过滤器
            for filter_func in self.filters:
                if not filter_func(msg):
                    return False
            
            # 查找处理器
            handlers = self.handlers.get(msg.type, [])
            
            # 调用处理器
            for handler in handlers:
                try:
                    handler(msg)
                except Exception as e:
                    logger.error(f"消息处理器执行失败: {e}")
                    self.error_count += 1
            
            return len(handlers) > 0
            
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            self.error_count += 1
            return False
    
    def create_control_message(self, target: str, channel: int, 
                              value: int) -> Message:
        """创建控制消息"""
        return Message(
            type=MessageTypes.CONTROL,
            device=target,
            data={
                'channel': channel,
                'value': value
            }
        )
    
    def create_telemetry_message(self, device: str, 
                                 telemetry_type: str,
                                 data: Dict) -> Message:
        """创建遥测消息"""
        msg_type = f"{device}_telemetry_{telemetry_type}"
        return Message(
            type=msg_type,
            device=device,
            data=data
        )
    
    def create_error_message(self, error: str, device: str = None) -> Message:
        """创建错误消息"""
        return Message(
            type='error',
            device=device,
            data={'error': error},
            status='error'
        )
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_messages': self.message_count,
            'error_count': self.error_count,
            'registered_handlers': {
                msg_type: len(handlers)
                for msg_type, handlers in self.handlers.items()
            }
        }


class MessageBuilder:
    """消息构建器"""
    
    @staticmethod
    def build_auth_request(username: str, password: str) -> Dict:
        """构建认证请求"""
        return {
            'username': username,
            'password': password
        }
    
    @staticmethod
    def build_auth_response(token: str, success: bool = True) -> Dict:
        """构建认证响应"""
        if success:
            return {
                'code': '1',
                'msg': 'success',
                'data': {'token': token}
            }
        else:
            return {
                'code': '0',
                'msg': 'invalid credentials'
            }
    
    @staticmethod
    def build_control_command(target: str, channel: int, value: int) -> Dict:
        """构建控制指令"""
        return {
            'type': MessageTypes.CONTROL,
            'target': target,
            'channel': channel,
            'value': value
        }
    
    @staticmethod
    def build_telemetry(device: str, 
                       position: tuple = None,
                       attitude: tuple = None,
                       power: int = None,
                       voltage: float = None) -> Dict:
        """构建遥测数据"""
        data = {
            'device': device,
            'timestamp': time.time()
        }
        
        if position:
            data['position'] = position
        if attitude:
            data['attitude'] = attitude
        if power is not None:
            data['power'] = power
        if voltage is not None:
            data['voltage'] = voltage
        
        return data
    
    @staticmethod
    def build_image_request() -> Dict:
        """构建图像请求"""
        return {'type': 'capture_image_request'}
    
    @staticmethod
    def build_image_response(image_data: str) -> Dict:
        """构建图像响应"""
        return {
            'type': 'capture_image_response',
            'data': image_data
        }


class MessageValidator:
    """消息验证器"""
    
    @staticmethod
    def validate_control_message(data: Dict) -> bool:
        """验证控制消息"""
        required_fields = ['type', 'target', 'channel', 'value']
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_telemetry_message(data: Dict) -> bool:
        """验证遥测消息"""
        return 'device' in data and 'timestamp' in data
    
    @staticmethod
    def validate_auth_request(data: Dict) -> bool:
        """验证认证请求"""
        return 'username' in data and 'password' in data
    
    @staticmethod
    def validate_image_data(image_data: str) -> bool:
        """验证图像数据"""
        if not image_data:
            return False
        
        # 检查是否是base64格式
        try:
            import base64
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            base64.b64decode(image_data)
            return True
        except Exception:
            return False
