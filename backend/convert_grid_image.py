"""
手绘格栅图转换器
将黑白格栅图转换为二维数组数据
"""

import cv2
import numpy as np
import json
from pathlib import Path


def convert_grid_image(
    input_path: str,
    grid_cols: int = 150,  # 列数（宽度方向格子数）
    grid_rows: int = 60,   # 行数（高度方向格子数）
    output_dir: str = "output",
    wall_threshold: int = 128,  # 灰度阈值，低于此值为墙壁
    cyan_as_gate: bool = True   # 青色线条作为门（可通行）
):
    """
    将手绘格栅图转换为二维数组
    
    Args:
        input_path: 输入图像路径
        grid_cols: 格栅列数
        grid_rows: 格栅行数
        output_dir: 输出目录
        wall_threshold: 墙壁判定阈值
        cyan_as_gate: 是否将青色标记为门
    
    Returns:
        grid: 二维numpy数组 (0=可通行, 1=障碍物)
    """
    # 读取图像
    image = cv2.imdecode(np.fromfile(input_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取图像: {input_path}")
    
    img_h, img_w = image.shape[:2]
    print(f"图像尺寸: {img_w} x {img_h}")
    print(f"目标格栅: {grid_cols} x {grid_rows}")
    
    # 计算每个格子的像素大小
    cell_w = img_w / grid_cols
    cell_h = img_h / grid_rows
    print(f"每格像素: {cell_w:.2f} x {cell_h:.2f}")
    
    # 转灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 检测青色区域（门）
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    cyan_mask = cv2.inRange(hsv, np.array([80, 50, 50]), np.array([100, 255, 255]))
    
    # 创建格栅数组
    grid = np.zeros((grid_rows, grid_cols), dtype=np.uint8)
    
    # 逐格分析
    for row in range(grid_rows):
        for col in range(grid_cols):
            # 计算格子在图像中的区域
            x1 = int(col * cell_w)
            y1 = int(row * cell_h)
            x2 = int((col + 1) * cell_w)
            y2 = int((row + 1) * cell_h)
            
            # 提取格子区域
            cell_gray = gray[y1:y2, x1:x2]
            cell_cyan = cyan_mask[y1:y2, x1:x2]
            
            # 计算黑色像素比例（墙壁）
            black_ratio = np.sum(cell_gray < wall_threshold) / cell_gray.size
            
            # 计算青色像素比例（门）
            cyan_ratio = np.sum(cell_cyan > 0) / cell_cyan.size if cyan_as_gate else 0
            
            # 判定：如果有足够多的青色，认为是门（可通行）
            # 如果黑色比例高且没有青色，认为是墙壁
            if cyan_ratio > 0.1:
                grid[row, col] = 0  # 门，可通行
            elif black_ratio > 0.15:  # 超过15%是黑色则认为是墙壁
                grid[row, col] = 1  # 障碍物
            else:
                grid[row, col] = 0  # 可通行
    
    # 统计
    obstacle_count = np.sum(grid)
    passable_count = grid.size - obstacle_count
    print(f"\n转换结果:")
    print(f"  总格子数: {grid.size}")
    print(f"  障碍物格子: {obstacle_count} ({obstacle_count/grid.size*100:.1f}%)")
    print(f"  可通行格子: {passable_count} ({passable_count/grid.size*100:.1f}%)")
    
    # 保存结果
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 1. 保存为NPZ（numpy格式）
    npz_path = output_path / "grid_data.npz"
    np.savez(str(npz_path), 
             grid=grid, 
             cols=grid_cols, 
             rows=grid_rows,
             resolution=1/6,  # 米/格
             real_width=grid_cols * (1/6),
             real_height=grid_rows * (1/6))
    print(f"\nNPZ数据已保存: {npz_path}")
    
    # 2. 保存为JSON
    json_path = output_path / "grid_data.json"
    json_data = {
        "width": grid_cols,
        "height": grid_rows,
        "resolution": 1/6,
        "real_width": grid_cols * (1/6),
        "real_height": grid_rows * (1/6),
        "grid": grid.tolist()
    }
    with open(json_path, 'w') as f:
        json.dump(json_data, f)
    print(f"JSON数据已保存: {json_path}")
    
    # 3. 保存为CSV
    csv_path = output_path / "grid_data.csv"
    np.savetxt(str(csv_path), grid, fmt='%d', delimiter=',')
    print(f"CSV数据已保存: {csv_path}")
    
    # 4. 保存可视化图
    vis_path = output_path / "grid_visualization.png"
    save_visualization(grid, str(vis_path))
    print(f"可视化图已保存: {vis_path}")
    
    # 5. 检测蓝色拱门
    gates = detect_gates(input_path, grid_cols, grid_rows)
    if gates:
        print(f"检测到 {len(gates)} 个蓝色拱门:")
        for i, gate in enumerate(gates):
            print(f"  拱门{i+1}: 中心={gate['center']}, 尺寸={gate['width']}×{gate['height']}格")
    
    # 6. 保存带坐标的详细图（含拱门标注）
    detail_path = output_path / "grid_detail.png"
    save_detailed_visualization(grid, str(detail_path), grid_cols, grid_rows, gates)
    print(f"详细图已保存: {detail_path}")
    
    return grid


def save_visualization(grid: np.ndarray, output_path: str):
    """保存格栅可视化图"""
    h, w = grid.shape
    
    # 创建彩色可视化
    vis = np.zeros((h, w, 3), dtype=np.uint8)
    vis[grid == 0] = [144, 238, 144]  # 浅绿 - 可通行
    vis[grid == 1] = [50, 50, 50]     # 深灰 - 障碍物
    
    # 放大以便查看
    scale = max(1, 800 // max(h, w))
    vis_large = cv2.resize(vis, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)
    
    cv2.imwrite(output_path, vis_large)


def detect_gates(image_path: str, grid_cols: int, grid_rows: int):
    """检测蓝色拱门位置并返回格栅坐标"""
    image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return []
    
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # 检测蓝色/青色区域
    cyan_mask = cv2.inRange(hsv, np.array([80, 50, 50]), np.array([100, 255, 255]))
    
    # 找到连通区域
    contours, _ = cv2.findContours(cyan_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    gates = []
    img_h, img_w = image.shape[:2]
    cell_w = img_w / grid_cols
    cell_h = img_h / grid_rows
    
    for contour in contours:
        M = cv2.moments(contour)
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            # 转换为格栅坐标
            grid_x = int(cx / cell_w)
            grid_y = int(cy / cell_h)
            
            # 计算拱门的宽高（格栅单位）
            x, y, w, h = cv2.boundingRect(contour)
            gate_w = max(1, int(w / cell_w))
            gate_h = max(1, int(h / cell_h))
            
            gates.append({
                'center': (grid_x, grid_y),
                'width': gate_w,
                'height': gate_h,
                'pixel_y': cy,
                'pixel_x': cx
            })
    
    # 按照实际迷宫路径顺序排序（基于坐标位置手动指定顺序）
    gates = sort_gates_by_path_order(gates)
    return gates


def sort_gates_by_path_order(gates):
    """按照实际走迷宫的路径顺序排序拱门"""
    if not gates:
        return gates
    
    # 定义拱门的正确顺序（基于坐标位置）
    # 顺序: 1=起点(339,103), 2=(331,943), 3=(295,1003), 4=(219,1087), 
    #        5=(131,999), 6=(19,1087), 7=(75,1167), 8=(323,1167), 9=终点(391,1107)
    
    # 根据坐标位置匹配顺序
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
        
        if best_gate and best_dist < 50:  # 允许一定误差
            sorted_gates.append(best_gate)
            used.add(best_idx)
    
    # 添加未匹配的拱门
    for i, gate in enumerate(gates):
        if i not in used:
            sorted_gates.append(gate)
    
    return sorted_gates


def save_detailed_visualization(grid: np.ndarray, output_path: str, cols: int, rows: int, 
                                  gates: list = None):
    """保存带网格线和坐标的详细可视化"""
    import matplotlib.pyplot as plt
    import matplotlib
    # 配置中文字体
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    
    # 按真实比例计算图像尺寸
    aspect_ratio = cols / rows  # 宽/高比例
    if aspect_ratio > 1:
        # 宽图
        fig_width = 16
        fig_height = 16 / aspect_ratio
    else:
        # 高图  
        fig_height = 20
        fig_width = 20 * aspect_ratio
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # 创建颜色映射
    cmap = plt.cm.colors.ListedColormap(['lightgreen', 'dimgray'])
    
    ax.imshow(grid, cmap=cmap, aspect='auto')
    
    # 添加网格线（每10格一条粗线）
    for i in range(0, cols + 1, 10):
        ax.axvline(x=i - 0.5, color='black', linewidth=0.5 if i % 50 != 0 else 1.5)
    for i in range(0, rows + 1, 10):
        ax.axhline(y=i - 0.5, color='black', linewidth=0.5 if i % 50 != 0 else 1.5)
    
    # 设置刻度
    ax.set_xticks(range(0, cols, 10))
    ax.set_yticks(range(0, rows, 10))
    # 标注蓝色拱门
    if gates:
        for i, gate in enumerate(gates):
            cx, cy = gate['center']
            gw, gh = gate['width'], gate['height']
            
            # 画矩形标注
            rect = plt.Rectangle((cx - gw/2 - 0.5, cy - gh/2 - 0.5), gw, gh,
                                  linewidth=2, edgecolor='blue', facecolor='cyan', alpha=0.5)
            ax.add_patch(rect)
            
            # 添加文字标签
            label = f'拱门{i+1}'
            ax.annotate(label, (cx, cy), color='blue', fontsize=8, 
                        ha='center', va='center', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_xlabel(f'X (格) - 共{cols}列')
    ax.set_ylabel(f'Y (格) - 共{rows}行')
    ax.set_title(f'格栅地图 {cols}×{rows} (绿色=可通行, 灰色=障碍物, 蓝色=拱门)')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def print_grid_section(grid: np.ndarray, start_row=0, start_col=0, rows=20, cols=30):
    """打印格栅的一部分（用于调试）"""
    print(f"\n格栅数据预览 [{start_row}:{start_row+rows}, {start_col}:{start_col+cols}]:")
    print("  " + "".join([f"{i%10}" for i in range(start_col, min(start_col+cols, grid.shape[1]))]))
    
    for r in range(start_row, min(start_row + rows, grid.shape[0])):
        row_str = "".join(['█' if grid[r, c] == 1 else '·' for c in range(start_col, min(start_col+cols, grid.shape[1]))])
        print(f"{r:2d} {row_str}")


if __name__ == "__main__":
    import sys
    
    # 默认参数
    default_input = r"d:\pythonCodes\air-ground\backend\grid-1775449079133_upscaled_3.0x.png"
    default_cols = 480
    default_rows = 1200
    
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else default_cols
    rows = int(sys.argv[3]) if len(sys.argv) > 3 else default_rows
    
    print("=" * 60)
    print("手绘格栅图转换器")
    print("=" * 60)
    
    grid = convert_grid_image(
        input_path=input_path,
        grid_cols=cols,
        grid_rows=rows
    )
    
    # 打印部分格栅数据预览
    print_grid_section(grid, 0, 0, 15, 40)
    
    print("\n" + "=" * 60)
    print("转换完成！")
    print(f"格栅尺寸: {cols} × {rows}")
    print(f"物理尺寸: {cols/6:.1f}m × {rows/6:.1f}m")
    print("=" * 60)
