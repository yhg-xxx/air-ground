"""
可视化工具模块

负责路径、地图和状态的可视化显示。
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class VisualizationConfig:
    """可视化配置"""
    width: int = 800
    height: int = 600
    scale: float = 10.0  # 像素/米
    origin_x: float = 400.0
    origin_z: float = 300.0


class PathVisualizer:
    """路径可视化器"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
    
    def world_to_pixel(self, x: float, z: float) -> Tuple[int, int]:
        """世界坐标转像素坐标"""
        px = int(self.config.origin_x + x * self.config.scale)
        pz = int(self.config.origin_z - z * self.config.scale)
        return px, pz
    
    def pixel_to_world(self, px: int, pz: int) -> Tuple[float, float]:
        """像素坐标转世界坐标"""
        x = (px - self.config.origin_x) / self.config.scale
        z = (self.config.origin_z - pz) / self.config.scale
        return x, z
    
    def draw_path(self, image: np.ndarray, 
                 path: List[Tuple[float, float]],
                 color: Tuple = (0, 255, 0),
                 thickness: int = 2) -> np.ndarray:
        """绘制路径"""
        if len(path) < 2:
            return image
        
        points = [self.world_to_pixel(x, z) for x, z in path]
        
        for i in range(len(points) - 1):
            cv2.line(image, points[i], points[i+1], color, thickness)
        
        return image
    
    def draw_point(self, image: np.ndarray,
                  position: Tuple[float, float],
                  color: Tuple = (0, 0, 255),
                  radius: int = 5,
                  label: str = None) -> np.ndarray:
        """绘制点"""
        px, pz = self.world_to_pixel(*position)
        cv2.circle(image, (px, pz), radius, color, -1)
        
        if label:
            cv2.putText(image, label, (px + 10, pz - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return image
    
    def draw_robot(self, image: np.ndarray,
                  position: Tuple[float, float],
                  yaw: float,
                  color: Tuple = (255, 0, 0),
                  size: int = 10) -> np.ndarray:
        """绘制机器人"""
        px, pz = self.world_to_pixel(*position)
        
        # 绘制主体
        cv2.circle(image, (px, pz), size, color, 2)
        
        # 绘制朝向
        end_x = int(px + size * 2 * np.cos(yaw))
        end_z = int(pz - size * 2 * np.sin(yaw))
        cv2.line(image, (px, pz), (end_x, end_z), color, 2)
        
        return image
    
    def create_canvas(self, background_color: Tuple = (255, 255, 255)) -> np.ndarray:
        """创建画布"""
        return np.ones(
            (self.config.height, self.config.width, 3),
            dtype=np.uint8
        ) * np.array(background_color, dtype=np.uint8)


class MapVisualizer:
    """地图可视化器"""
    
    def __init__(self, cell_size: float = 0.05):
        self.cell_size = cell_size
        self.color_map = {
            0: (128, 128, 128),  # 未知 - 灰色
            1: (255, 255, 255),  # 可通行 - 白色
            2: (0, 0, 0),       # 障碍 - 黑色
            3: (0, 255, 0),     # 拱门 - 绿色
            4: (0, 255, 255),   # 起点 - 青色
            5: (255, 0, 0),     # 终点 - 红色
        }
    
    def visualize_grid(self, grid: np.ndarray, 
                      scale: int = 4) -> np.ndarray:
        """可视化栅格地图"""
        height, width = grid.shape
        
        # 创建彩色图像
        image = np.ones((height * scale, width * scale, 3), dtype=np.uint8) * 128
        
        for i in range(height):
            for j in range(width):
                cell_value = grid[i, j]
                color = self.color_map.get(cell_value, (128, 128, 128))
                
                # 填充缩放后的区域
                for si in range(scale):
                    for sj in range(scale):
                        if i * scale + si < image.shape[0] and j * scale + sj < image.shape[1]:
                            image[i * scale + si, j * scale + sj] = color
        
        return image
    
    def overlay_path(self, map_image: np.ndarray, 
                    path: List[Tuple[int, int]],
                    color: Tuple = (255, 255, 0),
                    scale: int = 4) -> np.ndarray:
        """在地图上叠加路径"""
        result = map_image.copy()
        
        for i in range(len(path) - 1):
            pt1 = (path[i][0] * scale + scale // 2, path[i][1] * scale + scale // 2)
            pt2 = (path[i+1][0] * scale + scale // 2, path[i+1][1] * scale + scale // 2)
            cv2.line(result, pt1, pt2, color, 2)
        
        return result


class TelemetryVisualizer:
    """遥测数据可视化器"""
    
    def __init__(self, width: int = 400, height: int = 300):
        self.width = width
        self.height = height
        
        # 历史数据
        self.position_history = []
        self.max_history = 100
    
    def update_position(self, position: Tuple[float, float]):
        """更新位置历史"""
        self.position_history.append(position)
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
    
    def draw_trajectory(self) -> np.ndarray:
        """绘制轨迹"""
        image = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        
        if len(self.position_history) < 2:
            return image
        
        # 计算范围
        xs = [p[0] for p in self.position_history]
        zs = [p[1] for p in self.position_history]
        
        min_x, max_x = min(xs), max(xs)
        min_z, max_z = min(zs), max(zs)
        
        # 添加边距
        margin = 20
        range_x = max_x - min_x if max_x > min_x else 1
        range_z = max_z - min_z if max_z > min_z else 1
        
        scale_x = (self.width - 2 * margin) / range_x
        scale_z = (self.height - 2 * margin) / range_z
        scale = min(scale_x, scale_z)
        
        # 转换为像素坐标
        def to_pixel(x, z):
            px = int(margin + (x - min_x) * scale)
            pz = int(self.height - margin - (z - min_z) * scale)
            return px, pz
        
        # 绘制轨迹
        points = [to_pixel(x, z) for x, z in self.position_history]
        
        for i in range(len(points) - 1):
            cv2.line(image, points[i], points[i+1], (0, 255, 0), 2)
        
        # 绘制起点和终点
        if points:
            cv2.circle(image, points[0], 5, (0, 0, 255), -1)  # 起点 - 红色
            cv2.circle(image, points[-1], 5, (255, 0, 0), -1)  # 终点 - 蓝色
        
        return image
    
    def draw_status_panel(self, status: Dict) -> np.ndarray:
        """绘制状态面板"""
        image = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        
        # 绘制背景
        cv2.rectangle(image, (0, 0), (self.width, self.height), (200, 200, 200), -1)
        
        # 绘制状态信息
        y_offset = 30
        for key, value in status.items():
            text = f"{key}: {value}"
            cv2.putText(image, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            y_offset += 25
            
            if y_offset > self.height - 20:
                break
        
        return image


class VisualizationManager:
    """可视化管理器"""
    
    def __init__(self):
        self.path_viz = PathVisualizer()
        self.map_viz = MapVisualizer()
        self.telemetry_viz = TelemetryVisualizer()
        
        self.active = False
    
    def start(self):
        """启动可视化"""
        self.active = True
    
    def stop(self):
        """停止可视化"""
        self.active = False
        cv2.destroyAllWindows()
    
    def show_map(self, grid: np.ndarray, path: List[Tuple[int, int]] = None):
        """显示地图"""
        if not self.active:
            return
        
        map_image = self.map_viz.visualize_grid(grid)
        
        if path:
            map_image = self.map_viz.overlay_path(map_image, path)
        
        cv2.imshow("Map", map_image)
        cv2.waitKey(1)
    
    def show_path(self, path: List[Tuple[float, float]], 
                 robot_pos: Tuple[float, float] = None):
        """显示路径"""
        if not self.active:
            return
        
        canvas = self.path_viz.create_canvas()
        
        if path:
            canvas = self.path_viz.draw_path(canvas, path)
        
        if robot_pos:
            canvas = self.path_viz.draw_robot(canvas, robot_pos, 0)
        
        cv2.imshow("Path", canvas)
        cv2.waitKey(1)
    
    def update(self):
        """更新显示"""
        if self.active:
            cv2.waitKey(1)
