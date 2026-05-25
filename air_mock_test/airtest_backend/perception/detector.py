"""
目标检测器模块

负责拱门检测、ArUco码识别等目标检测功能。
集成拱门识别和ArUco检测算法。
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suanfa.arch_detection import arch_detection_controller
from suanfa.aruco_detection import aruco_detection_controller
from perception.image_processor import ImageProcessor


@dataclass
class DetectionResult:
    """检测结果"""
    success: bool
    target_type: str
    position: Optional[Tuple[float, float]] = None
    confidence: float = 0.0
    data: Dict = None
    message: str = ""


class TargetDetector:
    """目标检测器"""
    
    def __init__(self, image_processor: Optional[ImageProcessor] = None):
        self.image_processor = image_processor or ImageProcessor()
        
        # 检测结果缓存
        self.last_detection = None
        self.detection_count = 0
    
    def detect_arch(self, image_data: str) -> DetectionResult:
        """检测拱门"""
        try:
            result = arch_detection_controller.process_image(image_data)
            
            if result.get('success') and result.get('arch_detected'):
                arch = result['arch']
                position = result['position']
                target = result['target']
                
                return DetectionResult(
                    success=True,
                    target_type='arch',
                    position=(arch['center'][0], arch['center'][1]),
                    confidence=arch['confidence'],
                    data={
                        'arch': arch,
                        'position': position,
                        'target': target,
                        'can_cross': target['can_cross']
                    },
                    message="拱门检测成功"
                )
            else:
                return DetectionResult(
                    success=False,
                    target_type='arch',
                    confidence=0.0,
                    message=result.get('message', '未检测到拱门')
                )
        
        except Exception as e:
            logger.error(f"拱门检测失败: {e}")
            return DetectionResult(
                success=False,
                target_type='arch',
                confidence=0.0,
                message=f"检测失败: {str(e)}"
            )
    
    def detect_aruco(self, image_data: str) -> DetectionResult:
        """检测ArUco标记"""
        try:
            result = aruco_detection_controller.process_image(image_data)
            
            if result.get('success'):
                detection = result['detection']
                pos = detection['position']
                landing_cmd = result['landing_command']
                
                return DetectionResult(
                    success=True,
                    target_type='aruco',
                    position=(detection['corners'][0][0][0], 
                             detection['corners'][0][0][1]),
                    confidence=1.0,
                    data={
                        'marker_id': detection['marker_id'],
                        'position_3d': pos,
                        'rotation': detection['rotation'],
                        'landing_command': landing_cmd,
                        'action': landing_cmd['action']
                    },
                    message=f"检测到ArUco标记 ID:{detection['marker_id']}"
                )
            else:
                return DetectionResult(
                    success=False,
                    target_type='aruco',
                    confidence=0.0,
                    message=result.get('message', '未检测到ArUco标记')
                )
        
        except Exception as e:
            logger.error(f"ArUco检测失败: {e}")
            return DetectionResult(
                success=False,
                target_type='aruco',
                confidence=0.0,
                message=f"检测失败: {str(e)}"
            )
    
    def detect_maze_boundary(self, image: np.ndarray) -> List[Dict]:
        """检测迷宫边界"""
        try:
            # 预处理图像
            edges = self.image_processor.detect_edges(image)
            morphed = self.image_processor.morphological_operation(edges, 'close')
            
            # 查找轮廓
            contours, _ = self.image_processor.find_contours(morphed)
            
            # 筛选大轮廓（可能是迷宫墙体）
            boundary_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # 面积阈值
                    perimeter = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                    
                    boundary_contours.append({
                        'contour': contour,
                        'area': area,
                        'perimeter': perimeter,
                        'vertices': len(approx),
                        'approx': approx
                    })
            
            return boundary_contours
        
        except Exception as e:
            logger.error(f"迷宫边界检测失败: {e}")
            return []
    
    def detect_path(self, image: np.ndarray) -> List[Tuple[int, int]]:
        """检测可通行路径"""
        try:
            # 转换为灰度图
            gray = self.image_processor.to_grayscale(image)
            
            # 二值化处理
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            path_points = []
            for contour in contours:
                # 计算轮廓中心
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    path_points.append((cx, cy))
            
            return path_points
        
        except Exception as e:
            logger.error(f"路径检测失败: {e}")
            return []
    
    def batch_detect(self, image_data: str, 
                    detect_types: List[str] = None) -> Dict[str, DetectionResult]:
        """批量检测"""
        if detect_types is None:
            detect_types = ['arch', 'aruco']
        
        results = {}
        
        if 'arch' in detect_types:
            results['arch'] = self.detect_arch(image_data)
        
        if 'aruco' in detect_types:
            results['aruco'] = self.detect_aruco(image_data)
        
        return results
    
    def get_detection_summary(self) -> Dict:
        """获取检测统计"""
        return {
            'total_detections': self.detection_count,
            'last_detection': self.last_detection
        }


class DetectionPipeline:
    """检测流水线"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.detector = TargetDetector(self.image_processor)
        
        # 处理统计
        self.processed_count = 0
        self.detection_history = []
    
    def process(self, image_data: str, 
                detect_types: List[str] = None) -> Dict:
        """处理图像并执行检测"""
        self.processed_count += 1
        
        # 解码图像
        image = self.image_processor.decode_image(image_data)
        if image is None:
            return {
                'success': False,
                'message': '图像解码失败'
            }
        
        # 预处理
        processed = self.image_processor.preprocess(image)
        
        # 执行检测
        results = self.detector.batch_detect(image_data, detect_types)
        
        # 记录历史
        detection_record = {
            'timestamp': self.processed_count,
            'results': {k: {
                'success': v.success,
                'type': v.target_type,
                'confidence': v.confidence,
                'message': v.message
            } for k, v in results.items()}
        }
        self.detection_history.append(detection_record)
        
        # 限制历史记录数量
        if len(self.detection_history) > 100:
            self.detection_history.pop(0)
        
        return {
            'success': True,
            'processed_image': processed,
            'detections': results,
            'processed_count': self.processed_count
        }
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取检测历史"""
        return self.detection_history[-limit:]
