"""
局部路径规划模块

使用动态窗口法（DWA）实现实时避障与路径调整。
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from loguru import logger

from config.constants import PlanningConstants, MotionLimits


@dataclass
class RobotState:
    """机器人状态"""
    x: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    v: float = 0.0      # 线速度
    omega: float = 0.0  # 角速度


@dataclass
class Trajectory:
    """轨迹"""
    positions: List[Tuple[float, float]]
    velocities: List[Tuple[float, float]]
    cost: float


class DynamicWindowApproach:
    """动态窗口法避障器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 机器人参数
        self.max_speed = self.config.get('max_speed', PlanningConstants.DWA_MAX_SPEED)
        self.max_angular_speed = self.config.get('max_angular_speed', 
                                                  PlanningConstants.DWA_MAX_ANGULAR_SPEED)
        self.acceleration = MotionLimits.VEHICLE_ACCELERATION
        self.deceleration = MotionLimits.VEHICLE_DECELERATION
        self.angular_acceleration = 2.0  # 角加速度限制
        
        # 采样参数
        self.velocity_samples = self.config.get('velocity_samples', 
                                               PlanningConstants.DWA_VELOCITY_SAMPLES)
        self.angular_samples = self.config.get('angular_samples', 
                                              PlanningConstants.DWA_ANGULAR_SAMPLES)
        
        # 预测参数
        self.prediction_time = self.config.get('prediction_time', 
                                              PlanningConstants.DWA_PREDICTION_TIME)
        self.dt = 0.1  # 时间步长
        
        # 安全距离
        self.safe_distance = self.config.get('safe_distance', 
                                            PlanningConstants.DWA_SAFE_DISTANCE)
        
        # 评价函数权重
        self.weight_heading = 0.5
        self.weight_obstacle = 0.3
        self.weight_velocity = 0.2
        
        # 障碍物
        self.obstacles: List[Tuple[float, float]] = []
    
    def calculate_dynamic_window(self, state: RobotState) -> Tuple[float, float, float, float]:
        """计算动态窗口"""
        # 速度限制
        v_min = max(-self.max_speed, state.v - self.acceleration * self.dt)
        v_max = min(self.max_speed, state.v + self.acceleration * self.dt)
        
        # 角速度限制
        omega_min = max(-self.max_angular_speed, 
                       state.omega - self.angular_acceleration * self.dt)
        omega_max = min(self.max_angular_speed, 
                       state.omega + self.angular_acceleration * self.dt)
        
        return v_min, v_max, omega_min, omega_max
    
    def predict_trajectory(self, state: RobotState, v: float, 
                          omega: float) -> Trajectory:
        """预测轨迹"""
        positions = [(state.x, state.z)]
        velocities = [(v, omega)]
        
        x, z, yaw = state.x, state.z, state.yaw
        
        # 模拟运动
        steps = int(self.prediction_time / self.dt)
        for _ in range(steps):
            # 更新位姿
            x += v * math.cos(yaw) * self.dt
            z += v * math.sin(yaw) * self.dt
            yaw += omega * self.dt
            
            positions.append((x, z))
            velocities.append((v, omega))
        
        # 计算代价
        cost = self.calculate_cost(state, positions, v, omega)
        
        return Trajectory(positions, velocities, cost)
    
    def calculate_cost(self, state: RobotState, positions: List[Tuple[float, float]],
                      v: float, omega: float) -> float:
        """计算轨迹代价"""
        # 目标朝向代价（使机器人朝向目标）
        heading_cost = self.calculate_heading_cost(state, positions[-1])
        
        # 避障代价（与障碍物的距离）
        obstacle_cost = self.calculate_obstacle_cost(positions)
        
        # 速度代价（鼓励高速运动）
        velocity_cost = self.max_speed - abs(v)
        
        # 总代价
        total_cost = (self.weight_heading * heading_cost +
                     self.weight_obstacle * obstacle_cost +
                     self.weight_velocity * velocity_cost)
        
        return total_cost
    
    def calculate_heading_cost(self, state: RobotState, 
                              end_pos: Tuple[float, float]) -> float:
        """计算朝向代价"""
        # 计算目标方向
        dx = end_pos[0] - state.x
        dz = end_pos[1] - state.z
        target_yaw = math.atan2(dz, dx)
        
        # 计算角度差
        diff = target_yaw - state.yaw
        # 归一化到[-pi, pi]
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        
        return abs(diff)
    
    def calculate_obstacle_cost(self, positions: List[Tuple[float, float]]) -> float:
        """计算避障代价"""
        if not self.obstacles:
            return 0.0
        
        min_distance = float('inf')
        
        for pos in positions:
            for obs in self.obstacles:
                dx = pos[0] - obs[0]
                dz = pos[1] - obs[1]
                distance = math.sqrt(dx*dx + dz*dz)
                min_distance = min(min_distance, distance)
        
        if min_distance < self.safe_distance:
            # 距离太近，代价极高
            return 1000.0
        else:
            # 距离越远代价越低
            return 1.0 / min_distance
    
    def plan(self, state: RobotState, 
            goal: Tuple[float, float]) -> Tuple[float, float]:
        """规划速度指令"""
        # 计算动态窗口
        v_min, v_max, omega_min, omega_max = self.calculate_dynamic_window(state)
        
        # 采样速度空间
        best_cost = float('inf')
        best_v = 0.0
        best_omega = 0.0
        
        vs = np.linspace(v_min, v_max, self.velocity_samples)
        omegas = np.linspace(omega_min, omega_max, self.angular_samples)
        
        for v in vs:
            for omega in omegas:
                # 预测轨迹
                trajectory = self.predict_trajectory(state, v, omega)
                
                # 检查是否与障碍物碰撞
                if self.check_collision(trajectory):
                    continue
                
                # 选择代价最小的轨迹
                if trajectory.cost < best_cost:
                    best_cost = trajectory.cost
                    best_v = v
                    best_omega = omega
        
        return best_v, best_omega
    
    def check_collision(self, trajectory: Trajectory) -> bool:
        """检查轨迹是否与障碍物碰撞"""
        if not self.obstacles:
            return False
        
        for pos in trajectory.positions:
            for obs in self.obstacles:
                dx = pos[0] - obs[0]
                dz = pos[1] - obs[1]
                distance = math.sqrt(dx*dx + dz*dz)
                
                if distance < self.safe_distance * 0.5:
                    return True
        
        return False
    
    def update_obstacles(self, obstacles: List[Tuple[float, float]]):
        """更新障碍物列表"""
        self.obstacles = obstacles


class LocalPlanner:
    """局部规划器"""
    
    def __init__(self):
        self.dwa = DynamicWindowApproach()
        
        # 当前状态
        self.current_state = RobotState()
        
        # 目标航点
        self.current_waypoint: Optional[Tuple[float, float]] = None
        self.waypoint_index = 0
        self.waypoints: List[Tuple[float, float]] = []
        
        # 到达阈值
        self.reached_threshold = 0.3  # 米
    
    def set_waypoints(self, waypoints: List[Tuple[float, float]]):
        """设置航点序列"""
        self.waypoints = waypoints
        self.waypoint_index = 0
        if waypoints:
            self.current_waypoint = waypoints[0]
        logger.info(f"局部规划器设置{len(waypoints)}个航点")
    
    def update_state(self, x: float, z: float, yaw: float, 
                    v: float = 0.0, omega: float = 0.0):
        """更新当前状态"""
        self.current_state = RobotState(x, z, yaw, v, omega)
    
    def update_obstacles(self, obstacles: List[Tuple[float, float]]):
        """更新障碍物"""
        self.dwa.update_obstacles(obstacles)
    
    def step(self) -> Tuple[float, float, bool]:
        """执行一步规划，返回(速度, 角速度, 是否到达终点)"""
        if not self.current_waypoint:
            return 0.0, 0.0, True
        
        # 检查是否到达当前航点
        dx = self.current_waypoint[0] - self.current_state.x
        dz = self.current_waypoint[1] - self.current_state.z
        distance = math.sqrt(dx*dx + dz*dz)
        
        if distance < self.reached_threshold:
            # 到达当前航点，切换到下一个
            self.waypoint_index += 1
            if self.waypoint_index >= len(self.waypoints):
                # 到达终点
                return 0.0, 0.0, True
            else:
                self.current_waypoint = self.waypoints[self.waypoint_index]
                logger.info(f"到达航点{self.waypoint_index-1}, 前往航点{self.waypoint_index}")
        
        # 使用DWA规划
        v, omega = self.dwa.plan(self.current_state, self.current_waypoint)
        
        return v, omega, False
    
    def has_reached_goal(self) -> bool:
        """检查是否到达终点"""
        if not self.waypoints or self.waypoint_index >= len(self.waypoints):
            return True
        return False
    
    def get_progress(self) -> float:
        """获取进度（0.0 ~ 1.0）"""
        if not self.waypoints:
            return 1.0
        return self.waypoint_index / len(self.waypoints)
