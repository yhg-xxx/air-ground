"""
地图构建器模块

负责迷宫地图的构建、更新和管理。
实现栅格地图和拓扑地图两种表示。
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from config.constants import PlanningConstants


class CellType(Enum):
    """栅格类型"""
    UNKNOWN = 0      # 未知
    FREE = 1         # 可通行
    OCCUPIED = 2     # 障碍
    ARCH = 3         # 拱门
    START = 4        # 起点
    GOAL = 5         # 终点


@dataclass
class MapConfig:
    """地图配置"""
    width: int = 480
    height: int = 1200
    cell_size: float = 0.052  # 米
    origin_x: float = -12.5
    origin_z: float = 0.0


class GridMap:
    """栅格地图"""
    
    def __init__(self, config: Optional[MapConfig] = None):
        self.config = config or MapConfig()
        
        # 初始化栅格地图
        self.grid = np.zeros(
            (self.config.height, self.config.width),
            dtype=np.uint8
        )
        
        # 地图元数据
        self.metadata = {
            'created_at': None,
            'updated_at': None,
            'resolution': self.config.cell_size,
            'origin': (self.config.origin_x, self.config.origin_z)
        }
        
        # 特殊位置标记
        self.start_pos: Optional[Tuple[int, int]] = None
        self.goal_pos: Optional[Tuple[int, int]] = None
        self.arch_positions: List[Tuple[int, int]] = []
    
    def world_to_grid(self, x: float, z: float) -> Tuple[int, int]:
        """世界坐标转栅格坐标"""
        grid_x = int((x - self.config.origin_x) / self.config.cell_size)
        grid_z = int((z - self.config.origin_z) / self.config.cell_size)
        
        # 边界检查
        grid_x = max(0, min(grid_x, self.config.width - 1))
        grid_z = max(0, min(grid_z, self.config.height - 1))
        
        return grid_x, grid_z
    
    def grid_to_world(self, grid_x: int, grid_z: int) -> Tuple[float, float]:
        """栅格坐标转世界坐标"""
        x = grid_x * self.config.cell_size + self.config.origin_x
        z = grid_z * self.config.cell_size + self.config.origin_z
        return x, z
    
    def set_cell(self, grid_x: int, grid_z: int, cell_type: CellType):
        """设置栅格类型"""
        if 0 <= grid_x < self.config.width and 0 <= grid_z < self.config.height:
            self.grid[grid_z, grid_x] = cell_type.value
            
            if cell_type == CellType.START:
                self.start_pos = (grid_x, grid_z)
            elif cell_type == CellType.GOAL:
                self.goal_pos = (grid_x, grid_z)
            elif cell_type == CellType.ARCH:
                if (grid_x, grid_z) not in self.arch_positions:
                    self.arch_positions.append((grid_x, grid_z))
    
    def get_cell(self, grid_x: int, grid_z: int) -> CellType:
        """获取栅格类型"""
        if 0 <= grid_x < self.config.width and 0 <= grid_z < self.config.height:
            return CellType(self.grid[grid_z, grid_x])
        return CellType.UNKNOWN
    
    def is_free(self, grid_x: int, grid_z: int) -> bool:
        """检查栅格是否可通行"""
        cell = self.get_cell(grid_x, grid_z)
        return cell in [CellType.FREE, CellType.START, CellType.GOAL, CellType.ARCH]
    
    def is_valid_position(self, grid_x: int, grid_z: int) -> bool:
        """检查位置是否有效"""
        return 0 <= grid_x < self.config.width and 0 <= grid_z < self.config.height
    
    def get_neighbors(self, grid_x: int, grid_z: int, 
                     diagonal: bool = True) -> List[Tuple[int, int]]:
        """获取相邻栅格"""
        neighbors = []
        
        # 四连通
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        # 八连通（对角线）
        if diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        
        for dx, dz in directions:
            nx, nz = grid_x + dx, grid_z + dz
            if self.is_valid_position(nx, nz):
                neighbors.append((nx, nz))
        
        return neighbors
    
    def inflate_obstacles(self, inflation_radius: int = 2):
        """膨胀障碍物"""
        occupied = (self.grid == CellType.OCCUPIED.value)
        
        # 创建膨胀后的障碍物地图
        inflated = occupied.copy()
        
        for i in range(self.config.height):
            for j in range(self.config.width):
                if occupied[i, j]:
                    for di in range(-inflation_radius, inflation_radius + 1):
                        for dj in range(-inflation_radius, inflation_radius + 1):
                            ni, nj = i + di, j + dj
                            if 0 <= ni < self.config.height and 0 <= nj < self.config.width:
                                inflated[ni, nj] = True
        
        # 更新地图
        self.grid[inflated] = CellType.OCCUPIED.value
    
    def to_image(self, scale: int = 1) -> np.ndarray:
        """转换为可视化图像"""
        height, width = self.config.height * scale, self.config.width * scale
        
        # 创建彩色图像
        image = np.ones((height, width, 3), dtype=np.uint8) * 128
        
        # 颜色映射
        color_map = {
            CellType.UNKNOWN.value: (128, 128, 128),    # 灰色
            CellType.FREE.value: (255, 255, 255),       # 白色
            CellType.OCCUPIED.value: (0, 0, 0),         # 黑色
            CellType.ARCH.value: (0, 255, 0),           # 绿色
            CellType.START.value: (0, 255, 255),        # 青色
            CellType.GOAL.value: (255, 0, 0)            # 红色
        }
        
        for i in range(self.config.height):
            for j in range(self.config.width):
                cell_value = self.grid[i, j]
                color = color_map.get(cell_value, (128, 128, 128))
                
                # 填充缩放后的区域
                for si in range(scale):
                    for sj in range(scale):
                        image[i * scale + si, j * scale + sj] = color
        
        return image
    
    def save(self, filepath: str):
        """保存地图"""
        np.savez(filepath,
                 grid=self.grid,
                 config=self.config.__dict__,
                 metadata=self.metadata,
                 start_pos=self.start_pos,
                 goal_pos=self.goal_pos,
                 arch_positions=self.arch_positions)
        logger.info(f"地图已保存到: {filepath}")
    
    def load(self, filepath: str):
        """加载地图"""
        data = np.load(filepath, allow_pickle=True)
        
        self.grid = data['grid']
        self.config = MapConfig(**data['config'].item())
        self.metadata = data['metadata'].item()
        self.start_pos = tuple(data['start_pos']) if data['start_pos'] is not None else None
        self.goal_pos = tuple(data['goal_pos']) if data['goal_pos'] is not None else None
        self.arch_positions = [tuple(pos) for pos in data['arch_positions']]
        
        logger.info(f"地图已从 {filepath} 加载")


class MazeMapper:
    """迷宫地图构建器"""
    
    def __init__(self):
        self.grid_map = GridMap()
        self.image_processor = None
        
        # 构建状态
        self.is_building = False
        self.explored_area = 0.0
    
    def initialize(self, config: Optional[MapConfig] = None):
        """初始化地图"""
        self.grid_map = GridMap(config)
        logger.info("地图构建器初始化完成")
    
    def update_from_detection(self, detection_result: Dict, 
                            robot_position: Tuple[float, float]):
        """根据检测结果更新地图"""
        grid_x, grid_z = self.grid_map.world_to_grid(*robot_position)
        
        # 标记机器人位置为已探索
        if self.grid_map.is_valid_position(grid_x, grid_z):
            if self.grid_map.get_cell(grid_x, grid_z) == CellType.UNKNOWN:
                self.grid_map.set_cell(grid_x, grid_z, CellType.FREE)
        
        # 根据检测结果更新地图
        if detection_result.get('arch_detected'):
            arch = detection_result['arch']
            # 转换拱门位置到世界坐标
            # 这里需要根据实际相机参数和无人机位置计算
            pass
    
    def add_boundary(self, points: List[Tuple[float, float]]):
        """添加边界"""
        for point in points:
            grid_x, grid_z = self.grid_map.world_to_grid(*point)
            if self.grid_map.is_valid_position(grid_x, grid_z):
                self.grid_map.set_cell(grid_x, grid_z, CellType.OCCUPIED)
    
    def add_arch(self, position: Tuple[float, float]):
        """添加拱门位置"""
        grid_x, grid_z = self.grid_map.world_to_grid(*position)
        if self.grid_map.is_valid_position(grid_x, grid_z):
            self.grid_map.set_cell(grid_x, grid_z, CellType.ARCH)
            logger.info(f"添加拱门位置: 世界({position[0]:.2f}, {position[1]:.2f}) -> 栅格({grid_x}, {grid_z})")
    
    def set_start(self, position: Tuple[float, float]):
        """设置起点"""
        grid_x, grid_z = self.grid_map.world_to_grid(*position)
        if self.grid_map.is_valid_position(grid_x, grid_z):
            self.grid_map.set_cell(grid_x, grid_z, CellType.START)
            logger.info(f"设置起点: 世界({position[0]:.2f}, {position[1]:.2f}) -> 栅格({grid_x}, {grid_z})")
    
    def set_goal(self, position: Tuple[float, float]):
        """设置终点"""
        grid_x, grid_z = self.grid_map.world_to_grid(*position)
        if self.grid_map.is_valid_position(grid_x, grid_z):
            self.grid_map.set_cell(grid_x, grid_z, CellType.GOAL)
            logger.info(f"设置终点: 世界({position[0]:.2f}, {position[1]:.2f}) -> 栅格({grid_x}, {grid_z})")
    
    def get_map(self) -> GridMap:
        """获取地图"""
        return self.grid_map
    
    def get_exploration_rate(self) -> float:
        """获取探索率"""
        total_cells = self.grid_map.config.width * self.grid_map.config.height
        explored_cells = np.sum(self.grid_map.grid != CellType.UNKNOWN.value)
        return explored_cells / total_cells
    
    def visualize(self, scale: int = 1) -> np.ndarray:
        """可视化地图"""
        return self.grid_map.to_image(scale)
