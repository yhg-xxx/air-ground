"""
安全监控器模块

负责监控系统安全状态，实现多级安全监控与故障恢复。
"""

import asyncio
import time
from typing import Dict, Optional, List, Callable, Any
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from config.constants import SafetyConstants, MissionStages


class SafetyLevel(Enum):
    """安全等级枚举"""
    NORMAL = "normal"      # 正常
    WARNING = "warning"    # 警告
    CRITICAL = "critical"  # 严重
    EMERGENCY = "emergency" # 紧急


@dataclass
class SafetyEvent:
    """安全事件"""
    level: SafetyLevel
    source: str
    message: str
    timestamp: float
    data: Optional[Dict] = None


class SafetyMonitor:
    """安全监控器"""
    
    def __init__(self, controller_manager=None):
        self.controller_manager = controller_manager
        
        # 监控状态
        self.monitoring = False
        self.monitor_task = None
        
        # 设备状态缓存
        self.device_status = {
            'aircraft': {
                'position': [0.0, 0.0],
                'altitude': 0.0,
                'power': 100,
                'voltage': 0.0,
                'last_update': 0
            },
            'vehicle': {
                'position': [0.0, 0.0],
                'power': 100,
                'voltage': 0.0,
                'last_update': 0
            }
        }
        
        # 安全阈值
        self.thresholds = {
            'power_warning': SafetyConstants.POWER_WARNING,
            'power_critical': SafetyConstants.POWER_CRITICAL,
            'power_return': SafetyConstants.POWER_RETURN,
            'boundary_min_x': SafetyConstants.BOUNDARY_MIN_X,
            'boundary_max_x': SafetyConstants.BOUNDARY_MAX_X,
            'boundary_min_z': SafetyConstants.BOUNDARY_MIN_Z,
            'boundary_max_z': SafetyConstants.BOUNDARY_MAX_Z,
            'safe_distance': SafetyConstants.SAFE_DISTANCE,
            'emergency_distance': SafetyConstants.EMERGENCY_DISTANCE,
            'mission_timeout': SafetyConstants.MISSION_TIMEOUT,
            'stage_timeout': SafetyConstants.STAGE_TIMEOUT
        }
        
        # 事件记录
        self.events: List[SafetyEvent] = []
        self.max_events = 100
        
        # 回调函数
        self.alert_callbacks: List[Callable] = []
        self.emergency_callbacks: List[Callable] = []
    
    def register_alert_callback(self, callback: Callable):
        """注册告警回调"""
        self.alert_callbacks.append(callback)
        logger.debug("注册安全告警回调")
    
    def register_emergency_callback(self, callback: Callable):
        """注册紧急回调"""
        self.emergency_callbacks.append(callback)
        logger.debug("注册紧急停止回调")
    
    def update_device_status(self, device_type: str, status: Dict):
        """更新设备状态"""
        if device_type in self.device_status:
            self.device_status[device_type].update(status)
            self.device_status[device_type]['last_update'] = time.time()
    
    async def start_monitoring(self, interval: float = 1.0):
        """启动安全监控"""
        if self.monitoring:
            logger.warning("安全监控已在运行")
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info("安全监控已启动")
    
    async def stop_monitoring(self):
        """停止安全监控"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("安全监控已停止")
    
    async def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.monitoring:
            try:
                await self._check_safety()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"安全监控异常: {e}")
                await asyncio.sleep(interval)
    
    async def _check_safety(self):
        """执行安全检查"""
        # 检查电量
        await self._check_power()
        
        # 检查边界
        await self._check_boundary()
        
        # 检查通信超时
        await self._check_communication()
    
    async def _check_power(self):
        """检查电量"""
        for device_type, status in self.device_status.items():
            power = status.get('power', 100)
            
            if power <= self.thresholds['power_critical']:
                # 严重低电量
                event = SafetyEvent(
                    level=SafetyLevel.EMERGENCY,
                    source=device_type,
                    message=f"电量严重不足: {power}%",
                    timestamp=time.time()
                )
                self._add_event(event)
                await self._trigger_emergency(f"{device_type}电量严重不足")
                
            elif power <= self.thresholds['power_return']:
                # 需要返航
                event = SafetyEvent(
                    level=SafetyLevel.CRITICAL,
                    source=device_type,
                    message=f"电量低，需要返航: {power}%",
                    timestamp=time.time()
                )
                self._add_event(event)
                await self._trigger_alert(event)
                
                # 触发返航
                if device_type == 'aircraft' and self.controller_manager:
                    if self.controller_manager.aircraft:
                        await self.controller_manager.aircraft.return_home()
                
            elif power <= self.thresholds['power_warning']:
                # 电量警告
                event = SafetyEvent(
                    level=SafetyLevel.WARNING,
                    source=device_type,
                    message=f"电量警告: {power}%",
                    timestamp=time.time()
                )
                self._add_event(event)
                await self._trigger_alert(event)
    
    async def _check_boundary(self):
        """检查边界"""
        for device_type, status in self.device_status.items():
            position = status.get('position', [0.0, 0.0])
            x, z = position[0], position[1]
            
            # 检查X边界
            if x < self.thresholds['boundary_min_x'] or x > self.thresholds['boundary_max_x']:
                event = SafetyEvent(
                    level=SafetyLevel.EMERGENCY,
                    source=device_type,
                    message=f"超出X边界: x={x:.2f}",
                    timestamp=time.time(),
                    data={'position': position}
                )
                self._add_event(event)
                await self._trigger_emergency(f"{device_type}超出安全边界")
            
            # 检查Z边界
            if z < self.thresholds['boundary_min_z'] or z > self.thresholds['boundary_max_z']:
                event = SafetyEvent(
                    level=SafetyLevel.EMERGENCY,
                    source=device_type,
                    message=f"超出Z边界: z={z:.2f}",
                    timestamp=time.time(),
                    data={'position': position}
                )
                self._add_event(event)
                await self._trigger_emergency(f"{device_type}超出安全边界")
    
    async def _check_communication(self):
        """检查通信状态"""
        current_time = time.time()
        timeout_threshold = 10.0  # 10秒超时
        
        for device_type, status in self.device_status.items():
            last_update = status.get('last_update', 0)
            if current_time - last_update > timeout_threshold:
                event = SafetyEvent(
                    level=SafetyLevel.CRITICAL,
                    source=device_type,
                    message=f"通信超时: {current_time - last_update:.1f}s",
                    timestamp=current_time
                )
                self._add_event(event)
                await self._trigger_alert(event)
    
    def _add_event(self, event: SafetyEvent):
        """添加安全事件"""
        self.events.append(event)
        
        # 限制事件数量
        if len(self.events) > self.max_events:
            self.events.pop(0)
        
        # 记录日志
        if event.level == SafetyLevel.WARNING:
            logger.warning(f"[安全事件] {event.source}: {event.message}")
        elif event.level in [SafetyLevel.CRITICAL, SafetyLevel.EMERGENCY]:
            logger.error(f"[安全事件] {event.source}: {event.message}")
    
    async def _trigger_alert(self, event: SafetyEvent):
        """触发告警"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
    
    async def _trigger_emergency(self, reason: str):
        """触发紧急停止"""
        logger.critical(f"[紧急停止] 原因: {reason}")
        
        # 执行紧急停止
        await self.emergency_stop()
        
        # 通知紧急回调
        for callback in self.emergency_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reason)
                else:
                    callback(reason)
            except Exception as e:
                logger.error(f"紧急回调执行失败: {e}")
    
    async def emergency_stop(self):
        """执行紧急停止"""
        logger.critical("[安全监控] 执行紧急停止")
        
        if self.controller_manager:
            await self.controller_manager.emergency_stop()
        
        # 添加紧急事件
        event = SafetyEvent(
            level=SafetyLevel.EMERGENCY,
            source='safety_monitor',
            message='紧急停止已执行',
            timestamp=time.time()
        )
        self._add_event(event)
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        recent_events = [e for e in self.events if time.time() - e.timestamp < 60]
        
        return {
            'monitoring': self.monitoring,
            'device_status': self.device_status,
            'recent_events': [
                {
                    'level': e.level.value,
                    'source': e.source,
                    'message': e.message,
                    'timestamp': e.timestamp
                }
                for e in recent_events[-10:]
            ]
        }
    
    def get_events(self, level: Optional[SafetyLevel] = None, 
                   limit: int = 50) -> List[SafetyEvent]:
        """获取安全事件"""
        events = self.events
        
        if level:
            events = [e for e in events if e.level == level]
        
        return events[-limit:]
    
    def clear_events(self):
        """清除事件记录"""
        self.events.clear()
        logger.info("安全事件记录已清除")
