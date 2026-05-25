"""
全局路径规划模块

使用A*算法计算从起点到终点的最优路径。
"""

import heapq
import math
import time
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from loguru import logger

import numpy as np

from perception.mapper import GridMap, CellType


@dataclass
class Node:
    """A*节点"""
    x: int
    z: int
    g: float = 0.0  # 从起点到当前节点的代价
    h: float = 0.0  # 启发式估计代价
    parent: Optional['Node'] = None
    
    @property
    def f(self) -> float:
        """总代价"""
        return self.g + self.h
    
    def __lt__(self, other: 'Node') -> bool:
        """用于优先队列比较"""
        return self.f < other.f
    
    def __eq__(self, other) -> bool:
        """判断位置是否相同"""
        if isinstance(other, Node):
            return self.x == other.x and self.z == other.z
        return False
    
    def __hash__(self) -> int:
        """用于集合和字典"""
        return hash((self.x, self.z))


class AStarPlanner:
    """A*路径规划器"""
    
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
        
        # A*参数
        self.heuristic_weight = 1.0
        self.allow_diagonal = True
        
        # 路径缓存
        self.last_path: Optional[List[Tuple[int, int]]] = None
        self.planning_time: float = 0.0
    
    def heuristic(self, x1: int, z1: int, x2: int, z2: int) -> float:
        """启发式函数（欧几里得距离）"""
        dx = abs(x1 - x2)
        dz = abs(z1 - z2)
        
        if self.allow_diagonal:
            # 对角线距离
            return self.heuristic_weight * math.sqrt(dx * dx + dz * dz)
        else:
            # 曼哈顿距离
            return self.heuristic_weight * (dx + dz)
    
    def get_neighbors(self, node: Node) -> List[Tuple[int, int, float]]:
        """获取邻居节点及移动代价"""
        neighbors = []
        
        # 四连通
        directions = [
            (0, 1, 1.0),   # 上
            (0, -1, 1.0),  # 下
            (1, 0, 1.0),   # 右
            (-1, 0, 1.0),  # 左
        ]
        
        # 八连通（对角线）
        if self.allow_diagonal:
            diagonal_cost = math.sqrt(2)
            directions.extend([
                (1, 1, diagonal_cost),    # 右上
                (1, -1, diagonal_cost),   # 右下
                (-1, 1, diagonal_cost),   # 左上
                (-1, -1, diagonal_cost), # 左下
            ])
        
        for dx, dz, cost in directions:
            nx, nz = node.x + dx, node.z + dz
            
            # 检查边界和障碍物
            if self.grid_map.is_valid_position(nx, nz):
                if self.grid_map.is_free(nx, nz):
                    neighbors.append((nx, nz, cost))
        
        return neighbors
    
    def plan(self, start: Tuple[int, int], 
            goal: Tuple[int, int],
            timeout: float = 5.0) -> Optional[List[Tuple[int, int]]]:
        """规划路径"""
        start_time = time.time()
        
        # 检查起点和终点
        if not self.grid_map.is_valid_position(*start):
            logger.error(f"起点无效: {start}")
            return None
        
        if not self.grid_map.is_valid_position(*goal):
            logger.error(f"终点无效: {goal}")
            return None
        
        # 检查起点和终点是否被占用
        if not self.grid_map.is_free(*start):
            logger.warning(f"起点被占用: {start}")
        
        if not self.grid_map.is_free(*goal):
            logger.warning(f"终点被占用: {goal}")
        
        # 初始化
        start_node = Node(start[0], start[1])
        goal_node = Node(goal[0], goal[1])
        
        start_node.h = self.heuristic(start[0], start[1], goal[0], goal[1])
        
        # 开放列表和关闭列表
        open_list: List[Node] = [start_node]
        closed_set: Set[Tuple[int, int]] = set()
        
        # 节点记录（用于快速查找）
        node_map: Dict[Tuple[int, int], Node] = {(start[0], start[1]): start_node}
        
        while open_list and (time.time() - start_time) < timeout:
            # 取出f值最小的节点
            current = heapq.heappop(open_list)
            
            # 到达目标
            if current.x == goal[0] and current.z == goal[1]:
                path = self._reconstruct_path(current)
                self.last_path = path
                self.planning_time = time.time() - start_time
                logger.info(f"A*规划成功: 路径长度{len(path)}, 耗时{self.planning_time:.3f}s")
                return path
            
            # 加入关闭列表
            closed_set.add((current.x, current.z))
            
            # 扩展邻居
            for nx, nz, cost in self.get_neighbors(current):
                if (nx, nz) in closed_set:
                    continue
                
                # 计算新的g值
                new_g = current.g + cost
                
                # 检查是否已在开放列表中
                neighbor = node_map.get((nx, nz))
                
                if neighbor is None:
                    # 创建新节点
                    neighbor = Node(nx, nz, new_g, 
                                   self.heuristic(nx, nz, goal[0], goal[1]),
                                   current)
                    node_map[(nx, nz)] = neighbor
                    heapq.heappush(open_list, neighbor)
                elif new_g < neighbor.g:
                    # 更新更优路径
                    neighbor.g = new_g
                    neighbor.parent = current
                    # 重新排序
                    heapq.heapify(open_list)
        
        # 超时或无法到达
        if time.time() - start_time >= timeout:
            logger.error(f"A*规划超时: {timeout}s")
        else:
            logger.error("A*规划失败: 无法到达目标")
        
        return None
    
    def _reconstruct_path(self, goal_node: Node) -> List[Tuple[int, int]]:
        """重建路径"""
        path = []
        current: Optional[Node] = goal_node
        
        while current is not None:
            path.append((current.x, current.z))
            current = current.parent
        
        # 反转得到从起点到终点的路径
        path.reverse()
        return path
    
    def smooth_path(self, path: List[Tuple[int, int]], 
                   weight_data: float = 0.5,
                   weight_smooth: float = 0.3,
                   tolerance: float = 0.00001) -> List[Tuple[int, int]]:
        """路径平滑"""
        if len(path) < 3:
            return path
        
        # 转换为浮点数进行平滑
        smooth_path = [[float(p[0]), float(p[1])] for p in path]
        
        change = tolerance
        while change >= tolerance:
            change = 0.0
            
            for i in range(1, len(path) - 1):
                for j in range(2):
                    aux = smooth_path[i][j]
                    
                    # 平滑公式
                    smooth_path[i][j] += weight_data * (path[i][j] - smooth_path[i][j])
                    smooth_path[i][j] += weight_smooth * (
                        smooth_path[i-1][j] + smooth_path[i+1][j] - 2 * smooth_path[i][j]
                    )
                    
                    change += abs(aux - smooth_path[i][j])
        
        # 转回整数坐标
        return [(int(round(p[0])), int(round(p[1]))) for p in smooth_path]
    
    def simplify_path(self, path: List[Tuple[int, int]], 
                     epsilon: float = 1.0) -> List[Tuple[int, int]]:
        """简化路径（Ramer-Douglas-Peucker算法）"""
        if len(path) < 3:
            return path
        
        def perpendicular_distance(point, line_start, line_end):
            """计算点到线段的垂直距离"""
            x0, z0 = point
            x1, z1 = line_start
            x2, z2 = line_end
            
            if x1 == x2 and z1 == z2:
                return math.sqrt((x0 - x1)**2 + (z0 - z1)**2)
            
            num = abs((z2 - z1) * x0 - (x2 - x1) * z0 + x2 * z1 - z2 * x1)
            den = math.sqrt((z2 - z1)**2 + (x2 - x1)**2)
            
            return num / den if den > 0 else 0
        
        def rdp(points, epsilon):
            """RDP递归实现"""
            if len(points) < 3:
                return points
            
            # 找到距离最远的点
            dmax = 0
            index = 0
            
            for i in range(1, len(points) - 1):
                d = perpendicular_distance(points[i], points[0], points[-1])
                if d > dmax:
                    index = i
                    dmax = d
            
            # 如果最大距离超过阈值，递归简化
            if dmax > epsilon:
                left = rdp(points[:index+1], epsilon)
                right = rdp(points[index:], epsilon)
                return left[:-1] + right
            else:
                return [points[0], points[-1]]
        
        return rdp(path, epsilon)


class GlobalPlanner:
    """全局规划器"""
    
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
        self.astar = AStarPlanner(grid_map)
        
        # 规划结果
        self.current_path: Optional[List[Tuple[int, int]]] = None
        self.waypoints: Optional[List[Tuple[float, float]]] = None
    
    def plan_path(self, start_world: Tuple[float, float],
                 goal_world: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """规划世界坐标路径"""
        # 转换为栅格坐标
        start_grid = self.grid_map.world_to_grid(*start_world)
        goal_grid = self.grid_map.world_to_grid(*goal_world)
        
        logger.info(f"规划路径: 世界{start_world} -> {goal_world}")
        logger.info(f"栅格坐标: {start_grid} -> {goal_grid}")
        
        # 执行A*规划
        grid_path = self.astar.plan(start_grid, goal_grid)
        
        if grid_path is None:
            return None
        
        self.current_path = grid_path
        
        # 平滑路径
        smoothed_grid_path = self.astar.smooth_path(grid_path)
        
        # 简化为航点
        waypoint_grid = self.astar.simplify_path(smoothed_grid_path)
        
        # 转换为世界坐标
        self.waypoints = [self.grid_map.grid_to_world(gx, gz) 
                         for gx, gz in waypoint_grid]
        
        logger.info(f"路径规划完成: {len(grid_path)}个栅格, {len(self.waypoints)}个航点")
        
        return self.waypoints
    
    def get_path_length(self) -> float:
        """获取路径长度（米）"""
        if not self.waypoints:
            return 0.0
        
        length = 0.0
        for i in range(len(self.waypoints) - 1):
            dx = self.waypoints[i+1][0] - self.waypoints[i][0]
            dz = self.waypoints[i+1][1] - self.waypoints[i][1]
            length += math.sqrt(dx*dx + dz*dz)
        
        return length
    
    def update_map(self, grid_map: GridMap):
        """更新地图"""
        self.grid_map = grid_map
        self.astar.grid_map = grid_map
        
        # 重新规划
        if self.waypoints:
            self.plan_path(self.waypoints[0], self.waypoints[-1])
