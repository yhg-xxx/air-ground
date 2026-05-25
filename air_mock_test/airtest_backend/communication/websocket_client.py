"""
WebSocket客户端模块

负责与无人机、无人车建立和维护WebSocket连接。
"""

import asyncio
import json
import time
from typing import Optional, Callable, Dict, Any, List
from loguru import logger

import websockets
from websockets.exceptions import ConnectionClosed

from config.constants import CommunicationConstants, MessageTypes


class WebSocketClient:
    """WebSocket客户端"""
    
    def __init__(self, host: str = None, port: int = None, token: str = None):
        self.host = host or CommunicationConstants.HOST
        self.port = port or CommunicationConstants.WS_PORT
        self.token = token or CommunicationConstants.AUTH_TOKEN
        
        self.uri = f"ws://{self.host}:{self.port}?token={self.token}"
        
        # WebSocket连接
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        
        # 重连配置
        self.reconnect_interval = CommunicationConstants.RECONNECT_INTERVAL
        self.max_reconnect_attempts = CommunicationConstants.MAX_RECONNECT_ATTEMPTS
        self.reconnect_attempts = 0
        
        # 心跳配置
        self.heartbeat_interval = CommunicationConstants.HEARTBEAT_INTERVAL
        self.last_heartbeat = 0
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # 接收任务
        self.receive_task: Optional[asyncio.Task] = None
        
        # 回调函数
        self.message_callbacks: List[Callable] = []
        self.connect_callbacks: List[Callable] = []
        self.disconnect_callbacks: List[Callable] = []
        
        # 状态数据
        self.telemetry_data: Dict[str, Any] = {
            'aircraft': {},
            'vehicle': {}
        }
    
    def register_message_callback(self, callback: Callable):
        """注册消息回调"""
        self.message_callbacks.append(callback)
    
    def register_connect_callback(self, callback: Callable):
        """注册连接回调"""
        self.connect_callbacks.append(callback)
    
    def register_disconnect_callback(self, callback: Callable):
        """注册断开回调"""
        self.disconnect_callbacks.append(callback)
    
    async def connect(self) -> bool:
        """连接WebSocket服务器"""
        logger.info(f"[WebSocket] 连接到 {self.uri}")
        
        try:
            self.websocket = await websockets.connect(self.uri, ping_interval=None)
            self.connected = True
            self.reconnect_attempts = 0
            
            logger.info("[WebSocket] 连接成功")
            
            # 启动接收任务
            self.receive_task = asyncio.create_task(self._receive_loop())
            
            # 启动心跳任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 通知连接回调
            for callback in self.connect_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"连接回调执行失败: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"[WebSocket] 连接失败: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        logger.info("[WebSocket] 断开连接")
        
        self.connected = False
        
        # 取消任务
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        
        # 关闭连接
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
            self.websocket = None
        
        # 通知断开回调
        for callback in self.disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"断开回调执行失败: {e}")
    
    async def _receive_loop(self):
        """接收消息循环"""
        while self.connected and self.websocket:
            try:
                message = await self.websocket.recv()
                await self._handle_message(message)
            except ConnectionClosed:
                logger.warning("[WebSocket] 连接已关闭")
                self.connected = False
                break
            except Exception as e:
                logger.error(f"[WebSocket] 接收消息失败: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: str):
        """处理收到的消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', '')
            
            # 更新遥测数据
            self._update_telemetry(data)
            
            # 记录日志
            if msg_type == MessageTypes.AUTH_SUCCESS:
                logger.info("[WebSocket] 认证成功")
            elif msg_type == MessageTypes.AIRCRAFT_TELEMETRY_GNSS:
                logger.debug(f"[遥测] 无人机位置: {data.get('data', {}).get('gps')}")
            elif msg_type == MessageTypes.VEHICLE_TELEMETRY_GNSS:
                logger.debug(f"[遥测] 无人车位置: {data.get('data', {}).get('gps')}")
            
            # 通知回调
            for callback in self.message_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"消息回调执行失败: {e}")
                    
        except json.JSONDecodeError:
            logger.warning(f"[WebSocket] 收到非JSON消息: {message[:100]}")
        except Exception as e:
            logger.error(f"[WebSocket] 处理消息失败: {e}")
    
    def _update_telemetry(self, data: Dict):
        """更新遥测数据"""
        msg_type = data.get('type', '')
        msg_data = data.get('data', {})
        
        if 'aircraft' in msg_type:
            self.telemetry_data['aircraft'].update(msg_data)
        elif 'vehicle' in msg_type:
            self.telemetry_data['vehicle'].update(msg_data)
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.connected:
            try:
                await self.send_message({'type': MessageTypes.HEARTBEAT})
                self.last_heartbeat = time.time()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WebSocket] 心跳发送失败: {e}")
                await asyncio.sleep(1)
    
    async def send_message(self, message: Dict) -> bool:
        """发送消息"""
        if not self.connected or not self.websocket:
            logger.warning("[WebSocket] 未连接，无法发送消息")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"[WebSocket] 发送消息失败: {e}")
            return False
    
    async def send_control(self, target: str, channel: int, value: int) -> bool:
        """发送控制指令"""
        message = {
            'type': MessageTypes.CONTROL,
            'target': target,
            'channel': channel,
            'value': value
        }
        return await self.send_message(message)
    
    async def reconnect(self) -> bool:
        """重连"""
        logger.info("[WebSocket] 尝试重连...")
        
        await self.disconnect()
        
        while self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"[WebSocket] 第{self.reconnect_attempts}次重连尝试")
            
            if await self.connect():
                return True
            
            await asyncio.sleep(self.reconnect_interval)
        
        logger.error("[WebSocket] 重连失败，已达最大尝试次数")
        return False
    
    def get_telemetry(self, device: str = None) -> Dict:
        """获取遥测数据"""
        if device:
            return self.telemetry_data.get(device, {})
        return self.telemetry_data
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
