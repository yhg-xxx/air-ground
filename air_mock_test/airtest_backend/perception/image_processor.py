"""
图像处理器模块

负责图像预处理、去畸变、降噪和增强等操作。
"""

import cv2
import numpy as np
import base64
from typing import Optional, Tuple, Dict, Any
from loguru import logger

from config.constants import VisionConstants


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 图像处理参数
        self.resolution = self.config.get('resolution', VisionConstants.CAMERA_RESOLUTION)
        self.blur_kernel = self.config.get('blur_kernel', VisionConstants.GAUSSIAN_KERNEL)
        self.canny_threshold1 = self.config.get('canny_threshold1', VisionConstants.CANNY_THRESHOLD1)
        self.canny_threshold2 = self.config.get('canny_threshold2', VisionConstants.CANNY_THRESHOLD2)
        self.morph_kernel = self.config.get('morph_kernel', VisionConstants.MORPH_KERNEL)
        
        # 相机内参（用于去畸变）
        self.camera_matrix = None
        self.dist_coeffs = None
        self._init_camera_params()
    
    def _init_camera_params(self):
        """初始化相机参数"""
        width, height = self.resolution
        
        # 简化相机内参矩阵
        self.camera_matrix = np.array([
            [width, 0, width / 2],
            [0, width, height / 2],
            [0, 0, 1]
        ], dtype=np.float32)
        
        # 假设无畸变
        self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)
    
    def decode_image(self, image_data: str) -> Optional[np.ndarray]:
        """解码base64图像数据"""
        try:
            # 移除data URL前缀
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Base64解码
            image_bytes = base64.b64decode(image_data)
            
            # 转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("图像解码失败")
            
            # 调整分辨率
            if image.shape[:2] != (self.resolution[1], self.resolution[0]):
                image = cv2.resize(image, self.resolution)
            
            return image
        
        except Exception as e:
            logger.error(f"图像解码错误: {e}")
            return None
    
    def undistort(self, image: np.ndarray) -> np.ndarray:
        """去畸变"""
        if self.camera_matrix is not None and self.dist_coeffs is not None:
            return cv2.undistort(image, self.camera_matrix, self.dist_coeffs)
        return image
    
    def denoise(self, image: np.ndarray, method: str = 'gaussian') -> np.ndarray:
        """降噪处理"""
        if method == 'gaussian':
            return cv2.GaussianBlur(image, (self.blur_kernel, self.blur_kernel), 0)
        elif method == 'median':
            return cv2.medianBlur(image, self.blur_kernel)
        elif method == 'bilateral':
            return cv2.bilateralFilter(image, self.blur_kernel, 75, 75)
        else:
            return cv2.GaussianBlur(image, (self.blur_kernel, self.blur_kernel), 0)
    
    def enhance(self, image: np.ndarray) -> np.ndarray:
        """图像增强"""
        # 使用CLAHE进行对比度增强
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def preprocess(self, image: np.ndarray, 
                   undistort: bool = True,
                   denoise: bool = True,
                   enhance: bool = True) -> Dict[str, np.ndarray]:
        """完整预处理流程"""
        results = {
            'original': image.copy()
        }
        
        # 去畸变
        if undistort:
            image = self.undistort(image)
            results['undistorted'] = image.copy()
        
        # 降噪
        if denoise:
            image = self.denoise(image)
            results['denoised'] = image.copy()
        
        # 增强
        if enhance:
            image = self.enhance(image)
            results['enhanced'] = image.copy()
        
        results['processed'] = image
        return results
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """转换为灰度图"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def to_hsv(self, image: np.ndarray) -> np.ndarray:
        """转换为HSV颜色空间"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        """边缘检测"""
        gray = self.to_grayscale(image)
        blurred = cv2.GaussianBlur(gray, (self.blur_kernel, self.blur_kernel), 0)
        edges = cv2.Canny(blurred, self.canny_threshold1, self.canny_threshold2)
        return edges
    
    def morphological_operation(self, image: np.ndarray, 
                                operation: str = 'close') -> np.ndarray:
        """形态学操作"""
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.morph_kernel, self.morph_kernel)
        )
        
        if operation == 'open':
            return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        elif operation == 'close':
            return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        elif operation == 'erode':
            return cv2.erode(image, kernel)
        elif operation == 'dilate':
            return cv2.dilate(image, kernel)
        else:
            return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    
    def find_contours(self, image: np.ndarray, 
                      mode: int = cv2.RETR_EXTERNAL,
                      method: int = cv2.CHAIN_APPROX_SIMPLE) -> Tuple:
        """查找轮廓"""
        if len(image.shape) == 3:
            image = self.to_grayscale(image)
        
        contours, hierarchy = cv2.findContours(image, mode, method)
        return contours, hierarchy
    
    def draw_contours(self, image: np.ndarray, contours: list, 
                     color: Tuple = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """绘制轮廓"""
        result = image.copy()
        cv2.drawContours(result, contours, -1, color, thickness)
        return result
    
    def encode_image(self, image: np.ndarray, format: str = 'jpg') -> str:
        """编码图像为base64"""
        if format == 'jpg':
            _, buffer = cv2.imencode('.jpg', image)
        elif format == 'png':
            _, buffer = cv2.imencode('.png', image)
        else:
            _, buffer = cv2.imencode('.jpg', image)
        
        return base64.b64encode(buffer).decode('utf-8')
