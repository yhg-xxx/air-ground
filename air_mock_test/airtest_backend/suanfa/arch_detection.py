import cv2
import numpy as np
import base64
import math
from typing import List, Dict, Tuple, Optional


class ArchDetectionController:
    """拱门识别算法控制器
    
    用于无人机在飞行过程中快速检测并定位拱门障碍，实现精准穿越。
    算法流程：
    1. 图像预处理：灰度化、高斯模糊、边缘检测
    2. 形态学操作过滤噪声
    3. 筛选符合拱门几何特征的连通区域
    4. 结合颜色与轮廓比例约束识别拱门
    5. 计算相对位置与偏航角，输出穿越目标点
    """
    
    def __init__(self):
        # 相机参数
        self.camera_resolution = (1280, 720)
        self.focal_length = 1000  # 焦距（像素）
        self.camera_center = (self.camera_resolution[0] // 2, self.camera_resolution[1] // 2)
        
        # 拱门几何特征参数
        self.arch_aspect_ratio_range = (0.3, 2.0)  # 宽高比范围（拱门通常较宽或较高）
        self.arch_area_range = (5000, 100000)  # 面积范围
        self.arch_circularity_range = (0.3, 0.9)  # 圆度范围（拱门有一定曲线特征）
        
        # 颜色约束参数（拱门的典型颜色范围）
        self.arch_color_lower = np.array([0, 50, 50])  # HSV下限
        self.arch_color_upper = np.array([180, 255, 255])  # HSV上限
        
        # 检测参数
        self.canny_threshold1 = 50
        self.canny_threshold2 = 150
        self.morph_kernel_size = 5
        
    def decode_image(self, image_data: str) -> Optional[np.ndarray]:
        """解码base64图像数据"""
        try:
            # 移除data URL前缀（如果有）
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Base64解码
            image_bytes = base64.b64decode(image_data)
            
            # 转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("图像解码失败")
            
            # 调整图像分辨率
            image = cv2.resize(image, self.camera_resolution)
                
            return image
        except Exception as e:
            print(f"图像解码错误: {e}")
            return None
    
    def preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """图像预处理
        
        Returns:
            gray: 灰度图
            blurred: 高斯模糊后的图像
            edges: 边缘检测结果
        """
        # 1. 灰度化
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 2. 高斯模糊 - 去除噪声
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. 边缘检测 - Canny算法
        edges = cv2.Canny(blurred, self.canny_threshold1, self.canny_threshold2)
        
        return gray, blurred, edges
    
    def morphological_operation(self, edges: np.ndarray) -> np.ndarray:
        """形态学操作过滤噪声
        
        Args:
            edges: 边缘检测结果
            
        Returns:
            形态学处理后的二值图像
        """
        # 创建形态学核
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, 
            (self.morph_kernel_size, self.morph_kernel_size)
        )
        
        # 闭运算 - 填充小空洞，连接断裂边缘
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 开运算 - 去除小噪声点
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)
        
        return opened
    
    def calculate_circularity(self, contour: np.ndarray) -> float:
        """计算轮廓的圆度"""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return 0
        # 圆度 = 4π * 面积 / 周长²（圆的圆度为1）
        return 4 * np.pi * area / (perimeter ** 2)
    
    def calculate_contour_features(self, contour: np.ndarray) -> Dict:
        """计算轮廓的几何特征"""
        # 外接矩形
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0
        
        # 面积
        area = cv2.contourArea(contour)
        
        # 周长
        perimeter = cv2.arcLength(contour, True)
        
        # 圆度
        circularity = self.calculate_circularity(contour)
        
        # 凸包面积比
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # 中心点
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + w // 2, y + h // 2
        
        return {
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'aspect_ratio': aspect_ratio,
            'area': area,
            'perimeter': perimeter,
            'circularity': circularity,
            'solidity': solidity,
            'center_x': cx,
            'center_y': cy,
            'contour': contour
        }
    
    def is_arch_shape(self, features: Dict) -> bool:
        """判断是否符合拱门几何特征"""
        # 检查宽高比
        if not (self.arch_aspect_ratio_range[0] <= features['aspect_ratio'] <= self.arch_aspect_ratio_range[1]):
            return False
        
        # 检查面积
        if not (self.arch_area_range[0] <= features['area'] <= self.arch_area_range[1]):
            return False
        
        # 检查圆度（拱门应有曲线特征，圆度在0.3-0.9之间）
        if not (self.arch_circularity_range[0] <= features['circularity'] <= self.arch_circularity_range[1]):
            return False
        
        # 检查凸包面积比（拱门通常是凸的）
        if features['solidity'] < 0.7:
            return False
        
        return True
    
    def filter_by_color(self, image: np.ndarray, contour: np.ndarray) -> float:
        """基于颜色约束筛选拱门
        
        Returns:
            颜色匹配得分（0-1）
        """
        # 创建掩码
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 计算颜色范围内的像素比例
        color_mask = cv2.inRange(hsv, self.arch_color_lower, self.arch_color_upper)
        color_mask = cv2.bitwise_and(color_mask, mask)
        
        # 计算匹配比例
        total_pixels = cv2.countNonZero(mask)
        color_pixels = cv2.countNonZero(color_mask)
        
        if total_pixels == 0:
            return 0
        
        return color_pixels / total_pixels
    
    def detect_arch(self, image: np.ndarray) -> List[Dict]:
        """检测拱门
        
        Args:
            image: 输入图像
            
        Returns:
            检测到的拱门列表，按置信度排序
        """
        # 1. 预处理
        gray, blurred, edges = self.preprocess(image)
        
        # 2. 形态学操作
        morph = self.morphological_operation(edges)
        
        # 3. 查找连通区域
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 4. 筛选符合拱门特征的轮廓
        arch_candidates = []
        
        for contour in contours:
            # 计算轮廓特征
            features = self.calculate_contour_features(contour)
            
            # 几何特征筛选
            if not self.is_arch_shape(features):
                continue
            
            # 颜色筛选
            color_score = self.filter_by_color(image, contour)
            
            # 计算综合置信度
            confidence = self.calculate_arch_confidence(features, color_score)
            
            if confidence > 0.5:  # 置信度阈值
                features['confidence'] = confidence
                features['color_score'] = color_score
                arch_candidates.append(features)
        
        # 按置信度排序
        arch_candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        return arch_candidates
    
    def calculate_arch_confidence(self, features: Dict, color_score: float) -> float:
        """计算拱门识别置信度"""
        # 基于面积评分（适中面积得分更高）
        ideal_area = 30000
        area_score = 1.0 - min(abs(features['area'] - ideal_area) / ideal_area, 1.0)
        
        # 基于宽高比评分（拱门通常宽高比在0.5-1.5之间）
        ideal_ratio = 1.0
        ratio_score = 1.0 - min(abs(features['aspect_ratio'] - ideal_ratio), 1.0)
        
        # 基于圆度评分
        ideal_circularity = 0.6
        circularity_score = 1.0 - min(abs(features['circularity'] - ideal_circularity) / 0.6, 1.0)
        
        # 综合置信度（加权平均）
        confidence = (
            area_score * 0.3 +
            ratio_score * 0.3 +
            circularity_score * 0.2 +
            color_score * 0.2
        )
        
        return confidence
    
    def calculate_relative_position(self, arch_features: Dict, image_shape: Tuple[int, int]) -> Dict:
        """计算无人机与拱门的相对位置
        
        Args:
            arch_features: 拱门特征
            image_shape: 图像尺寸 (width, height)
            
        Returns:
            相对位置信息
        """
        img_w, img_h = image_shape
        
        # 拱门中心点在图像中的位置
        arch_cx = arch_features['center_x']
        arch_cy = arch_features['center_y']
        
        # 计算相对于图像中心的位置偏移
        dx = arch_cx - self.camera_center[0]
        dy = arch_cy - self.camera_center[1]
        
        # 归一化位置（-1到1）
        nx = dx / (img_w / 2)
        ny = dy / (img_h / 2)
        
        # 估算距离（基于拱门在图像中的大小）
        # 假设标准拱门宽度为1米
        arch_width_pixels = arch_features['width']
        if arch_width_pixels > 0:
            estimated_distance = (self.focal_length * 1.0) / arch_width_pixels
        else:
            estimated_distance = 10.0
        
        # 计算偏航角（水平方向）
        yaw_angle = math.atan2(dx, self.focal_length) * 180 / math.pi
        
        # 计算俯仰角（垂直方向）
        pitch_angle = math.atan2(dy, self.focal_length) * 180 / math.pi
        
        return {
            'dx': dx,  # 像素偏移x
            'dy': dy,  # 像素偏移y
            'nx': nx,  # 归一化位置x
            'ny': ny,  # 归一化位置y
            'distance': estimated_distance,  # 估算距离（米）
            'yaw_angle': yaw_angle,  # 偏航角（度）
            'pitch_angle': pitch_angle,  # 俯仰角（度）
            'arch_width': arch_features['width'],
            'arch_height': arch_features['height']
        }
    
    def calculate_crossing_target(self, arch_features: Dict, position: Dict) -> Dict:
        """计算穿越目标点
        
        Args:
            arch_features: 拱门特征
            position: 相对位置信息
            
        Returns:
            穿越目标点信息
        """
        # 拱门中心作为穿越目标点
        target_x = arch_features['center_x']
        target_y = arch_features['center_y']
        
        # 计算需要调整的控制指令
        commands = []
        
        # 水平调整（左右）
        if abs(position['nx']) > 0.1:  # 水平偏移超过10%
            if position['nx'] > 0:
                # 拱门在右侧，需要右移
                commands.append({
                    'channel': 3,
                    'value': 1600 + int(400 * min(position['nx'], 1.0)),
                    'description': '向右调整'
                })
            else:
                # 拱门在左侧，需要左移
                commands.append({
                    'channel': 3,
                    'value': 1400 - int(400 * min(abs(position['nx']), 1.0)),
                    'description': '向左调整'
                })
        
        # 垂直调整（上下）
        if abs(position['ny']) > 0.1:  # 垂直偏移超过10%
            if position['ny'] > 0:
                # 拱门在下方，需要下降
                commands.append({
                    'channel': 2,
                    'value': 1400 - int(400 * min(position['ny'], 1.0)),
                    'description': '向下调整'
                })
            else:
                # 拱门在上方，需要上升
                commands.append({
                    'channel': 2,
                    'value': 1600 + int(400 * min(abs(position['ny']), 1.0)),
                    'description': '向上调整'
                })
        
        # 方向调整（偏航角）
        if abs(position['yaw_angle']) > 5:  # 偏航角超过5度
            if position['yaw_angle'] > 0:
                commands.append({
                    'channel': 1,
                    'value': 1600 + int(400 * min(position['yaw_angle'] / 45, 1.0)),
                    'description': '向右偏航'
                })
            else:
                commands.append({
                    'channel': 1,
                    'value': 1400 - int(400 * min(abs(position['yaw_angle']) / 45, 1.0)),
                    'description': '向左偏航'
                })
        
        # 前进指令（当对准后）
        if abs(position['nx']) < 0.2 and abs(position['ny']) < 0.2 and abs(position['yaw_angle']) < 10:
            commands.append({
                'channel': 4,
                'value': 1800,  # 中等速度前进
                'description': '前进穿越拱门'
            })
        
        return {
            'target_x': target_x,
            'target_y': target_y,
            'commands': commands,
            'can_cross': len([c for c in commands if c['channel'] == 4]) > 0
        }
    
    def process_image(self, image_data: str) -> Dict:
        """处理图像并返回拱门识别结果
        
        Args:
            image_data: base64编码的图像数据
            
        Returns:
            识别结果字典
        """
        # 解码图像
        image = self.decode_image(image_data)
        if image is None:
            return {
                'success': False,
                'message': '图像解码失败'
            }
        
        # 检测拱门
        arches = self.detect_arch(image)
        
        if not arches:
            return {
                'success': False,
                'message': '未检测到拱门'
            }
        
        # 取置信度最高的拱门
        best_arch = arches[0]
        
        # 计算相对位置
        position = self.calculate_relative_position(best_arch, image.shape[:2][::-1])
        
        # 计算穿越目标点
        target = self.calculate_crossing_target(best_arch, position)
        
        return {
            'success': True,
            'arch_detected': True,
            'arch': {
                'confidence': best_arch['confidence'],
                'area': best_arch['area'],
                'aspect_ratio': best_arch['aspect_ratio'],
                'circularity': best_arch['circularity'],
                'center': (best_arch['center_x'], best_arch['center_y']),
                'bbox': (best_arch['x'], best_arch['y'], best_arch['width'], best_arch['height']),
                'color_score': best_arch['color_score']
            },
            'position': position,
            'target': target,
            'total_candidates': len(arches)
        }
    
    def get_debug_image(self, image_data: str, result: Dict) -> np.ndarray:
        """生成调试图像，标注检测结果
        
        Args:
            image_data: base64编码的图像数据
            result: 检测结果
            
        Returns:
            标注后的图像
        """
        image = self.decode_image(image_data)
        if image is None:
            return None
        
        if not result.get('success') or not result.get('arch_detected'):
            cv2.putText(image, "No arch detected", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return image
        
        arch = result['arch']
        position = result['position']
        target = result['target']
        
        # 绘制拱门边界框
        x, y, w, h = arch['bbox']
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 绘制中心点
        cx, cy = arch['center']
        cv2.circle(image, (cx, cy), 5, (0, 0, 255), -1)
        
        # 绘制中心十字线
        cv2.line(image, (cx - 20, cy), (cx + 20, cy), (255, 0, 0), 2)
        cv2.line(image, (cx, cy - 20), (cx, cy + 20), (255, 0, 0), 2)
        
        # 绘制图像中心十字线
        img_cx, img_cy = self.camera_center
        cv2.line(image, (img_cx - 30, img_cy), (img_cx + 30, img_cy), (255, 255, 0), 2)
        cv2.line(image, (img_cx, img_cy - 30), (img_cx, img_cy + 30), (255, 255, 0), 2)
        
        # 添加文字信息
        info_texts = [
            f"Confidence: {arch['confidence']:.2f}",
            f"Distance: {position['distance']:.2f}m",
            f"Yaw: {position['yaw_angle']:.1f}deg",
            f"Offset: ({position['nx']:.2f}, {position['ny']:.2f})",
            f"CanCross: {target['can_cross']}"
        ]
        
        y_offset = 30
        for text in info_texts:
            cv2.putText(image, text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += 30
        
        return image


# 全局实例
arch_detection_controller = ArchDetectionController()
