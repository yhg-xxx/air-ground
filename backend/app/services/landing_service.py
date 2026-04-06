import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Tuple

import cv2
import numpy as np

from backend.app.config.settings import (
    AIRCRAFT_CHANNEL_ALTITUDE, AIRCRAFT_CHANNEL_MOVEMENT, AIRCRAFT_CHANNEL_THROTTLE,
    CONTROL_MIN, CONTROL_MAX, CONTROL_MID
)
from backend.app.services.capture_service import CaptureService
from backend.app.services.ws_service import WebSocketService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('landing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('LandingService')

# 监控数据
class LandingMonitor:
    """降落过程监控类"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.detection_count = 0
        self.alignment_count = 0
        self.control_commands = 0
        self.aruco_detections = 0
        self.aruco_lost = 0
        
    def start(self):
        """开始监控"""
        self.start_time = datetime.now()
        logger.info("开始降落监控")
    
    def end(self):
        """结束监控"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        logger.info(f"降落监控结束，总时长: {duration:.2f}秒")
        logger.info(f"检测次数: {self.detection_count}, 对齐次数: {self.alignment_count}")
        logger.info(f"控制指令数: {self.control_commands}, Aruco检测数: {self.aruco_detections}")
        logger.info(f"Aruco丢失次数: {self.aruco_lost}")
    
    def record_detection(self, success: bool):
        """记录Aruco码检测"""
        self.detection_count += 1
        if success:
            self.aruco_detections += 1
        else:
            self.aruco_lost += 1
    
    def record_alignment(self, success: bool):
        """记录对齐状态"""
        if success:
            self.alignment_count += 1
    
    def record_control(self):
        """记录控制指令"""
        self.control_commands += 1


class LandingStatus(Enum):
    """降落状态枚举"""
    IDLE = "idle"            # 空闲状态
    INITIALIZING = "initializing"  # 初始化中
    DETECTING = "detecting"      # 检测Aruco码
    ALIGNING = "aligning"        # 对齐位置
    DESCENDING = "descending"      # 下降中
    LANDED = "landed"          # 已降落
    FAILED = "failed"          # 降落失败
    CANCELLED = "cancelled"      # 已取消

class LandingService:
    """无人机降落服务类"""
    
    def __init__(self):
        self.ws_service = WebSocketService()
        self.status = LandingStatus.IDLE
        self.error_message = ""
        self.landing_task: Optional[asyncio.Task] = None
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
        # PID控制器参数
        self.pid_x = PIDController(kp=0.5, ki=0.1, kd=0.2)
        self.pid_y = PIDController(kp=0.5, ki=0.1, kd=0.2)
        self.pid_z = PIDController(kp=0.8, ki=0.2, kd=0.3)
        
        # 目标Aruco码ID
        self.target_aruco_id = 0
        
        # 图像中心点
        self.image_center = (320, 240)  # 假设图像分辨率为640x480
        
        # 降落参数
        self.landing_altitude = 0.5  # 降落高度（米）
        self.min_altitude = 0.1  # 最小安全高度
        self.detection_threshold = 3  # 连续检测到Aruco码的次数
        self.alignment_threshold = 10  # 对齐成功的次数
        
        # 监控实例
        self.monitor = LandingMonitor()
    
    async def start_landing(self, target_aruco_id: int = 0) -> Dict[str, Any]:
        """开始降落过程
        
        Args:
            target_aruco_id: 目标Aruco码ID
            
        Returns:
            Dict[str, Any]: 降落状态信息
        """
        if self.status != LandingStatus.IDLE:
            logger.warning(f"尝试开始降落，但当前状态为: {self.status.value}")
            return {
                "status": "error",
                "message": "降落过程已经在进行中"
            }
        
        logger.info(f"开始降落过程，目标Aruco码ID: {target_aruco_id}")
        self.target_aruco_id = target_aruco_id
        self.status = LandingStatus.INITIALIZING
        self.error_message = ""
        
        # 启动监控
        self.monitor = LandingMonitor()
        self.monitor.start()
        
        # 启动WebSocket连接
        try:
            logger.info("正在连接WebSocket服务...")
            await self.ws_service.connect()
            logger.info("WebSocket连接成功")
        except Exception as e:
            self.status = LandingStatus.FAILED
            self.error_message = f"WebSocket连接失败: {str(e)}"
            logger.error(f"WebSocket连接失败: {str(e)}")
            self.monitor.end()
            return {
                "status": "error",
                "message": self.error_message
            }
        
        # 启动降落任务
        logger.info("启动降落任务")
        self.landing_task = asyncio.create_task(self._landing_task())
        
        return {
            "status": "success",
            "message": "降落过程已开始"
        }
    
    async def cancel_landing(self) -> Dict[str, Any]:
        """取消降落过程
        
        Returns:
            Dict[str, Any]: 取消状态信息
        """
        if self.status == LandingStatus.IDLE:
            logger.warning("尝试取消降落，但当前状态为空闲")
            return {
                "status": "error",
                "message": "没有正在进行的降落过程"
            }
        
        logger.info(f"取消降落过程，当前状态: {self.status.value}")
        
        if self.landing_task:
            logger.info("取消降落任务")
            self.landing_task.cancel()
            try:
                await self.landing_task
            except asyncio.CancelledError:
                logger.info("降落任务已成功取消")
        
        self.status = LandingStatus.CANCELLED
        
        # 断开WebSocket连接
        logger.info("断开WebSocket连接")
        await self.ws_service.disconnect()
        
        # 结束监控
        self.monitor.end()
        
        return {
            "status": "success",
            "message": "降落过程已取消"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取降落状态
        
        Returns:
            Dict[str, Any]: 降落状态信息
        """
        return {
            "status": self.status.value,
            "error_message": self.error_message
        }
    
    async def _landing_task(self):
        """降落任务主逻辑"""
        try:
            # 初始化
            logger.info("开始降落任务初始化")
            self.status = LandingStatus.INITIALIZING
            await asyncio.sleep(1)
            logger.info("初始化完成")
            
            # 检测Aruco码
            logger.info("开始检测Aruco码")
            self.status = LandingStatus.DETECTING
            detection_count = 0
            aruco_position = None
            
            while detection_count < self.detection_threshold:
                logger.debug("正在捕获图像...")
                image_data = CaptureService.capture_image(save_to_file=False)
                if image_data:
                    logger.debug("图像捕获成功，正在检测Aruco码...")
                    position = self._detect_aruco(image_data)
                    if position:
                        logger.info(f"检测到Aruco码，位置: {position}")
                        aruco_position = position
                        detection_count += 1
                        self.monitor.record_detection(True)
                        logger.info(f"Aruco码检测计数: {detection_count}/{self.detection_threshold}")
                    else:
                        logger.warning("未检测到Aruco码")
                        detection_count = 0
                        self.monitor.record_detection(False)
                else:
                    logger.warning("图像捕获失败")
                    self.monitor.record_detection(False)
                await asyncio.sleep(0.5)
            
            logger.info("Aruco码检测完成")
            
            # 对齐位置
            logger.info("开始位置对齐")
            self.status = LandingStatus.ALIGNING
            alignment_count = 0
            
            while alignment_count < self.alignment_threshold:
                logger.debug("正在捕获图像进行对齐...")
                image_data = CaptureService.capture_image(save_to_file=False)
                if image_data:
                    position = self._detect_aruco(image_data)
                    if position:
                        # 计算控制量
                        control_x, control_y = self._calculate_alignment_control(position)
                        logger.debug(f"计算控制量 - x: {control_x}, y: {control_y}")
                        
                        # 发送控制指令
                        await self.ws_service.send_control("aircraft", AIRCRAFT_CHANNEL_MOVEMENT, control_x)
                        await self.ws_service.send_control("aircraft", AIRCRAFT_CHANNEL_THROTTLE, control_y)
                        self.monitor.record_control()
                        
                        # 检查是否对齐
                        if self._is_aligned(position):
                            alignment_count += 1
                            self.monitor.record_alignment(True)
                            logger.info(f"对齐成功计数: {alignment_count}/{self.alignment_threshold}")
                        else:
                            alignment_count = 0
                            self.monitor.record_alignment(False)
                            logger.debug("对齐失败，重置计数")
                    else:
                        logger.warning("对齐过程中未检测到Aruco码")
                        self.monitor.record_detection(False)
                await asyncio.sleep(0.2)
            
            logger.info("位置对齐完成")
            
            # 下降
            logger.info("开始下降过程")
            self.status = LandingStatus.DESCENDING
            
            while True:
                # 持续检测Aruco码
                image_data = CaptureService.capture_image(save_to_file=False)
                if image_data:
                    position = self._detect_aruco(image_data)
                    if position:
                        # 计算控制量
                        control_x, control_y = self._calculate_alignment_control(position)
                        control_z = self._calculate_descend_control()
                        logger.debug(f"下降控制量 - x: {control_x}, y: {control_y}, z: {control_z}")
                        
                        # 发送控制指令
                        await self.ws_service.send_control("aircraft", AIRCRAFT_CHANNEL_MOVEMENT, control_x)
                        await self.ws_service.send_control("aircraft", AIRCRAFT_CHANNEL_THROTTLE, control_y)
                        await self.ws_service.send_control("aircraft", AIRCRAFT_CHANNEL_ALTITUDE, control_z)
                        self.monitor.record_control()
                        
                        # 检查是否到达降落高度
                        if self._is_landed():
                            logger.info("降落成功")
                            break
                    else:
                        # 失去Aruco码，取消降落
                        logger.error("下降过程中失去Aruco码跟踪")
                        self.status = LandingStatus.FAILED
                        self.error_message = "失去Aruco码跟踪"
                        self.monitor.record_detection(False)
                        break
                await asyncio.sleep(0.1)
            
            if self.status == LandingStatus.DESCENDING:
                # 降落成功
                logger.info("降落过程完成，状态更新为已降落")
                self.status = LandingStatus.LANDED
                
        except Exception as e:
            logger.error(f"降落过程出错: {str(e)}", exc_info=True)
            self.status = LandingStatus.FAILED
            self.error_message = f"降落过程出错: {str(e)}"
        finally:
            # 结束监控
            self.monitor.end()
            # 断开WebSocket连接
            logger.info("断开WebSocket连接")
            await self.ws_service.disconnect()
    
    def _detect_aruco(self, image_data: bytes) -> Optional[Tuple[int, int]]:
        """检测Aruco码
        
        Args:
            image_data: 图像二进制数据
            
        Returns:
            Optional[Tuple[int, int]]: Aruco码中心坐标，如果未检测到返回None
        """
        try:
            # 转换图像数据
            logger.debug("转换图像数据...")
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.warning("图像解码失败")
                return None
            
            # 检测Aruco码
            logger.debug("检测Aruco码...")
            corners, ids, rejected = self.detector.detectMarkers(image)
            
            if ids is not None:
                logger.debug(f"检测到 {len(ids)} 个Aruco码")
                # 找到目标Aruco码
                for i, id in enumerate(ids):
                    logger.debug(f"检测到Aruco码ID: {id[0]}")
                    if id[0] == self.target_aruco_id:
                        # 计算中心坐标
                        corner = corners[i][0]
                        center_x = int((corner[0][0] + corner[1][0] + corner[2][0] + corner[3][0]) / 4)
                        center_y = int((corner[0][1] + corner[1][1] + corner[2][1] + corner[3][1]) / 4)
                        logger.info(f"找到目标Aruco码ID: {self.target_aruco_id}，中心坐标: ({center_x}, {center_y})")
                        return (center_x, center_y)
                logger.warning(f"未找到目标Aruco码ID: {self.target_aruco_id}")
            else:
                logger.debug("未检测到任何Aruco码")
            
            return None
        except Exception as e:
            logger.error(f"Aruco码检测出错: {str(e)}", exc_info=True)
            return None
    
    def _calculate_alignment_control(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """计算对齐控制量
        
        Args:
            position: Aruco码中心坐标
            
        Returns:
            Tuple[int, int]: 控制量 (x, y)
        """
        # 计算偏差
        error_x = position[0] - self.image_center[0]
        error_y = position[1] - self.image_center[1]
        
        # 使用PID控制器计算控制量
        control_x = CONTROL_MID + self.pid_x.update(error_x)
        control_y = CONTROL_MID + self.pid_y.update(error_y)
        
        # 限制控制量范围
        control_x = max(CONTROL_MIN, min(CONTROL_MAX, control_x))
        control_y = max(CONTROL_MIN, min(CONTROL_MAX, control_y))
        
        return (int(control_x), int(control_y))
    
    def _calculate_descend_control(self) -> int:
        """计算下降控制量
        
        Returns:
            int: 控制量
        """
        # 简单的下降控制，实际应用中可能需要基于高度传感器数据
        control_z = CONTROL_MID - 100  # 缓慢下降
        return max(CONTROL_MIN, min(CONTROL_MAX, control_z))
    
    def _is_aligned(self, position: Tuple[int, int]) -> bool:
        """检查是否对齐
        
        Args:
            position: Aruco码中心坐标
            
        Returns:
            bool: 是否对齐
        """
        error_x = abs(position[0] - self.image_center[0])
        error_y = abs(position[1] - self.image_center[1])
        
        # 允许10像素的误差
        return error_x < 10 and error_y < 10
    
    def _is_landed(self) -> bool:
        """检查是否已降落
        
        Returns:
            bool: 是否已降落
        """
        # 实际应用中需要基于高度传感器数据
        # 这里简化处理，假设下降一定时间后认为已降落
        return True

class PIDController:
    """PID控制器类"""
    
    def __init__(self, kp: float, ki: float, kd: float):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.last_error = 0
        self.integral = 0
    
    def update(self, error: float) -> float:
        """更新PID控制器
        
        Args:
            error: 误差值
            
        Returns:
            float: 控制量
        """
        self.integral += error
        derivative = error - self.last_error
        self.last_error = error
        
        return self.kp * error + self.ki * self.integral + self.kd * derivative
