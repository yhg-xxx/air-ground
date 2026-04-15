"""
路径规划脚本
找出迷宫中从起点到终点的最短路径
"""

import numpy as np
import json
import cv2
import matplotlib.pyplot as plt
import matplotlib

# 配置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
import heapq
from scipy import interpolate


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
        
        # 构建拱门阻挡掩码
        self.build_gate_mask()
        
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
    
    def build_gate_mask(self):
        """预计算拱门阻挡掩码，用于快速判断坐标是否在拱门膨胀区域内"""
        self.gate_mask = np.zeros((self.rows, self.cols), dtype=bool)
        if not hasattr(self, 'gates') or not self.gates:
            return
        expansion = 2
        # 只处理拱门1和拱门9（第一个和最后一个）
        for i, gate in enumerate(self.gates):
            if i == 0 or i == len(self.gates) - 1:  # 只处理第一个和最后一个拱门
                cx, cy = gate['center']
                gw, gh = gate['width'], gate['height']
                x1 = max(0, int(cx - gw/2 - expansion))
                x2 = min(self.cols, int(cx + gw/2 + expansion))
                y1 = max(0, int(cy - gh/2 - expansion))
                y2 = min(self.rows, int(cy + gh/2 + expansion))
                self.gate_mask[y1:y2, x1:x2] = True
    
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
            # 16方向移动
            for dx, dy in [(-1,-1), (-1,0), (0,-1), (1,-1), (1,0) ]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.grid[ny, nx] == 0:  # 可通行
                        # 使用预计算的拱门阻挡掩码进行O(1)检查
                        if hasattr(self, 'gate_mask') and self.gate_mask[ny, nx]:
                            continue  # 在拱门区域内，禁止通行
                        # 计算实际欧氏距离作为移动代价
                        cost = np.sqrt(dx**2 + dy**2)
                        # 计算障碍物惩罚项（增强版）
                        obstacle_penalty = 0
                        # 检查周围8个方向的障碍物
                        for dx2, dy2 in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                            ox, oy = nx + dx2, ny + dy2
                            if 0 <= ox < self.cols and 0 <= oy < self.rows:
                                if self.grid[oy, ox] == 1:
                                    # 直接惩罚，不计算距离
                                    obstacle_penalty += 1.0
                        # 添加障碍物惩罚
                        cost += obstacle_penalty * 0.8  # 增加惩罚系数
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
    
    def smooth_path(self, path):
        """使用三次样条插值平滑路径"""
        if not path or len(path) < 3:
            return path
        
        # 提取路径坐标
        x = [p[0] for p in path]
        y = [p[1] for p in path]
        
        # 创建参数t，基于路径点之间的距离
        t = [0]
        for i in range(1, len(path)):
            dist = np.sqrt((x[i] - x[i-1])**2 + (y[i] - y[i-1])**2)
            t.append(t[-1] + dist)
        t = np.array(t)
        
        # 使用三次样条插值，增加平滑参数s
        s = len(path) * 0.15  # 平滑参数，越大越平滑
        tck_x = interpolate.splrep(t, x, s=s)
        tck_y = interpolate.splrep(t, y, s=s)
        
        # 生成更密集的点
        t_new = np.linspace(0, t[-1], int(len(path) * 2.5))
        x_new = interpolate.splev(t_new, tck_x)
        y_new = interpolate.splev(t_new, tck_y)
        
        # 转换为整数坐标并去重
        smooth_path = []
        seen = set()
        for i in range(len(x_new)):
            px = int(round(x_new[i]))
            py = int(round(y_new[i]))
            if (px, py) not in seen:
                smooth_path.append((px, py))
                seen.add((px, py))
        
        # 确保起点和终点在平滑路径中
        if smooth_path[0] != path[0]:
            smooth_path.insert(0, path[0])
        if smooth_path[-1] != path[-1]:
            smooth_path.append(path[-1])
        
        return smooth_path
    
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
        
        # 3. 路径平滑处理
        smooth_path = None
        if path:
            print(f"找到路径！总步数: {len(path)}")
            real_length = self.calculate_path_length(path)
            print(f"路径实际长度: {real_length:.2f} 米")
            
            # 平滑路径
            smooth_path = self.smooth_path(path)
            smooth_length = self.calculate_path_length(smooth_path)
            print(f"平滑后路径步数: {len(smooth_path)}")
            print(f"平滑后路径长度: {smooth_length:.2f} 米")
        else:
            print("未找到可行路径！")
            
        # 4. 可视化
        self.visualize_path(start, end, smooth_path or path)
        
        # 5. 保存路径数据
        if path:
            path_data = {
                "start": start,
                "end": end,
                "path": path,
                "smooth_path": smooth_path,
                "length_steps": len(path),
                "smooth_length_steps": len(smooth_path) if smooth_path else 0,
                "length_meters": self.calculate_path_length(path),
                "smooth_length_meters": self.calculate_path_length(smooth_path) if smooth_path else 0
            }
            
            with open("output/path_data.json", 'w') as f:
                json.dump(path_data, f, indent=2)
            print("路径数据已保存: output/path_data.json")
        
        return smooth_path or path


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
    manual_start = (320, 945)   # 起点
    manual_end = (330, 105)     # 终点
    
    # 寻找最短路径
    path = planner.find_shortest_path(image_path, manual_start, manual_end)
    
    print("\n" + "=" * 60)
    print("路径规划完成！")
    print("=" * 60)
