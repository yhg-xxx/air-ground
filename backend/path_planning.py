"""
路径规划脚本
找出迷宫中从起点到终点的最短路径
"""

import numpy as np
import json
import cv2
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

# 配置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
from collections import deque
import heapq


class PathPlanner:
    def __init__(self, grid_data_path: str = "output/grid_data.npz"):
        """初始化路径规划器"""
        # 加载格栅数据
        data = np.load(grid_data_path)
        self.grid = data['grid']  # 0=可通行, 1=障碍物
        self.rows, self.cols = self.grid.shape
        print(f"格栅尺寸: {self.cols} × {self.rows}")
        
    def find_gates(self, original_image_path: str):
        """找到蓝色拱门（起点和终点），并返回详细信息"""
        # 读取原始图像
        image = cv2.imdecode(np.fromfile(original_image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 检测蓝色区域
        cyan_mask = cv2.inRange(hsv, np.array([80, 50, 50]), np.array([100, 255, 255]))
        
        # 找到蓝色连通区域
        contours, _ = cv2.findContours(cyan_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        gates = []
        img_h, img_w = image.shape[:2]
        cell_w = img_w / self.cols
        cell_h = img_h / self.rows
        
        for contour in contours:
            # 计算中心点
            M = cv2.moments(contour)
            if M['m00'] > 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                
                # 转换为格栅坐标
                grid_x = int(cx / cell_w)
                grid_y = int(cy / cell_h)
                
                # 确保在边界内
                grid_x = max(0, min(grid_x, self.cols - 1))
                grid_y = max(0, min(grid_y, self.rows - 1))
                
                # 计算拱门的宽高（格栅单位）
                x, y, w, h = cv2.boundingRect(contour)
                gate_w = max(1, int(w / cell_w))
                gate_h = max(1, int(h / cell_h))
                
                gates.append({
                    'center': (grid_x, grid_y),
                    'width': gate_w,
                    'height': gate_h,
                    'pixel_y': cy  # 用于排序
                })
        
        # 按照实际迷宫路径顺序排序
        gates = self._sort_gates_by_path_order(gates)
        self.gates = gates  # 保存拱门信息用于可视化
        
        if len(gates) >= 2:
            start = gates[0]['center']   # 下边的门（起点）
            end = gates[-1]['center']    # 上边的门（终点）
            print(f"起点: {start}, 终点: {end}")
            return start, end
        else:
            print(f"只找到 {len(gates)} 个门，手动设置起点终点")
            # 手动设置（基于480x1200格栅）
            start = (self.cols // 2, self.rows - 10)  # 下边中间
            end = (self.cols // 2, 10)                # 上边中间
            return start, end
    
    def _sort_gates_by_path_order(self, gates):
        """按照实际走迷宫的路径顺序排序拱门"""
        if not gates:
            return gates
        
        # 定义拱门的正确顺序（基于坐标位置）
        # 顺序: 1-8为下半部分拱门，9为最上边的拱门
        order_coords = [
            (331, 943),   # 1
            (295, 1003),  # 2
            (219, 1087),  # 3
            (131, 999),   # 4
            (19, 1087),   # 5
            (75, 1167),   # 6
            (323, 1167),  # 7
            (391, 1107),  # 8
            (339, 103),   # 9 - 最上边的拱门
        ]
        
        sorted_gates = []
        used = set()
        
        for target_x, target_y in order_coords:
            best_gate = None
            best_dist = float('inf')
            best_idx = -1
            
            for i, gate in enumerate(gates):
                if i in used:
                    continue
                gx, gy = gate['center']
                dist = abs(gx - target_x) + abs(gy - target_y)
                if dist < best_dist:
                    best_dist = dist
                    best_gate = gate
                    best_idx = i
            
            if best_gate and best_dist < 50:
                sorted_gates.append(best_gate)
                used.add(best_idx)
        
        for i, gate in enumerate(gates):
            if i not in used:
                sorted_gates.append(gate)
        
        return sorted_gates
    
    def a_star(self, start, end):
        """A*算法找最短路径"""
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        def get_neighbors(pos):
            x, y = pos
            neighbors = []
            # 8方向移动
            for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.grid[ny, nx] == 0:  # 可通行
                        # 对角线移动的代价更高
                        cost = 1.414 if dx != 0 and dy != 0 else 1.0
                        neighbors.append(((nx, ny), cost))
            return neighbors
        
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, end)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == end:
                # 重建路径
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            
            for neighbor, move_cost in get_neighbors(current):
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None  # 无路径
    
    def visualize_path(self, start, end, path, output_path="output/path_result.png"):
        """可视化路径"""
        # 创建彩色图像
        vis = np.zeros((self.rows, self.cols, 3), dtype=np.uint8)
        vis[self.grid == 0] = [240, 240, 240]  # 浅灰 - 可通行
        vis[self.grid == 1] = [50, 50, 50]     # 深灰 - 障碍物
        
        # 绘制路径
        if path:
            for i, (x, y) in enumerate(path):
                if i == 0:
                    vis[y, x] = [0, 255, 0]      # 绿色 - 起点
                elif i == len(path) - 1:
                    vis[y, x] = [0, 0, 255]      # 红色 - 终点
                else:
                    vis[y, x] = [255, 165, 0]    # 橙色 - 路径
        
        # 放大以便查看
        scale = max(1, 1200 // max(self.rows, self.cols))
        vis_large = cv2.resize(vis, (self.cols * scale, self.rows * scale), interpolation=cv2.INTER_NEAREST)
        
        # 保存图像
        cv2.imwrite(output_path, vis_large)
        print(f"路径图已保存: {output_path}")
        
        # 也用matplotlib保存高质量版本
        plt.figure(figsize=(16, 40))
        plt.imshow(vis, aspect='auto')
        plt.title(f"最短路径 - 长度: {len(path) if path else 0}步")
        
        if path:
            # 标记起点和终点
            plt.plot(start[0], start[1], 'go', markersize=10, label='起点')
            plt.plot(end[0], end[1], 'ro', markersize=10, label='终点')
            
            # 绘制路径线
            path_x = [p[0] for p in path]
            path_y = [p[1] for p in path]
            plt.plot(path_x, path_y, 'orange', linewidth=2, label='最短路径')
            
            plt.legend()
        
        # 标注蓝色拱门
        if hasattr(self, 'gates') and self.gates:
            for i, gate in enumerate(self.gates):
                cx, cy = gate['center']
                gw, gh = gate['width'], gate['height']
                
                # 画矩形标注
                rect = plt.Rectangle((cx - gw/2, cy - gh/2), gw, gh,
                                      linewidth=2, edgecolor='blue', facecolor='cyan', alpha=0.4)
                plt.gca().add_patch(rect)
                
                # 添加文字标签
                label = f'拱门{i+1}'
                plt.annotate(label, (cx, cy - gh/2 - 5), color='blue', fontsize=10, 
                            ha='center', va='bottom', fontweight='bold',
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.xlabel('X (格)')
        plt.ylabel('Y (格)')
        
        detail_path = "output/path_detail.png"
        plt.savefig(detail_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"详细路径图已保存: {detail_path}")
        
        return vis_large
    
    def calculate_path_length(self, path):
        """计算路径实际长度（米）"""
        if not path:
            return 0
        
        total_length = 0
        for i in range(1, len(path)):
            x1, y1 = path[i-1]
            x2, y2 = path[i]
            # 计算欧几里得距离
            distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            total_length += distance
        
        # 转换为实际长度（假设每格0.167米）
        real_length = total_length * (1/6)
        return real_length
    
    def find_shortest_path(self, original_image_path: str, manual_start=None, manual_end=None):
        """主函数：找出最短路径"""
        print("=" * 60)
        print("路径规划开始")
        print("=" * 60)
        
        # 1. 找到起点终点
        # 先检测拱门（用于可视化）
        self.find_gates(original_image_path)
        
        if manual_start and manual_end:
            start, end = manual_start, manual_end
            print(f"使用手动设置: 起点: {start}, 终点: {end}")
            
            # 如果起终点 x 坐标相同且都在边缘，临时阻断边缘路径强制往内走
            if start[0] == end[0] and start[0] >= 340:  # x=350 附近的边缘
                print("检测到边缘路径，临时阻断边缘强制往内走...")
                # 临时把 x=350 中间段设为障碍物，保留起终点附近通道
                x_coord = min(start[0], self.grid.shape[0] - 1)
                # 只阻断中间 60% 的路径
                total_distance = abs(end[1] - start[1])
                block_start = min(start[1], end[1]) + int(total_distance * 0.2)
                block_end = max(start[1], end[1]) - int(total_distance * 0.2)
                
                for y in range(block_start, block_end):
                    if y < self.grid.shape[1]:
                        self.grid[x_coord, y] = 1  # 设为障碍物
                        
        else:
            start, end = self.find_gates(original_image_path)
        
        # 2. A*算法寻路
        print("开始A*算法寻路...")
        path = self.a_star(start, end)
        
        if path:
            print(f"找到路径！总步数: {len(path)}")
            real_length = self.calculate_path_length(path)
            print(f"路径实际长度: {real_length:.2f} 米")
        else:
            print("未找到可行路径！")
            
        # 3. 可视化
        self.visualize_path(start, end, path)
        
        # 4. 保存路径数据
        if path:
            path_data = {
                "start": start,
                "end": end,
                "path": path,
                "length_steps": len(path),
                "length_meters": self.calculate_path_length(path)
            }
            
            with open("output/path_data.json", 'w') as f:
                json.dump(path_data, f, indent=2)
            print("路径数据已保存: output/path_data.json")
        
        return path


if __name__ == "__main__":
    import sys
    
    # 默认参数
    grid_path = "output/grid_data.npz"
    image_path = r"d:\pythonCodes\air-ground\backend\grid-1775449079133_upscaled_3.0x.png"
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    
    # 创建规划器
    planner = PathPlanner(grid_path)
    
    # 用户指定的起点和终点坐标（x 必须是 350）
    manual_start = (350, 945)   # 起点
    manual_end = (350, 105)     # 终点
    
    # 寻找最短路径
    path = planner.find_shortest_path(image_path, manual_start, manual_end)
    
    print("\n" + "=" * 60)
    print("路径规划完成！")
    print("=" * 60)
