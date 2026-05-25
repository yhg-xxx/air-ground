import cv2
import cv2.aruco as aruco
import numpy as np
import base64
import math
from typing import Dict, Optional, Tuple, List


class ArucoDetectionController:
    """ArUco码识别算法控制器
    
    用于无人机精准降落阶段识别无人车顶部的ArUco标记，实现厘米级精度的自主降落。
    算法流程：
    1. 图像解码与预处理：解码base64图像，调整分辨率
    2. ArUco标记检测：使用OpenCV ArUco库检测标记
    3. 位姿估计：通过solvePnP计算相对位置与姿态
    4. 控制指令生成：根据相对位置计算降落控制指令
    """
    
    def __init__(self):
        # 相机参数
        self.camera_resolution = (1280, 720)
        self.focal_length = 1000  # 焦距（像素）
        self.camera_center = (self.camera_resolution[0] // 2, self.camera_resolution[1] // 2)
        
        # ArUco标记参数
        self.marker_length = 0.2  # 标记实际边长，单位：米（20cm）
        self.coordinate_system = 1  # 1: 中心坐标系, 0: 左上角坐标系
        
        # 初始化相机内参矩阵
        width, height = self.camera_resolution
        self.camera_matrix = np.array([
            [width, 0, width / 2],
            [0, width, height / 2],
            [0, 0, 1]
        ], dtype=np.float32)
        self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)
        
        # 创建ArUco检测器
        dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(dictionary, parameters)
        
        # 精准降落控制参数
        self.target_height = 0.3  # 目标降落高度（米）
        self.landing_threshold = 0.1  # 降落判定阈值（米）
        self.horizontal_threshold = 0.15  # 水平对齐阈值（米）
        self.alignment_threshold = 0.05  # 精对准阈值（米）
        
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
    
    def get_object_points(self) -> np.ndarray:
        """获取3D物体点（ArUco标记的四个角点）"""
        if self.coordinate_system == 1:
            # 中心坐标系
            half_size = self.marker_length / 2.0
            return np.array([
                [-half_size, half_size, 0],
                [half_size, half_size, 0],
                [half_size, -half_size, 0],
                [-half_size, -half_size, 0]
            ], dtype=np.float32)
        else:
            # 左上角坐标系
            return np.array([
                [0, 0, 0],
                [self.marker_length, 0, 0],
                [self.marker_length, self.marker_length, 0],
                [0, self.marker_length, 0]
            ], dtype=np.float32)
    
    def detect_aruco(self, image: np.ndarray) -> Dict:
        """检测ArUco标记并计算位姿
        
        Args:
            image: 输入图像
            
        Returns:
            检测结果字典
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 检测ArUco标记
            corners, ids, rejected = self.detector.detectMarkers(gray)
            
            if ids is not None and len(ids) > 0:
                # 获取物体点
                object_points = self.get_object_points()
                
                # 对第一个检测到的标记进行姿态估计
                marker_corners = corners[0].reshape(-1, 2)
                
                success, rvec, tvec = cv2.solvePnP(
                    object_points,
                    marker_corners.astype(np.float32),
                    self.camera_matrix,
                    self.dist_coeffs
                )
                
                if success:
                    # 计算相对位置
                    x_offset = tvec[0][0]  # 左右偏移（米）
                    y_offset = tvec[1][0]  # 前后偏移（米）
                    z_offset = tvec[2][0]  # 高度（米）
                    distance = np.linalg.norm(tvec)  # 总距离
                    
                    # 计算旋转矩阵
                    rotation_matrix, _ = cv2.Rodrigues(rvec)
                    
                    # 计算欧拉角（俯仰、偏航、滚转）
                    pitch = math.atan2(rotation_matrix[2][1], rotation_matrix[2][2])
                    yaw = math.atan2(-rotation_matrix[2][0], 
                                    math.sqrt(rotation_matrix[2][1]**2 + rotation_matrix[2][2]**2))
                    roll = math.atan2(rotation_matrix[1][0], rotation_matrix[0][0])
                    
                    # 转换为角度
                    pitch_deg = pitch * 180 / math.pi
                    yaw_deg = yaw * 180 / math.pi
                    roll_deg = roll * 180 / math.pi
                    
                    return {
                        'success': True,
                        'marker_id': int(ids[0][0]),
                        'position': {
                            'x': float(x_offset),
                            'y': float(y_offset),
                            'z': float(z_offset),
                            'distance': float(distance)
                        },
                        'rotation': {
                            'rvec': rvec.flatten().tolist(),
                            'pitch': float(pitch_deg),
                            'yaw': float(yaw_deg),
                            'roll': float(roll_deg)
                        },
                        'corners': corners[0].tolist(),
                        'total_markers': len(ids)
                    }
                else:
                    return {
                        'success': False,
                        'message': '位姿估计失败',
                        'total_markers': len(ids)
                    }
            else:
                return {
                    'success': False,
                    'message': '未检测到ArUco标记'
                }
                
        except Exception as e:
            print(f"ArUco检测错误: {e}")
            return {
                'success': False,
                'message': f'检测错误: {str(e)}'
            }
    
    def calculate_landing_command(self, detection_result: Dict) -> Dict:
        """根据检测结果计算降落控制指令
        
        Args:
            detection_result: ArUco检测结果
            
        Returns:
            控制指令字典
        """
        if not detection_result['success']:
            return {
                'action': 'hover',
                'message': '未检测到标记，保持悬停',
                'commands': []
            }
        
        pos = detection_result['position']
        x = pos['x']  # 左右偏移
        y = pos['y']  # 前后偏移
        height = pos['z']  # 高度
        
        # 计算水平偏差
        horizontal_error = math.sqrt(x**2 + y**2)
        
        commands = []
        
        # 判断是否到达目标高度
        if height <= self.target_height + self.landing_threshold:
            if horizontal_error <= self.alignment_threshold:
                return {
                    'action': 'land',
                    'message': f'到达目标位置，执行降落 (高度:{height:.2f}m, 水平偏差:{horizontal_error:.2f}m)',
                    'commands': [
                        {
                            'channel': 8,
                            'value': 2000,
                            'description': '执行降落'
                        }
                    ]
                }
        
        # 判断水平位置是否对准
        if horizontal_error > self.horizontal_threshold:
            # 需要调整水平位置
            
            # X轴调整（左右移动，通道3）
            if abs(x) > self.alignment_threshold:
                if x > 0:
                    # 标记在右侧，需要右移
                    x_value = 1500 + min(int(abs(x) * 500 / self.horizontal_threshold), 500)
                    commands.append({
                        'channel': 3,
                        'value': x_value,
                        'description': f'向右调整 {x:.3f}m'
                    })
                else:
                    # 标记在左侧，需要左移
                    x_value = 1500 - min(int(abs(x) * 500 / self.horizontal_threshold), 500)
                    commands.append({
                        'channel': 3,
                        'value': x_value,
                        'description': f'向左调整 {abs(x):.3f}m'
                    })
            
            # Y轴调整（前后移动，通道4）
            if abs(y) > self.alignment_threshold:
                if y > 0:
                    # 标记在前方，需要前进
                    y_value = 1500 + min(int(abs(y) * 500 / self.horizontal_threshold), 500)
                    commands.append({
                        'channel': 4,
                        'value': y_value,
                        'description': f'向前调整 {y:.3f}m'
                    })
                else:
                    # 标记在后方，需要后退
                    y_value = 1500 - min(int(abs(y) * 500 / self.horizontal_threshold), 500)
                    commands.append({
                        'channel': 4,
                        'value': y_value,
                        'description': f'向后调整 {abs(y):.3f}m'
                    })
            
            # 偏航角调整（通道1）
            yaw = detection_result['rotation']['yaw']
            if abs(yaw) > 5:  # 偏航角超过5度
                if yaw > 0:
                    yaw_value = 1500 + min(int(abs(yaw) * 200 / 45), 500)
                    commands.append({
                        'channel': 1,
                        'value': yaw_value,
                        'description': f'向右偏航调整 {yaw:.1f}度'
                    })
                else:
                    yaw_value = 1500 - min(int(abs(yaw) * 200 / 45), 500)
                    commands.append({
                        'channel': 1,
                        'value': yaw_value,
                        'description': f'向左偏航调整 {abs(yaw):.1f}度'
                    })
            
            return {
                'action': 'adjust',
                'message': f'调整水平位置 (水平偏差:{horizontal_error:.2f}m)',
                'commands': commands
            }
        
        # 水平位置已对准，需要降低高度
        if height > self.target_height + self.landing_threshold:
            return {
                'action': 'descend',
                'message': f'水平对准，降低高度 (当前:{height:.2f}m, 目标:{self.target_height:.2f}m)',
                'commands': [
                    {
                        'channel': 2,
                        'value': 1300,  # 下降
                        'description': f'下降调整'
                    }
                ]
            }
        
        return {
            'action': 'hover',
            'message': '保持悬停',
            'commands': []
        }
    
    def process_image(self, image_data: str) -> Dict:
        """处理图像并返回ArUco识别结果
        
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
                'message': '图像解码失败',
                'landing_command': {
                    'action': 'hover',
                    'message': '图像解码失败，保持悬停',
                    'commands': []
                }
            }
        
        # 检测ArUco标记
        detection = self.detect_aruco(image)
        
        # 计算降落控制指令
        landing_command = self.calculate_landing_command(detection)
        
        return {
            'success': detection.get('success', False),
            'detection': detection,
            'landing_command': landing_command,
            'target_height': self.target_height,
            'horizontal_threshold': self.horizontal_threshold
        }
    
    def get_debug_image(self, image_data: str, result: Dict) -> Optional[np.ndarray]:
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
        
        if not result.get('success') or not result['detection'].get('success'):
            cv2.putText(image, "No ArUco marker detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return image
        
        detection = result['detection']
        pos = detection['position']
        corners = np.array(detection['corners'][0], dtype=np.int32)
        
        # 绘制标记边界
        cv2.polylines(image, [corners], True, (0, 255, 0), 3)
        
        # 绘制标记ID
        center_x = int(np.mean(corners[:, 0]))
        center_y = int(np.mean(corners[:, 1]))
        cv2.putText(image, f"ID: {detection['marker_id']}", (center_x - 40, center_y - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # 绘制坐标轴
        axis_length = 50
        # X轴（红色）
        cv2.line(image, (center_x, center_y), (center_x + axis_length, center_y), (0, 0, 255), 2)
        # Y轴（绿色）
        cv2.line(image, (center_x, center_y), (center_x, center_y + axis_length), (0, 255, 0), 2)
        
        # 添加位置信息
        info_texts = [
            f"Marker ID: {detection['marker_id']}",
            f"Position: ({pos['x']:.3f}, {pos['y']:.3f}, {pos['z']:.3f})m",
            f"Distance: {pos['distance']:.3f}m",
            f"Rotation: P={detection['rotation']['pitch']:.1f}, Y={detection['rotation']['yaw']:.1f}, R={detection['rotation']['roll']:.1f}",
            f"Action: {result['landing_command']['action']}",
            f"Commands: {len(result['landing_command']['commands'])}"
        ]
        
        y_offset = 30
        for text in info_texts:
            cv2.putText(image, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 25
        
        return image
    
    def set_target_height(self, height: float):
        """设置目标降落高度"""
        self.target_height = height
    
    def set_marker_length(self, length: float):
        """设置ArUco标记的实际边长"""
        self.marker_length = length


# 全局实例
aruco_detection_controller = ArucoDetectionController()
