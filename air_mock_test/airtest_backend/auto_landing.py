import cv2
import cv2.aruco as aruco
import numpy as np
import base64
import io
from PIL import Image

class AutoLandingController:
    def __init__(self):
        # ArUco标记参数
        self.marker_length = 0.1  # 标记实际边长，单位：米（10cm）
        self.coordinate_system = 1  # 1: 中心坐标系, 0: 左上角坐标系
        self.camera_resolution = (1280, 720)
        
        # 初始化相机内参
        width, height = self.camera_resolution
        self.camera_matrix = np.array([
            [width, 0, width / 2],
            [0, width, height / 2],
            [0, 0, 1]
        ], dtype=np.float32)
        self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)
        
        # 创建Aruco检测器
        dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(dictionary, parameters)
        
        # 自动降落控制参数
        self.target_height = 0.5  # 目标降落高度（米）
        self.landing_threshold = 0.1  # 降落判定阈值（米）
        self.horizontal_threshold = 0.2  # 水平对齐阈值（米）
        
    def get_object_points(self):
        """获取3D物体点"""
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
    
    def decode_image(self, image_data):
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
                
            return image
        except Exception as e:
            print(f"图像解码错误: {e}")
            return None
    
    def detect_aruco(self, image):
        """检测Aruco标记并计算位置"""
        try:
            # 调整图像分辨率
            image = cv2.resize(image, self.camera_resolution)
            
            # 检测标记
            corners, ids, rejected = self.detector.detectMarkers(image)
            
            if ids is not None and len(ids) > 0:
                # 获取物体点
                object_points = self.get_object_points()
                
                # 对第一个标记进行姿态估计
                success, rvec, tvec = cv2.solvePnP(
                    object_points,
                    corners[0],
                    self.camera_matrix,
                    self.dist_coeffs
                )
                
                if success:
                    x_offset = tvec[0][0]
                    y_offset = tvec[1][0]
                    height = tvec[2][0]
                    distance = np.linalg.norm(tvec)
                    
                    return {
                        'success': True,
                        'marker_id': int(ids[0][0]),
                        'x': float(x_offset),
                        'y': float(y_offset),
                        'height': float(height),
                        'distance': float(distance),
                        'corners': corners[0].tolist()
                    }
            
            return {
                'success': False,
                'message': '未检测到Aruco标记'
            }
        except Exception as e:
            print(f"Aruco检测错误: {e}")
            return {
                'success': False,
                'message': f'检测错误: {str(e)}'
            }
    
    def calculate_landing_command(self, detection_result):
        """根据检测结果计算降落控制命令"""
        if not detection_result['success']:
            return {
                'action': 'hover',
                'message': '未检测到标记，保持悬停'
            }
        
        x = detection_result['x']
        y = detection_result['y']
        height = detection_result['height']
        
        # 判断是否已经降落到目标高度
        if height <= self.target_height + self.landing_threshold:
            return {
                'action': 'land',
                'message': f'到达目标高度，执行降落',
                'target': 'aircraft',
                'channel': 8,
                'value': 2000
            }
        
        # 判断水平位置是否对齐
        if abs(x) <= self.horizontal_threshold and abs(y) <= self.horizontal_threshold:
            # 水平位置对齐，降低高度
            return {
                'action': 'descend',
                'message': f'水平对齐，降低高度',
                'target': 'aircraft',
                'channel': 2,
                'value': 1000  # 下降
            }
        
        # 需要调整水平位置
        commands = []
        
        # X轴调整（左右）
        if abs(x) > self.horizontal_threshold:
            if x > 0:
                commands.append({
                    'target': 'aircraft',
                    'channel': 3,
                    'value': 2000,  # 右移
                    'message': f'向右调整'
                })
            else:
                commands.append({
                    'target': 'aircraft',
                    'channel': 3,
                    'value': 1000,  # 左移
                    'message': f'向左调整'
                })
        
        # Y轴调整（前后）
        if abs(y) > self.horizontal_threshold:
            if y > 0:
                commands.append({
                    'target': 'aircraft',
                    'channel': 4,
                    'value': 1000,  # 后退
                    'message': f'向后调整'
                })
            else:
                commands.append({
                    'target': 'aircraft',
                    'channel': 4,
                    'value': 2000,  # 前进
                    'message': f'向前调整'
                })
        
        if commands:
            return {
                'action': 'adjust',
                'message': f'调整水平位置',
                'commands': commands
            }
        
        return {
            'action': 'hover',
            'message': '保持悬停'
        }
    
    def process_landing_image(self, image_data):
        """处理降落图像并返回控制命令"""
        # 解码图像
        image = self.decode_image(image_data)
        if image is None:
            return {
                'success': False,
                'message': '图像解码失败'
            }
        
        # 检测Aruco标记
        detection = self.detect_aruco(image)
        
        if not detection['success']:
            return {
                'success': False,
                'message': detection['message']
            }
        
        # 计算控制命令
        command = self.calculate_landing_command(detection)
        
        return {
            'success': True,
            'detection': detection,
            'command': command
        }


# 全局实例
auto_landing_controller = AutoLandingController()
