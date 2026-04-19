"""
从grid_data提取墙壁轮廓，直接输出前端JavaScript代码
"""
import json
import numpy as np
from pathlib import Path

def extract_wall_contours(grid_path: str):
    """从格栅数据提取墙壁轮廓线"""
    with open(grid_path, 'r') as f:
        data = json.load(f)
    
    grid = np.array(data['grid'], dtype=np.uint8)
    rows, cols = grid.shape
    print(f"格栅尺寸: {cols} x {rows}")
    
    walls = []
    
    # 找水平边界（墙壁的上边缘和下边缘）
    for y in range(1, rows):
        in_segment = False
        start_x = 0
        for x in range(cols):
            # 检测从0到1的变化（墙壁上边缘）或从1到0（墙壁下边缘）
            curr = grid[y, x]
            prev = grid[y-1, x]
            is_edge = (curr == 1 and prev == 0) or (curr == 0 and prev == 1)
            
            if is_edge and not in_segment:
                start_x = x
                in_segment = True
            elif not is_edge and in_segment:
                if x - start_x > 20:  # 最小长度
                    walls.append({'x1': start_x, 'y1': y, 'x2': x-1, 'y2': y})
                in_segment = False
        
        if in_segment and cols - start_x > 20:
            walls.append({'x1': start_x, 'y1': y, 'x2': cols-1, 'y2': y})
    
    # 找垂直边界
    for x in range(1, cols):
        in_segment = False
        start_y = 0
        for y in range(rows):
            curr = grid[y, x]
            prev = grid[y, x-1]
            is_edge = (curr == 1 and prev == 0) or (curr == 0 and prev == 1)
            
            if is_edge and not in_segment:
                start_y = y
                in_segment = True
            elif not is_edge and in_segment:
                if y - start_y > 30:  # 最小长度
                    walls.append({'x1': x, 'y1': start_y, 'x2': x, 'y2': y-1})
                in_segment = False
        
        if in_segment and rows - start_y > 30:
            walls.append({'x1': x, 'y1': start_y, 'x2': x, 'y2': rows-1})
    
    print(f"提取了 {len(walls)} 条墙壁边界线")
    
    # 输出JavaScript代码
    print("\n// 墙壁数据（直接复制到AutoControl.vue）")
    print("const mazeWalls = [")
    for w in walls:
        print(f"  {{ x1: {w['x1']}, y1: {w['y1']}, x2: {w['x2']}, y2: {w['y2']} }},")
    print("]")
    
    return walls

def extract_wall_segments(grid_path: str, output_path: str, sample_rate: int = 8):
    """
    从格栅数据提取墙壁线段（连续扫描法）
    """
    with open(grid_path, 'r') as f:
        data = json.load(f)
    
    grid = np.array(data['grid'], dtype=np.uint8)
    rows, cols = grid.shape
    print(f"格栅尺寸: {cols} x {rows}")
    
    h_segments = []  # 水平线段
    v_segments = []  # 垂直线段
    
    # 扫描水平线段（每sample_rate行扫描一次）
    for y in range(0, rows, sample_rate):
        in_wall = False
        start_x = 0
        for x in range(cols):
            is_wall = grid[y, x] == 1
            if is_wall and not in_wall:
                start_x = x
                in_wall = True
            elif not is_wall and in_wall:
                if x - start_x > 5:  # 墙段长度阈值
                    h_segments.append({'x1': start_x, 'y1': y, 'x2': x, 'y2': y})
                in_wall = False
        if in_wall and cols - start_x > 5:
            h_segments.append({'x1': start_x, 'y1': y, 'x2': cols, 'y2': y})
    
    # 扫描垂直线段（每sample_rate列扫描一次）
    for x in range(0, cols, sample_rate):
        in_wall = False
        start_y = 0
        for y in range(rows):
            is_wall = grid[y, x] == 1
            if is_wall and not in_wall:
                start_y = y
                in_wall = True
            elif not is_wall and in_wall:
                if y - start_y > 10:  # 垂直墙段长度阈值
                    v_segments.append({'x1': x, 'y1': start_y, 'x2': x, 'y2': y})
                in_wall = False
        if in_wall and rows - start_y > 10:
            v_segments.append({'x1': x, 'y1': start_y, 'x2': x, 'y2': rows})
    
    # 简单合并：只合并紧邻行/列的线段
    h_merged = merge_nearby_h_segments(h_segments, y_threshold=sample_rate + 4)
    v_merged = merge_nearby_v_segments(v_segments, x_threshold=sample_rate + 4)
    
    all_segments = h_merged + v_merged
    
    print(f"水平线段: {len(h_merged)}, 垂直线段: {len(v_merged)}")
    print(f"总计: {len(all_segments)} 条墙壁线段")
    
    result = {
        'width': cols,
        'height': rows,
        'walls': all_segments
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"保存到: {output_path}")
    return all_segments

def smart_merge_h(segments, y_threshold):
    """智能合并水平线段：只合并y相近且x范围大部分重叠的线段"""
    if not segments:
        return []
    
    # 按y坐标排序
    segments.sort(key=lambda s: s['y1'])
    
    merged = []
    used = set()
    
    for i, seg in enumerate(segments):
        if i in used:
            continue
        
        current = seg.copy()
        # 查找可合并的线段
        for j in range(i + 1, len(segments)):
            if j in used:
                continue
            next_seg = segments[j]
            
            # y相差超过阈值，停止查找
            if next_seg['y1'] - current['y1'] > y_threshold:
                break
            
            # 检查x范围是否大部分重叠（至少70%重叠）
            overlap = min(current['x2'], next_seg['x2']) - max(current['x1'], next_seg['x1'])
            length1 = current['x2'] - current['x1']
            length2 = next_seg['x2'] - next_seg['x1']
            min_len = min(length1, length2)
            
            if overlap > min_len * 0.7:  # 70%重叠才合并
                current['x1'] = min(current['x1'], next_seg['x1'])
                current['x2'] = max(current['x2'], next_seg['x2'])
                current['y1'] = (current['y1'] + next_seg['y1']) // 2
                current['y2'] = current['y1']
                used.add(j)
        
        merged.append(current)
    
    return merged

def smart_merge_v(segments, x_threshold):
    """智能合并垂直线段：只合并x相近且y范围大部分重叠的线段"""
    if not segments:
        return []
    
    # 按x坐标排序
    segments.sort(key=lambda s: s['x1'])
    
    merged = []
    used = set()
    
    for i, seg in enumerate(segments):
        if i in used:
            continue
        
        current = seg.copy()
        for j in range(i + 1, len(segments)):
            if j in used:
                continue
            next_seg = segments[j]
            
            if next_seg['x1'] - current['x1'] > x_threshold:
                break
            
            overlap = min(current['y2'], next_seg['y2']) - max(current['y1'], next_seg['y1'])
            length1 = current['y2'] - current['y1']
            length2 = next_seg['y2'] - next_seg['y1']
            min_len = min(length1, length2)
            
            if overlap > min_len * 0.7:  # 70%重叠才合并
                current['y1'] = min(current['y1'], next_seg['y1'])
                current['y2'] = max(current['y2'], next_seg['y2'])
                current['x1'] = (current['x1'] + next_seg['x1']) // 2
                current['x2'] = current['x1']
                used.add(j)
        
        merged.append(current)
    
    return merged

def merge_nearby_h_segments(segments, y_threshold=20):
    """合并y坐标相近的水平线段"""
    if not segments:
        return []
    
    segments.sort(key=lambda s: s['y1'])
    merged = []
    current_group = [segments[0]]
    
    for seg in segments[1:]:
        if abs(seg['y1'] - current_group[-1]['y1']) < y_threshold:
            current_group.append(seg)
        else:
            merged.append(merge_h_group(current_group))
            current_group = [seg]
    
    if current_group:
        merged.append(merge_h_group(current_group))
    
    return merged

def merge_h_group(group):
    """合并一组水平线段"""
    avg_y = int(sum(s['y1'] for s in group) / len(group))
    min_x = min(s['x1'] for s in group)
    max_x = max(s['x2'] for s in group)
    return {'x1': min_x, 'y1': avg_y, 'x2': max_x, 'y2': avg_y}

def merge_nearby_v_segments(segments, x_threshold=15):
    """合并x坐标相近的垂直线段"""
    if not segments:
        return []
    
    segments.sort(key=lambda s: s['x1'])
    merged = []
    current_group = [segments[0]]
    
    for seg in segments[1:]:
        if abs(seg['x1'] - current_group[-1]['x1']) < x_threshold:
            current_group.append(seg)
        else:
            merged.append(merge_v_group(current_group))
            current_group = [seg]
    
    if current_group:
        merged.append(merge_v_group(current_group))
    
    return merged

def merge_v_group(group):
    """合并一组垂直线段"""
    avg_x = int(sum(s['x1'] for s in group) / len(group))
    min_y = min(s['y1'] for s in group)
    max_y = max(s['y2'] for s in group)
    return {'x1': avg_x, 'y1': min_y, 'x2': avg_x, 'y2': max_y}

def extract_wall_blocks(grid_path: str, sample: int = 8):
    """采样格栅数据，生成墙壁块列表（改进版：检测任何有墙壁的区域）"""
    with open(grid_path, 'r') as f:
        data = json.load(f)
    
    grid = np.array(data['grid'], dtype=np.uint8)
    rows, cols = grid.shape
    print(f"格栅尺寸: {cols} x {rows}")
    
    blocks = []
    # 每sample个格子采样一次
    for y in range(0, rows, sample):
        for x in range(0, cols, sample):
            # 检查这个区域是否有墙壁（任何墙壁像素）
            region = grid[y:min(y+sample, rows), x:min(x+sample, cols)]
            if np.any(region == 1):  # 只要有墙壁就标记
                blocks.append({'x': x, 'y': y, 'w': sample, 'h': sample})
    
    print(f"生成了 {len(blocks)} 个墙壁块")
    
    # 保存为JSON
    result = {'width': cols, 'height': rows, 'sample': sample, 'blocks': blocks}
    with open('output/wall_blocks.json', 'w') as f:
        json.dump(result, f)
    
    print("保存到 output/wall_blocks.json")
    return blocks

def extract_wall_lines(grid_path: str):
    """提取主要墙壁线条（水平和垂直）"""
    with open(grid_path, 'r') as f:
        data = json.load(f)
    
    grid = np.array(data['grid'], dtype=np.uint8)
    rows, cols = grid.shape
    print(f"格栅尺寸: {cols} x {rows}")
    
    walls = []
    
    # 检测水平墙壁线（扫描每隔一定间距的行）
    for y in range(0, rows, 8):
        in_wall = False
        start_x = 0
        wall_count = 0
        for x in range(cols):
            # 检查该列附近几行是否有连续墙壁
            has_wall = np.sum(grid[max(0,y-2):min(rows,y+3), x]) >= 3
            if has_wall and not in_wall:
                start_x = x
                in_wall = True
                wall_count = 1
            elif has_wall and in_wall:
                wall_count += 1
            elif not has_wall and in_wall:
                if wall_count > 30:  # 最小墙壁长度
                    walls.append({'x1': start_x, 'y1': y, 'x2': x-1, 'y2': y, 'type': 'h'})
                in_wall = False
        if in_wall and wall_count > 30:
            walls.append({'x1': start_x, 'y1': y, 'x2': cols-1, 'y2': y, 'type': 'h'})
    
    # 检测垂直墙壁线
    for x in range(0, cols, 8):
        in_wall = False
        start_y = 0
        wall_count = 0
        for y in range(rows):
            has_wall = np.sum(grid[y, max(0,x-2):min(cols,x+3)]) >= 3
            if has_wall and not in_wall:
                start_y = y
                in_wall = True
                wall_count = 1
            elif has_wall and in_wall:
                wall_count += 1
            elif not has_wall and in_wall:
                if wall_count > 50:  # 垂直墙最小长度
                    walls.append({'x1': x, 'y1': start_y, 'x2': x, 'y2': y-1, 'type': 'v'})
                in_wall = False
        if in_wall and wall_count > 50:
            walls.append({'x1': x, 'y1': start_y, 'x2': x, 'y2': rows-1, 'type': 'v'})
    
    print(f"提取了 {len(walls)} 条墙壁线")
    
    # 保存
    result = {'width': cols, 'height': rows, 'walls': walls}
    with open('output/wall_lines.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    return walls

if __name__ == "__main__":
    output_dir = Path("output")
    
    # 使用线条提取法
    walls = extract_wall_lines(str(output_dir / "grid_data.json"))
    
    # 输出JS代码
    print("\n// 墙壁线段数据")
    print("const mazeWalls = [")
    for w in walls:
        print(f"  {{x1:{w['x1']},y1:{w['y1']},x2:{w['x2']},y2:{w['y2']}}},")
    print("]")
