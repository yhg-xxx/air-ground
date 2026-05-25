"""
设备控制器模块

负责无人机和无人车的底层控制指令发送与状态管理。
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, Tuple
from loguru import logger

from config.constants import (
    AircraftChannels, VehicleChannels, ControlValues,
    MotionLimits, CoordinateConstants
)


class DeviceController:
    """设备控制器基类"""
    
    def __init__(self, device_type: str, websocket_client=None):
        self.device_type = device_type
        self.websocket_client = websocket_client
        self.is_connected = False
        self.last_command_time = 0
        
        # 设备状态
        self.status = {
            'connected': False,
            'position': [0.0, 0.0],
            'speed': 0.0,
            'power': 100,
            'voltage': 0.0,
            'timestamp': 0
        }
    
    async def send_command(self, channel: int, value: int) -> bool:
        """发送控制指令"""
        if not self.websocket_client:
            logger.warning(f"[{self.device_type}] WebSocket未连接，无法发送指令")
            return False
        
        # 检查最小间隔
        current_time = time.time()
        if current_time - self.last_command_time < ControlValues.MIN_INTERVAL:
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        
        try:
            message = {
                'type': 'control',
                'target': self.device_type,
                'channel': channel,
                'value': value
            }
            await self.websocket_client.send(json.dumps(message))
            self.last_command_time = time.time()
            logger.debug(f"[{self.device_type}] 通道{channel} 值{value}")
            return True
        except Exception as e:
            logger.error(f"[{self.device_type}] 发送指令失败: {e}")
            return False
    
    def update_status(self, status_data: Dict[str, Any]):
        """更新设备状态"""
        self.status.update(status_data)
        self.status['timestamp'] = time.time()
    
    def get_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        return self.status.copy()


class AircraftController(DeviceController):
    """无人机控制器"""
    
    def __init__(self, websocket_client=None):
        super().__init__('aircraft', websocket_client)
        self.altitude = 0.0
        self.gimbal_pitch = 0.0
        self.gimbal_roll = 0.0
    
    async def takeoff(self, target_height: float = 10.0) -> bool:
        """起飞"""
        logger.info(f"[无人机] 执行起飞，目标高度: {target_height}m")
        result = await self.send_command(AircraftChannels.TAKEOFF, ControlValues.MAX)
        if result:
            self.altitude = target_height
            await asyncio.sleep(3)  # 等待起飞稳定
        return result
    
    async def land(self) -> bool:
        """降落"""
        logger.info("[无人机] 执行降落")
        result = await self.send_command(AircraftChannels.LAND, ControlValues.MAX)
        if result:
            self.altitude = 0.0
        return result
    
    async def hover(self) -> bool:
        """悬停"""
        logger.debug("[无人机] 执行悬停")
        # 将所有控制通道设置为中值
        for channel in [AircraftChannels.DIRECTION, 
                       AircraftChannels.THROTTLE,
                       AircraftChannels.MOVEMENT]:
            await self.send_command(channel, ControlValues.MID)
        return True
    
    async def move_forward(self, duration: float, speed: float = 0.5) -> bool:
        """前进"""
        logger.info(f"[无人机] 前进 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID + speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.THROTTLE, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def move_backward(self, duration: float, speed: float = 0.5) -> bool:
        """后退"""
        logger.info(f"[无人机] 后退 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID - speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.THROTTLE, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def move_left(self, duration: float, speed: float = 0.5) -> bool:
        """左移"""
        logger.info(f"[无人机] 左移 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID - speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.MOVEMENT, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def move_right(self, duration: float, speed: float = 0.5) -> bool:
        """右移"""
        logger.info(f"[无人机] 右移 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID + speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.MOVEMENT, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def turn_left(self, duration: float, speed: float = 0.5) -> bool:
        """左转"""
        logger.info(f"[无人机] 左转 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID - speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.DIRECTION, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def turn_right(self, duration: float, speed: float = 0.5) -> bool:
        """右转"""
        logger.info(f"[无人机] 右转 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID + speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.DIRECTION, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def ascend(self, duration: float, speed: float = 0.5) -> bool:
        """上升"""
        logger.info(f"[无人机] 上升 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID + speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.ALTITUDE, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def descend(self, duration: float, speed: float = 0.5) -> bool:
        """下降"""
        logger.info(f"[无人机] 下降 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID - speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.ALTITUDE, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def gimbal_pitch_up(self, duration: float) -> bool:
        """云台上仰"""
        logger.info(f"[无人机] 云台上仰 {duration}秒")
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.GIMBAL_PITCH, ControlValues.MAX)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def gimbal_pitch_down(self, duration: float) -> bool:
        """云台下俯"""
        logger.info(f"[无人机] 云台下俯 {duration}秒")
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(AircraftChannels.GIMBAL_PITCH, ControlValues.MIN)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def gimbal_reset(self) -> bool:
        """云台复位"""
        logger.info("[无人机] 云台复位")
        return await self.send_command(AircraftChannels.GIMBAL_RESET, ControlValues.MAX)
    
    async def return_home(self) -> bool:
        """返航"""
        logger.info("[无人机] 执行返航")
        return await self.send_command(AircraftChannels.BACK, ControlValues.MAX)


class VehicleController(DeviceController):
    """无人车控制器"""
    
    def __init__(self, websocket_client=None):
        super().__init__('vehicle', websocket_client)
    
    async def move_forward(self, duration: float, speed: float = 0.5) -> bool:
        """前进"""
        logger.info(f"[无人车] 前进 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID + speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(VehicleChannels.THROTTLE, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def move_backward(self, duration: float, speed: float = 0.5) -> bool:
        """后退"""
        logger.info(f"[无人车] 后退 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID - speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(VehicleChannels.THROTTLE, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def turn_left(self, duration: float, speed: float = 0.5) -> bool:
        """左转"""
        logger.info(f"[无人车] 左转 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID - speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(VehicleChannels.DIRECTION, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def turn_right(self, duration: float, speed: float = 0.5) -> bool:
        """右转"""
        logger.info(f"[无人车] 右转 {duration}秒，速度系数: {speed}")
        value = int(ControlValues.MID + speed * 1000)
        start_time = time.time()
        while time.time() - start_time < duration:
            await self.send_command(VehicleChannels.DIRECTION, value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        return True
    
    async def stop(self) -> bool:
        """停车"""
        logger.info("[无人车] 停车")
        await self.send_command(VehicleChannels.THROTTLE, ControlValues.MID)
        await self.send_command(VehicleChannels.DIRECTION, ControlValues.MID)
        return True


class ControllerManager:
    """控制器管理器"""
    
    def __init__(self):
        self.aircraft: Optional[AircraftController] = None
        self.vehicle: Optional[VehicleController] = None
    
    def set_websocket_client(self, websocket_client):
        """设置WebSocket客户端"""
        if self.aircraft:
            self.aircraft.websocket_client = websocket_client
        if self.vehicle:
            self.vehicle.websocket_client = websocket_client
    
    def create_controllers(self, websocket_client=None):
        """创建控制器实例"""
        self.aircraft = AircraftController(websocket_client)
        self.vehicle = VehicleController(websocket_client)
        logger.info("控制器管理器初始化完成")
    
    async def sync_forward(self, duration: float, aircraft_speed: float = 0.2, 
                          vehicle_speed: float = 0.3) -> bool:
        """无人机和无人车同步前进"""
        logger.info(f"[协同] 同步前进 {duration}秒")
        
        aircraft_value = int(ControlValues.MID + aircraft_speed * 1000)
        vehicle_value = int(ControlValues.MID + vehicle_speed * 1000)
        
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.aircraft:
                await self.aircraft.send_command(AircraftChannels.THROTTLE, aircraft_value)
            if self.vehicle:
                await self.vehicle.send_command(VehicleChannels.THROTTLE, vehicle_value)
            await asyncio.sleep(ControlValues.MIN_INTERVAL)
        
        return True
    
    async def emergency_stop(self):
        """紧急停止所有设备"""
        logger.warning("[控制器] 执行紧急停止")
        if self.aircraft:
            await self.aircraft.hover()
        if self.vehicle:
            await self.vehicle.stop()
