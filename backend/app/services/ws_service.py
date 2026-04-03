import asyncio
import json
from typing import Optional, Dict, Any, Callable
import websockets

from backend.app.config.settings import WS_ENDPOINT, MIN_CONTROL_INTERVAL
from backend.app.services.auth_service import TokenService

class WebSocketService:
    """WebSocket服务类"""
    
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.message_handler: Optional[Callable[[Dict[str, Any]], None]] = None
    
    async def connect(self):
        """连接到WebSocket服务器
        
        Raises:
            Exception: 连接失败时抛出异常
        """
        # 获取Token
        token = TokenService.get_token()
        ws_url = f"{WS_ENDPOINT}?token={token}"
        
        print(f"连接WebSocket服务：{ws_url}")
        
        try:
            self.ws = await websockets.connect(ws_url, ping_interval=None)
            self.is_connected = True
            print("WebSocket连接成功")
            
            # 启动消息接收循环
            asyncio.create_task(self._receive_messages())
        except Exception as e:
            print(f"WebSocket连接失败：{str(e)}")
            raise
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.ws and self.is_connected:
            try:
                await self.ws.close()
                self.is_connected = False
                print("WebSocket连接已关闭")
            except Exception as e:
                print(f"断开连接时出错：{str(e)}")
    
    async def _receive_messages(self):
        """接收并处理WebSocket消息"""
        if not self.ws:
            return
        
        try:
            while self.is_connected:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # 处理消息
                await self._handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket连接已关闭")
            self.is_connected = False
        except Exception as e:
            print(f"接收消息时出错：{str(e)}")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """处理接收到的消息
        
        Args:
            data: 消息数据
        """
        msg_type = data.get("type")
        
        if msg_type == "auth_success":
            print("【WebSocket】登录成功")
        elif msg_type == "ping":
            print("【WebSocket】收到心跳")
        elif msg_type == "aircraft_telemetry_power":
            power = data["data"].get("power")
            voltage = data["data"].get("voltage")
            print(f"【遥测】无人机 电量={power} 电压={voltage}V")
        elif msg_type == "aircraft_telemetry_gnss":
            gps = data["data"].get("gps")
            speed = data["data"].get("speed")
            print(f"【遥测】无人机 GPS={gps} 速度={speed}")
        elif msg_type == "vehicle_telemetry_power":
            power = data["data"].get("power")
            voltage = data["data"].get("voltage")
            print(f"【遥测】车辆 电量={power} 电压={voltage}V")
        elif msg_type == "vehicle_telemetry_gnss":
            gps = data["data"].get("gps")
            speed = data["data"].get("speed")
            print(f"【遥测】车辆 GPS={gps} 速度={speed}")
        
        # 调用外部消息处理器
        if self.message_handler:
            self.message_handler(data)
    
    async def send_control(self, target: str, channel: int, value: int):
        """发送控制指令
        
        Args:
            target: 目标设备，"aircraft"或"vehicle"
            channel: 通道号
            value: 控制值（1000-2000）
            
        Raises:
            Exception: 发送失败时抛出异常
        """
        if not self.ws or not self.is_connected:
            raise Exception("WebSocket未连接")
        
        # 验证参数
        if target not in ["aircraft", "vehicle"]:
            raise ValueError("target必须是'aircraft'或'vehicle'")
        
        if not 1000 <= value <= 2000:
            raise ValueError("value必须在1000-2000之间")
        
        # 构建消息
        message = {
            "type": "control",
            "target": target,
            "channel": channel,
            "value": value
        }
        
        # 发送消息
        await self.ws.send(json.dumps(message))
        print(f"[{target}] 通道{channel} 发送值 {value}")
        
        # 控制间隔
        await asyncio.sleep(MIN_CONTROL_INTERVAL)
