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
        
        # 场地尺寸：左边黑墙44米(1129格)，下边黑墙17米(425格)
        METERS_PER_GRID_X = 17.0 / 425.0   # X方向：0.04米/格
        METERS_PER_GRID_Y = 44.0 / 1129.0  # Y方向：0.039米/格
        
        total_length = 0
        for i in range(1, len(path)):
            x1, y1 = path[i-1]
            x2, y2 = path[i]
            dx = (x2 - x1) * METERS_PER_GRID_X
            dy = (y2 - y1) * METERS_PER_GRID_Y
            distance = np.sqrt(dx**2 + dy**2)
            total_length += distance
        
        return total_length
    
    def find_drone_flight_path(self, original_image_path: str, start_point=None, end_point=None):
        """
        无人机直飞路径规划
        从起点直接起飞，按顺序穿过拱门1-8的中心点，然后飞到终点
        无人机飞行不受地面障碍物限制，采用直线连接
        """
        print("=" * 60)
        print("无人机直飞路径规划")
        print("=" * 60)
        
        # 1. 检测所有拱门
        self.find_gates(original_image_path)
        
        if not hasattr(self, 'gates') or len(self.gates) < 8:
            print(f"警告: 只检测到 {len(self.gates) if hasattr(self, 'gates') else 0} 个拱门，需要至少8个")
            return None
        
        # 2. 获取起点和终点
        if start_point is None:
            start_point = (350, 945)  # 默认起点
        if end_point is None:
            end_point = (350, 105)    # 默认终点
        
        print(f"起点: {start_point}")
        print(f"终点: {end_point}")
        
        # 3. 构建飞行路径：起点 -> 拱门1-8中心 -> 终点
        flight_waypoints = [start_point]
        
        # 拱门1-8的中心点（不包括拱门9）
        for i in range(min(8, len(self.gates))):
            gate_center = self.gates[i]['center']
            flight_waypoints.append(gate_center)
            print(f"拱门{i+1}中心: {gate_center}")
        
        flight_waypoints.append(end_point)
        
        print(f"\n飞行路径点数: {len(flight_waypoints)}")
        
        # 4. 计算每段距离和总距离
        segment_distances = []
        total_distance = 0
        
        print("\n各段距离:")
        segment_distances_m = []  # 实际距离（米）
        for i in range(1, len(flight_waypoints)):
            x1, y1 = flight_waypoints[i-1]
            x2, y2 = flight_waypoints[i]
            dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            segment_distances.append(dist)
            total_distance += dist
            
            # 段名称
            if i == 1:
                segment_name = f"起点 -> 拱门1"
            elif i == len(flight_waypoints) - 1:
                segment_name = f"拱门{i-1} -> 终点"
            else:
                segment_name = f"拱门{i-1} -> 拱门{i}"
            
            # 场地尺寸：左边黑墙44米(1129格)，下边黑墙17米(425格)
            METERS_PER_GRID_X = 17.0 / 425.0
            METERS_PER_GRID_Y = 44.0 / 1129.0
            dx_m = (x2 - x1) * METERS_PER_GRID_X
            dy_m = (y2 - y1) * METERS_PER_GRID_Y
            dist_m = np.sqrt(dx_m**2 + dy_m**2)
            segment_distances_m.append(dist_m)
            print(f"  {segment_name}: {dist:.2f} 格 ({dist_m:.2f} 米)")
        
        # 计算实际总长度（米）
        real_length = sum(segment_distances_m)
        print(f"\n总飞行距离: {total_distance:.2f} 格 ({real_length:.2f} 米)")
        
        # 5. 可视化飞行路径
        self._visualize_flight_path(flight_waypoints, segment_distances)
        
        # 6. 保存路径数据
        flight_data = {
            "type": "drone_flight_path",
            "start": start_point,
            "end": end_point,
            "waypoints": flight_waypoints,
            "gate_sequence": [f"拱门{i+1}" for i in range(min(8, len(self.gates)))],
            "segment_distances_grid": segment_distances,
            "segment_distances_meters": segment_distances_m,
            "total_distance_grid": total_distance,
            "total_distance_meters": real_length
        }
        
        with open("output/drone_flight_path.json", 'w', encoding='utf-8') as f:
            json.dump(flight_data, f, indent=2, ensure_ascii=False)
        print(f"\n飞行路径数据已保存: output/drone_flight_path.json")
        
        return flight_waypoints
    
    def _visualize_flight_path(self, waypoints, segment_distances):
        """可视化无人机飞行路径"""
        # 创建图形
        plt.figure(figsize=(16, 40))
        
        # 绘制格栅背景
        vis = np.zeros((self.rows, self.cols, 3), dtype=np.uint8)
        vis[self.grid == 0] = [240, 240, 240]  # 浅灰 - 可通行
        vis[self.grid == 1] = [50, 50, 50]     # 深灰 - 障碍物
        
        plt.imshow(vis, aspect='auto')
        
        # 绘制飞行路径（直线连接）
        path_x = [p[0] for p in waypoints]
        path_y = [p[1] for p in waypoints]
        
        # 绘制路径线（红色虚线表示飞行路径）
        plt.plot(path_x, path_y, 'r-', linewidth=2.5, label='无人机飞行路径', zorder=5)
        plt.plot(path_x, path_y, 'r--', linewidth=1, alpha=0.5, zorder=4)
        
        # 标记起点（绿色大圆）
        plt.plot(waypoints[0][0], waypoints[0][1], 'go', markersize=15, 
                 label='起点', zorder=10, markeredgecolor='darkgreen', markeredgewidth=2)
        plt.annotate('起点', (waypoints[0][0], waypoints[0][1] + 20), 
                    color='green', fontsize=12, ha='center', fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # 标记终点（红色大圆）
        plt.plot(waypoints[-1][0], waypoints[-1][1], 'ro', markersize=15, 
                 label='终点', zorder=10, markeredgecolor='darkred', markeredgewidth=2)
        plt.annotate('终点', (waypoints[-1][0], waypoints[-1][1] - 20), 
                    color='red', fontsize=12, ha='center', fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # 标记拱门中心点（蓝色圆点）和编号
        for i in range(1, len(waypoints) - 1):
            x, y = waypoints[i]
            plt.plot(x, y, 'bo', markersize=12, zorder=8, 
                    markeredgecolor='darkblue', markeredgewidth=2)
            
            # 拱门编号标签
            plt.annotate(f'{i}', (x, y), color='white', fontsize=10, 
                        ha='center', va='center', fontweight='bold', zorder=9)
            
            # 拱门名称（偏移显示）
            offset_x = 25 if i % 2 == 0 else -25
            plt.annotate(f'拱门{i}', (x + offset_x, y), color='blue', fontsize=9,
                        ha='center', va='center',
                        bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))
        
        # 标注各段距离
        for i in range(len(segment_distances)):
            x1, y1 = waypoints[i]
            x2, y2 = waypoints[i+1]
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            # 场地尺寸：左边黑墙44米(1129格)，下边黑墙17米(425格)
            METERS_PER_GRID_X = 17.0 / 425.0
            METERS_PER_GRID_Y = 44.0 / 1129.0
            dx_m = (x2 - x1) * METERS_PER_GRID_X
            dy_m = (y2 - y1) * METERS_PER_GRID_Y
            dist_m = np.sqrt(dx_m**2 + dy_m**2)
            
            # 计算文本角度
            angle = np.degrees(np.arctan2(y2-y1, x2-x1))
            
            # 距离标签（米）
            plt.annotate(f'{dist_m:.1f}m', (mid_x, mid_y), 
                        color='purple', fontsize=8, ha='center', va='center',
                        rotation=angle if abs(angle) < 90 else angle + 180,
                        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
        
        # 计算总距离（使用正确的比例）
        METERS_PER_GRID_X = 17.0 / 425.0
        METERS_PER_GRID_Y = 44.0 / 1129.0
        
        total_dist_m = 0
        for i in range(len(segment_distances)):
            x1, y1 = waypoints[i]
            x2, y2 = waypoints[i+1]
            dx_m = (x2 - x1) * METERS_PER_GRID_X
            dy_m = (y2 - y1) * METERS_PER_GRID_Y
            dist_m = np.sqrt(dx_m**2 + dy_m**2)
            total_dist_m += dist_m
        
        plt.title(f'无人机直飞最短路径 - 穿越拱门1-8\n总飞行距离: {total_dist_m:.2f} 米', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('X (格)')
        plt.ylabel('Y (格)')
        plt.legend(loc='upper right')
        
        # 添加拱门顺序说明
        order_text = "飞行顺序: 起点"
        for i in range(1, len(waypoints) - 1):
            order_text += f" → 拱门{i}"
        order_text += " → 终点"
        
        plt.figtext(0.5, 0.01, order_text, ha='center', fontsize=10, 
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # 保存图像
        output_path = "output/drone_flight_path.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"飞行路径图已保存: {output_path}")
    
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
    
    # 用户指定的起点和终点坐标
    manual_start = (350, 945)   # 起点
    manual_end = (350, 105)     # 终点
    
    # 选择规划模式
    mode = "drone"  # "ground" 或 "drone"
    
    if len(sys.argv) > 2:
        mode = sys.argv[2]
    
    if mode == "drone":
        # 无人机直飞路径：起点 -> 拱门1-8 -> 终点
        print("\n>>> 模式: 无人机直飞路径规划")
        flight_path = planner.find_drone_flight_path(image_path, manual_start, manual_end)
        
        if flight_path:
            print("\n" + "=" * 60)
            print("无人机直飞路径规划完成！")
            print(f"路径点数: {len(flight_path)}")
            print("输出文件:")
            print("  - output/drone_flight_path.png (可视化)")
            print("  - output/drone_flight_path.json (路径数据)")
            print("=" * 60)
    else:
        # 地面A*路径规划
        print("\n>>> 模式: 地面A*路径规划")
        path = planner.find_shortest_path(image_path, manual_start, manual_end)
        
        print("\n" + "=" * 60)
        print("路径规划完成！")
        print("=" * 60)
