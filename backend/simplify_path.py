"""
简化路径数据，提取关键航点
"""
import json
import numpy as np

def simplify_path(path, tolerance=15):
    """使用Douglas-Peucker算法简化路径"""
    if len(path) < 3:
        return path
    
    # 找到距离首尾连线最远的点
    start = np.array(path[0])
    end = np.array(path[-1])
    
    # 计算所有点到首尾连线的距离
    line_vec = end - start
    line_len = np.linalg.norm(line_vec)
    
    if line_len == 0:
        return [path[0], path[-1]]
    
    line_unit = line_vec / line_len
    
    max_dist = 0
    max_idx = 0
    
    for i in range(1, len(path) - 1):
        point = np.array(path[i])
        point_vec = point - start
        proj_len = np.dot(point_vec, line_unit)
        proj_point = start + proj_len * line_unit
        dist = np.linalg.norm(point - proj_point)
        
        if dist > max_dist:
            max_dist = dist
            max_idx = i
    
    if max_dist > tolerance:
        # 递归简化
        left = simplify_path(path[:max_idx + 1], tolerance)
        right = simplify_path(path[max_idx:], tolerance)
        return left[:-1] + right
    else:
        return [path[0], path[-1]]

def main():
    with open('output/path_data.json', 'r') as f:
        data = json.load(f)
    
    path = data['path']
    print(f"原始路径点数: {len(path)}")
    
    # 简化路径
    simplified = simplify_path(path, tolerance=20)
    print(f"简化后航点数: {len(simplified)}")
    
    # 输出JavaScript代码
    print("\n// 简化后的航点数据（复制到AutoControl.vue）")
    print("const carWaypoints = [")
    for p in simplified:
        print(f"  [{p[0]}, {p[1]}],")
    print("]")
    
    # 同时输出无人机航点（可能需要不同的路径）
    print("\n// 无人机航点（飞越迷宫上方）")
    print("const flightWaypoints = [")
    # 无人机从起点直接飞向终点（在高空）
    print(f"  [{data['start'][0]}, {data['start'][1]}],  // 起点")
    print(f"  [{data['end'][0]}, {data['end'][1]}],  // 终点")
    print("]")

if __name__ == "__main__":
    main()
