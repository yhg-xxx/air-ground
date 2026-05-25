"""
仿真器模块

提供简单的物理仿真环境，用于测试算法。
"""

import numpy as np
import math
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass


@dataclass
class RobotKinematics:
    """机器人运动学参数"""
    x: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    v: float = 0.0  # 线速度
    omega: float = 0.0  # 角速度


class SimpleSimulator:
    """简单仿真器"""
    
    def __init__(self, dt: float = 0.1):
        self.dt = dt
        
        # 无人机状态
        self.aircraft = RobotKinematics()
        self.aircraft_altitude = 0.0
        
        # 无人车状态
        self.vehicle = RobotKinematics()
        
        # 时间
        self.time = 0.0
        
        # 历史记录
        self.aircraft_history = []
        self.vehicle_history = []
    
    def update_aircraft(self, linear_cmd: float, angular_cmd: float, 
                       altitude_cmd: float):
        """更新无人机状态"""
        # 简单的运动学模型
        max_speed = 5.0
        max_altitude_speed = 2.0
        
        # 速度平滑
        target_v = linear_cmd * max_speed
        target_omega = angular_cmd * 1.0
        target_altitude_v = altitude_cmd * max_altitude_speed
        
        # 更新速度
        self.aircraft.v += (target_v - self.aircraft.v) * 0.1
        self.aircraft.omega += (target_omega - self.aircraft.omega) * 0.1
        
        # 更新位置
        self.aircraft.x += self.aircraft.v * math.cos(self.aircraft.yaw) * self.dt
        self.aircraft.z += self.aircraft.v * math.sin(self.aircraft.yaw) * self.dt
        self.aircraft.yaw += self.aircraft.omega * self.dt
        
        # 归一化角度
        while self.aircraft.yaw > math.pi:
            self.aircraft.yaw -= 2 * math.pi
        while self.aircraft.yaw < -math.pi:
            self.aircraft.yaw += 2 * math.pi
        
        # 更新高度
        self.aircraft_altitude += target_altitude_v * self.dt
        self.aircraft_altitude = max(0, min(15, self.aircraft_altitude))
        
        # 记录历史
        self.aircraft_history.append({
            'time': self.time,
            'x': self.aircraft.x,
            'z': self.aircraft.z,
            'yaw': self.aircraft.yaw,
            'altitude': self.aircraft_altitude
        })
    
    def update_vehicle(self, linear_cmd: float, angular_cmd: float):
        """更新无人车状态"""
        # 差速模型
        max_speed = 3.0
        
        target_v = linear_cmd * max_speed
        target_omega = angular_cmd * 1.5
        
        # 速度平滑
        self.vehicle.v += (target_v - self.vehicle.v) * 0.2
        self.vehicle.omega += (target_omega - self.vehicle.omega) * 0.2
        
        # 更新位置
        self.vehicle.x += self.vehicle.v * math.cos(self.vehicle.yaw) * self.dt
        self.vehicle.z += self.vehicle.v * math.sin(self.vehicle.yaw) * self.dt
        self.vehicle.yaw += self.vehicle.omega * self.dt
        
        # 归一化角度
        while self.vehicle.yaw > math.pi:
            self.vehicle.yaw -= 2 * math.pi
        while self.vehicle.yaw < -math.pi:
            self.vehicle.yaw += 2 * math.pi
        
        # 记录历史
        self.vehicle_history.append({
            'time': self.time,
            'x': self.vehicle.x,
            'z': self.vehicle.z,
            'yaw': self.vehicle.yaw
        })
    
    def step(self, commands: Dict):
        """执行一步仿真"""
        # 处理无人机指令
        if 'aircraft' in commands:
            cmd = commands['aircraft']
            self.update_aircraft(
                cmd.get('linear', 0.0),
                cmd.get('angular', 0.0),
                cmd.get('altitude', 0.0)
            )
        
        # 处理无人车指令
        if 'vehicle' in commands:
            cmd = commands['vehicle']
            self.update_vehicle(
                cmd.get('linear', 0.0),
                cmd.get('angular', 0.0)
            )
        
        self.time += self.dt
    
    def get_aircraft_state(self) -> Dict:
        """获取无人机状态"""
        return {
            'x': self.aircraft.x,
            'z': self.aircraft.z,
            'yaw': self.aircraft.yaw,
            'altitude': self.aircraft_altitude,
            'v': self.aircraft.v,
            'omega': self.aircraft.omega
        }
    
    def get_vehicle_state(self) -> Dict:
        """获取无人车状态"""
        return {
            'x': self.vehicle.x,
            'z': self.vehicle.z,
            'yaw': self.vehicle.yaw,
            'v': self.vehicle.v,
            'omega': self.vehicle.omega
        }
    
    def reset(self):
        """重置仿真器"""
        self.aircraft = RobotKinematics()
        self.aircraft_altitude = 0.0
        self.vehicle = RobotKinematics()
        self.time = 0.0
        self.aircraft_history.clear()
        self.vehicle_history.clear()


class MazeSimulator:
    """迷宫仿真器"""
    
    def __init__(self, width: int = 480, height: int = 1200):
        self.width = width
        self.height = height
        
        # 迷宫地图
        self.grid = np.zeros((height, width), dtype=np.uint8)
        
        # 生成简单迷宫
        self._generate_simple_maze()
    
    def _generate_simple_maze(self):
        """生成简单迷宫"""
        # 设置边界
        self.grid[0, :] = 2  # 上边界
        self.grid[-1, :] = 2  # 下边界
        self.grid[:, 0] = 2  # 左边界
        self.grid[:, -1] = 2  # 右边界
        
        # 添加一些障碍物
        for i in range(100, 1000, 100):
            if i % 200 == 0:
                self.grid[i:i+20, 100:200] = 2
            else:
                self.grid[i:i+20, 300:400] = 2
    
    def is_collision(self, x: float, z: float, 
                    cell_size: float = 0.052) -> bool:
        """检查碰撞"""
        grid_x = int(x / cell_size)
        grid_z = int(z / cell_size)
        
        if 0 <= grid_x < self.width and 0 <= grid_z < self.height:
            return self.grid[grid_z, grid_x] == 2
        
        return True  # 边界外视为碰撞
    
    def get_grid(self) -> np.ndarray:
        """获取栅格地图"""
        return self.grid.copy()


class SensorSimulator:
    """传感器仿真器"""
    
    def __init__(self, noise_level: float = 0.01):
        self.noise_level = noise_level
    
    def get_gps_position(self, true_position: Tuple[float, float]) -> Tuple[float, float]:
        """获取GPS位置（带噪声）"""
        noise_x = np.random.normal(0, self.noise_level)
        noise_z = np.random.normal(0, self.noise_level)
        
        return (true_position[0] + noise_x, true_position[1] + noise_z)
    
    def get_imu_attitude(self, true_yaw: float) -> float:
        """获取IMU姿态（带噪声）"""
        noise = np.random.normal(0, self.noise_level * 0.1)
        return true_yaw + noise
    
    def get_power_level(self, true_level: float) -> float:
        """获取电量（带噪声）"""
        noise = np.random.normal(0, 0.5)
        return max(0, min(100, true_level + noise))
