"""
航点生成器模块

负责从全局路径生成可执行的航点序列。
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class Waypoint:
    """航点"""
    x: float
    z: float
    yaw: Optional[float] = None  # 期望朝向，None表示不指定
    speed: Optional[float] = None  # 期望速度，None表示使用默认值
    action: str = "move"  # 动作类型: move, hover, land, takeoff
    tolerance: float = 0.3  # 到达容差（米）


class WaypointGenerator:
    """航点生成器"""
    
    def __init__(self, spacing: float = 0.5, smoothing_factor: float = 0.5):
        """
        初始化
        
        Args:
            spacing: 航点间距（米）
            smoothing_factor: 平滑系数
        """
        self.spacing = spacing
        self.smoothing_factor = smoothing_factor
    
    def generate_from_path(self, path: List[Tuple[float, float]],
                         start_action: str = "move",
                         end_action: str = "hover") -> List[Waypoint]:
        """
        从路径生成航点
        
        Args:
            path: 路径点列表（世界坐标）
            start_action: 起始动作
            end_action: 结束动作
            
        Returns:
            航点列表
        """
        if len(path) < 2:
            logger.warning("路径点太少，无法生成航点")
            return []
        
        waypoints = []
        
        # 等距采样
        sampled_points = self._resample_path(path, self.spacing)
        
        # 为每个采样点生成航点
        for i, point in enumerate(sampled_points):
            # 计算期望朝向
            if i < len(sampled_points) - 1:
                next_point = sampled_points[i + 1]
                yaw = self._calculate_yaw(point, next_point)
            else:
                # 最后一个点，使用前一个朝向
                yaw = waypoints[-1].yaw if waypoints else 0.0
            
            # 确定动作
            if i == 0:
                action = start_action
            elif i == len(sampled_points) - 1:
                action = end_action
            else:
                action = "move"
            
            waypoint = Waypoint(
                x=point[0],
                z=point[1],
                yaw=yaw,
                speed=None,  # 使用默认速度
                action=action,
                tolerance=self.spacing * 0.5
            )
            
            waypoints.append(waypoint)
        
        logger.info(f"从{len(path)}个路径点生成{len(waypoints)}个航点")
        return waypoints
    
    def _resample_path(self, path: List[Tuple[float, float]], 
                      spacing: float) -> List[Tuple[float, float]]:
        """
        等距重采样路径
        
        Args:
            path: 原始路径
            spacing: 采样间距
            
        Returns:
            重采样后的路径
        """
        if len(path) < 2:
            return path
        
        resampled = [path[0]]  # 保留起点
        
        accumulated_dist = 0.0
        
        for i in range(1, len(path)):
            prev = path[i - 1]
            curr = path[i]
            
            # 计算当前段长度
            dx = curr[0] - prev[0]
            dz = curr[1] - prev[1]
            segment_length = math.sqrt(dx*dx + dz*dz)
            
            # 在当前段上采样
            while accumulated_dist + segment_length >= spacing:
                # 计算采样点位置
                ratio = (spacing - accumulated_dist) / segment_length
                
                sample_x = prev[0] + ratio * dx
                sample_z = prev[1] + ratio * dz
                
                resampled.append((sample_x, sample_z))
                
                # 更新
                accumulated_dist = 0.0
                segment_length -= (spacing - accumulated_dist)
                prev = (sample_x, sample_z)
            
            accumulated_dist += segment_length
        
        # 添加终点
        if resampled[-1] != path[-1]:
            resampled.append(path[-1])
        
        return resampled
    
    def _calculate_yaw(self, current: Tuple[float, float], 
                      target: Tuple[float, float]) -> float:
        """计算期望朝向（偏航角）"""
        dx = target[0] - current[0]
        dz = target[1] - current[1]
        
        yaw = math.atan2(dz, dx)
        
        # 归一化到[-pi, pi]
        while yaw > math.pi:
            yaw -= 2 * math.pi
        while yaw < -math.pi:
            yaw += 2 * math.pi
        
        return yaw
    
    def smooth_waypoints(self, waypoints: List[Waypoint],
                        iterations: int = 3) -> List[Waypoint]:
        """
        平滑航点
        
        使用简单的移动平均平滑航点位置
        """
        if len(waypoints) < 3:
            return waypoints
        
        smoothed = waypoints.copy()
        
        for _ in range(iterations):
            new_positions = []
            
            for i in range(len(smoothed)):
                if i == 0 or i == len(smoothed) - 1:
                    # 保持起点和终点不变
                    new_positions.append((smoothed[i].x, smoothed[i].z))
                else:
                    # 移动平均
                    prev = smoothed[i - 1]
                    curr = smoothed[i]
                    next_wp = smoothed[i + 1]
                    
                    new_x = (1 - self.smoothing_factor) * curr.x + \
                           self.smoothing_factor * (prev.x + next_wp.x) / 2
                    new_z = (1 - self.smoothing_factor) * curr.z + \
                           self.smoothing_factor * (prev.z + next_wp.z) / 2
                    
                    new_positions.append((new_x, new_z))
            
            # 更新航点位置
            for i, (x, z) in enumerate(new_positions):
                smoothed[i] = Waypoint(
                    x=x,
                    z=z,
                    yaw=smoothed[i].yaw,
                    speed=smoothed[i].speed,
                    action=smoothed[i].action,
                    tolerance=smoothed[i].tolerance
                )
        
        # 重新计算朝向
        for i in range(len(smoothed) - 1):
            smoothed[i].yaw = self._calculate_yaw(
                (smoothed[i].x, smoothed[i].z),
                (smoothed[i + 1].x, smoothed[i + 1].z)
            )
        
        return smoothed
    
    def generate_landing_waypoints(self, position: Tuple[float, float],
                                   height: float = 10.0) -> List[Waypoint]:
        """
        生成降落航点
        
        Args:
            position: 降落位置
            height: 初始高度
            
        Returns:
            降落航点序列
        """
        waypoints = [
            Waypoint(
                x=position[0],
                z=position[1],
                yaw=0.0,
                speed=1.0,
                action="move",
                tolerance=0.5
            ),
            Waypoint(
                x=position[0],
                z=position[1],
                yaw=0.0,
                speed=0.5,
                action="hover",
                tolerance=0.3
            ),
            Waypoint(
                x=position[0],
                z=position[1],
                yaw=0.0,
                speed=0.0,
                action="land",
                tolerance=0.1
            )
        ]
        
        return waypoints
    
    def generate_takeoff_waypoints(self, position: Tuple[float, float],
                                   target_height: float = 10.0) -> List[Waypoint]:
        """
        生成起飞航点
        
        Args:
            position: 起飞位置
            target_height: 目标高度
            
        Returns:
            起飞航点序列
        """
        waypoints = [
            Waypoint(
                x=position[0],
                z=position[1],
                yaw=0.0,
                speed=0.0,
                action="takeoff",
                tolerance=0.3
            ),
            Waypoint(
                x=position[0],
                z=position[1],
                yaw=0.0,
                speed=1.0,
                action="hover",
                tolerance=0.5
            )
        ]
        
        return waypoints
    
    def waypoint_to_dict(self, waypoint: Waypoint) -> dict:
        """航点转换为字典"""
        return {
            'x': waypoint.x,
            'z': waypoint.z,
            'yaw': waypoint.yaw,
            'speed': waypoint.speed,
            'action': waypoint.action,
            'tolerance': waypoint.tolerance
        }
    
    def waypoints_to_dicts(self, waypoints: List[Waypoint]) -> List[dict]:
        """航点列表转换为字典列表"""
        return [self.waypoint_to_dict(wp) for wp in waypoints]
