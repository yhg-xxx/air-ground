"""
运动控制器模块

负责无人机和无人车的运动控制，将规划路径转换为具体控制指令。
"""

import math
import asyncio
from typing import Tuple, Optional, List
from dataclasses import dataclass
from loguru import logger

from config.constants import (
    AircraftChannels, VehicleChannels, ControlValues,
    MotionLimits, CoordinateConstants
)
from control.pid_controller import PIDController, PIDConfig, PIDControllerSet


@dataclass
class MotionState:
    """运动状态"""
    x: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    altitude: float = 0.0
    linear_velocity: float = 0.0
    angular_velocity: float = 0.0


class BaseMotionController:
    """运动控制器基类"""
    
    def __init__(self, send_command_func=None):
        self.send_command = send_command_func
        
        # 当前状态
        self.state = MotionState()
        
        # 目标状态
        self.target_position: Optional[Tuple[float, float]] = None
        self.target_yaw: Optional[float] = None
        self.target_altitude: Optional[float] = None
        
        # PID控制器集合
        self.pid_set = PIDControllerSet()
        
        # 到达容差
        self.position_tolerance = 0.3  # 米
        self.yaw_tolerance = 0.1  # 弧度
        self.altitude_tolerance = 0.2  # 米
        
        # 控制频率
        self.control_frequency = 10.0  # Hz
        self.dt = 1.0 / self.control_frequency
    
    def update_state(self, state: MotionState):
        """更新当前状态"""
        self.state = state
    
    def update_position(self, x: float, z: float):
        """更新位置"""
        self.state.x = x
        self.state.z = z
    
    def update_attitude(self, yaw: float, altitude: Optional[float] = None):
        """更新姿态"""
        self.state.yaw = yaw
        if altitude is not None:
            self.state.altitude = altitude
    
    def set_target(self, position: Optional[Tuple[float, float]] = None,
                  yaw: Optional[float] = None,
                  altitude: Optional[float] = None):
        """设置目标"""
        if position:
            self.target_position = position
        if yaw is not None:
            self.target_yaw = yaw
        if altitude is not None:
            self.target_altitude = altitude
    
    def calculate_distance_to_target(self) -> float:
        """计算到目标的距离"""
        if not self.target_position:
            return float('inf')
        
        dx = self.target_position[0] - self.state.x
        dz = self.target_position[1] - self.state.z
        return math.sqrt(dx*dx + dz*dz)
    
    def calculate_angle_to_target(self) -> float:
        """计算到目标的角度"""
        if not self.target_position:
            return 0.0
        
        dx = self.target_position[0] - self.state.x
        dz = self.target_position[1] - self.state.z
        return math.atan2(dz, dx)
    
    def has_reached_position(self) -> bool:
        """检查是否到达位置目标"""
        return self.calculate_distance_to_target() < self.position_tolerance
    
    def has_reached_yaw(self) -> bool:
        """检查是否到达朝向目标"""
        if self.target_yaw is None:
            return True
        
        diff = abs(self.target_yaw - self.state.yaw)
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        
        return abs(diff) < self.yaw_tolerance
    
    def reset(self):
        """重置控制器"""
        self.pid_set.reset_all()
        self.target_position = None
        self.target_yaw = None
        self.target_altitude = None


class AircraftMotionController(BaseMotionController):
    """无人机运动控制器"""
    
    def __init__(self, send_command_func=None):
        super().__init__(send_command_func)
        
        # 初始化PID控制器
        self.pid_set.add_controller('x', PIDConfig(kp=1.0, ki=0.1, kd=0.5))
        self.pid_set.add_controller('z', PIDConfig(kp=1.0, ki=0.1, kd=0.5))
        self.pid_set.add_controller('yaw', PIDConfig(kp=2.0, ki=0.2, kd=1.0))
        self.pid_set.add_controller('altitude', PIDConfig(kp=1.5, ki=0.1, kd=0.3))
        
        # 最大速度限制
        self.max_horizontal_speed = MotionLimits.AIRCRAFT_MAX_SPEED
        self.max_vertical_speed = 2.0
        self.max_yaw_rate = 1.0
    
    async def control_step(self) -> Tuple[bool, dict]:
        """执行一步控制"""
        commands = {}
        reached = True
        
        # 位置控制
        if self.target_position:
            if not self.has_reached_position():
                reached = False
                
                # 计算到目标的角度
                target_angle = self.calculate_angle_to_target()
                
                # 计算距离
                distance = self.calculate_distance_to_target()
                
                # 计算朝向误差
                yaw_error = target_angle - self.state.yaw
                while yaw_error > math.pi:
                    yaw_error -= 2 * math.pi
                while yaw_error < -math.pi:
                    yaw_error += 2 * math.pi
                
                # 如果朝向误差较大，先调整朝向
                if abs(yaw_error) > 0.3:  # 约17度
                    # 偏航控制
                    yaw_pid = self.pid_set.get_controller('yaw')
                    yaw_pid.set_setpoint(target_angle)
                    yaw_output = yaw_pid.compute(self.state.yaw, self.dt)
                    
                    yaw_value = int(ControlValues.MID + yaw_output * 500)
                    yaw_value = max(ControlValues.MIN, min(ControlValues.MAX, yaw_value))
                    commands[AircraftChannels.DIRECTION] = yaw_value
                else:
                    # 前进控制
                    forward_speed = min(distance * 0.5, self.max_horizontal_speed)
                    forward_value = int(ControlValues.MID + forward_speed * 100)
                    commands[AircraftChannels.THROTTLE] = forward_value
                    
                    # 侧移控制（如果有横向偏差）
                    dx = self.target_position[0] - self.state.x
                    dz = self.target_position[1] - self.state.z
                    
                    # 计算横向距离（垂直于朝向方向）
                    lateral_dist = dx * math.sin(self.state.yaw) - dz * math.cos(self.state.yaw)
                    
                    if abs(lateral_dist) > 0.2:
                        lateral_speed = max(-self.max_horizontal_speed, 
                                          min(self.max_horizontal_speed, lateral_dist * 0.5))
                        lateral_value = int(ControlValues.MID + lateral_speed * 100)
                        commands[AircraftChannels.MOVEMENT] = lateral_value
        
        # 高度控制
        if self.target_altitude is not None:
            altitude_error = abs(self.target_altitude - self.state.altitude)
            if altitude_error > self.altitude_tolerance:
                reached = False
                
                altitude_pid = self.pid_set.get_controller('altitude')
                altitude_pid.set_setpoint(self.target_altitude)
                altitude_output = altitude_pid.compute(self.state.altitude, self.dt)
                
                altitude_value = int(ControlValues.MID + altitude_output * 500)
                altitude_value = max(ControlValues.MIN, min(ControlValues.MAX, altitude_value))
                commands[AircraftChannels.ALTITUDE] = altitude_value
        
        # 发送控制指令
        if self.send_command:
            for channel, value in commands.items():
                await self.send_command('aircraft', channel, value)
                await asyncio.sleep(0.01)
        
        return reached, commands
    
    async def navigate_to(self, target: Tuple[float, float], 
                         timeout: float = 60.0) -> bool:
        """导航到目标位置"""
        logger.info(f"[无人机运动控制] 导航到 {target}")
        
        self.set_target(position=target)
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            reached, _ = await self.control_step()
            
            if reached:
                logger.info("[无人机运动控制] 到达目标")
                return True
            
            await asyncio.sleep(self.dt)
        
        logger.warning("[无人机运动控制] 导航超时")
        return False
    
    async def hover_at(self, position: Tuple[float, float], 
                      altitude: float, duration: float):
        """在指定位置悬停"""
        logger.info(f"[无人机运动控制] 悬停 {duration}秒")
        
        self.set_target(position=position, altitude=altitude)
        
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < duration:
            await self.control_step()
            await asyncio.sleep(self.dt)


class VehicleMotionController(BaseMotionController):
    """无人车运动控制器"""
    
    def __init__(self, send_command_func=None):
        super().__init__(send_command_func)
        
        # 初始化PID控制器
        self.pid_set.add_controller('linear', PIDConfig(kp=1.5, ki=0.1, kd=0.3))
        self.pid_set.add_controller('angular', PIDConfig(kp=2.0, ki=0.0, kd=0.5))
        
        # 最大速度限制
        self.max_linear_speed = MotionLimits.VEHICLE_MAX_SPEED
        self.max_angular_speed = MotionLimits.VEHICLE_MAX_ANGULAR_SPEED
    
    async def control_step(self) -> Tuple[bool, dict]:
        """执行一步控制"""
        commands = {}
        reached = True
        
        if not self.target_position:
            return True, commands
        
        # 计算到目标的角度
        target_angle = self.calculate_angle_to_target()
        
        # 计算朝向误差
        yaw_error = target_angle - self.state.yaw
        while yaw_error > math.pi:
            yaw_error -= 2 * math.pi
        while yaw_error < -math.pi:
            yaw_error += 2 * math.pi
        
        # 计算距离
        distance = self.calculate_distance_to_target()
        
        if distance < self.position_tolerance:
            # 到达目标
            if self.send_command:
                await self.send_command('vehicle', VehicleChannels.THROTTLE, ControlValues.MID)
                await self.send_command('vehicle', VehicleChannels.DIRECTION, ControlValues.MID)
            return True, commands
        
        reached = False
        
        # 判断是否需要先转向
        if abs(yaw_error) > 0.5:  # 约28度
            # 原地转向
            angular_pid = self.pid_set.get_controller('angular')
            angular_pid.set_setpoint(0.0)  # 目标是消除误差
            angular_output = angular_pid.compute(-yaw_error, self.dt)
            
            direction_value = int(ControlValues.MID + angular_output * 500)
            direction_value = max(ControlValues.MIN, min(ControlValues.MAX, direction_value))
            
            commands[VehicleChannels.DIRECTION] = direction_value
            commands[VehicleChannels.THROTTLE] = ControlValues.MID  # 停止前进
        else:
            # 前进并微调转向
            linear_pid = self.pid_set.get_controller('linear')
            linear_pid.set_setpoint(0.0)  # 目标是消除距离
            linear_output = linear_pid.compute(-distance, self.dt)
            
            # 计算前进速度
            forward_speed = max(-self.max_linear_speed,
                              min(self.max_linear_speed, linear_output))
            throttle_value = int(ControlValues.MID + forward_speed * 300)
            throttle_value = max(ControlValues.MIN, min(ControlValues.MAX, throttle_value))
            
            # 计算转向
            angular_output = yaw_error * 2.0  # 简单的比例控制
            direction_value = int(ControlValues.MID + angular_output * 500)
            direction_value = max(ControlValues.MIN, min(ControlValues.MAX, direction_value))
            
            commands[VehicleChannels.THROTTLE] = throttle_value
            commands[VehicleChannels.DIRECTION] = direction_value
        
        # 发送控制指令
        if self.send_command:
            for channel, value in commands.items():
                await self.send_command('vehicle', channel, value)
                await asyncio.sleep(0.01)
        
        return reached, commands
    
    async def navigate_to(self, target: Tuple[float, float], 
                         timeout: float = 60.0) -> bool:
        """导航到目标位置"""
        logger.info(f"[无人车运动控制] 导航到 {target}")
        
        self.set_target(position=target)
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            reached, _ = await self.control_step()
            
            if reached:
                logger.info("[无人车运动控制] 到达目标")
                return True
            
            await asyncio.sleep(self.dt)
        
        logger.warning("[无人车运动控制] 导航超时")
        return False
    
    async def follow_path(self, path: List[Tuple[float, float]], 
                         timeout: float = 120.0) -> bool:
        """跟随路径"""
        logger.info(f"[无人车运动控制] 跟随路径，共{len(path)}个点")
        
        start_time = asyncio.get_event_loop().time()
        waypoint_index = 0
        
        while waypoint_index < len(path):
            if (asyncio.get_event_loop().time() - start_time) > timeout:
                logger.warning("[无人车运动控制] 路径跟随超时")
                return False
            
            # 设置当前目标
            self.set_target(position=path[waypoint_index])
            
            # 控制
            reached, _ = await self.control_step()
            
            if reached:
                waypoint_index += 1
                logger.info(f"[无人车运动控制] 到达航点 {waypoint_index}/{len(path)}")
            
            await asyncio.sleep(self.dt)
        
        logger.info("[无人车运动控制] 路径跟随完成")
        return True
