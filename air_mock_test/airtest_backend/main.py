"""
主程序入口

无人机与无人车协同控制系统的主入口。
"""

import asyncio
import argparse
import signal
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

# 导入各模块
from config.constants import CommunicationConstants, MissionStages
from utils.logger import setup_logging
from utils.visualizer import VisualizationManager
from utils.simulator import SimpleSimulator

from core.controller import ControllerManager
from core.coordinator import MissionCoordinator, TaskPhase
from core.safety_monitor import SafetyMonitor

from communication.websocket_client import WebSocketClient
from communication.api_client import APIService
from communication.message_handler import MessageHandler, MessageBuilder

from perception.image_processor import ImageProcessor
from perception.detector import TargetDetector, DetectionPipeline
from perception.mapper import MazeMapper, MapConfig

from planning.global_planner import GlobalPlanner
from planning.local_planner import LocalPlanner
from planning.waypoint_generator import WaypointGenerator

from control.pid_controller import PIDControllerSet, PIDConfig
from control.motion_controller import AircraftMotionController, VehicleMotionController
from control.gimbal_controller import GimbalController


class UAVUGVSystem:
    """无人机与无人车协同控制系统"""
    
    def __init__(self):
        self.running = False
        
        # 通信组件
        self.ws_client: WebSocketClient = None
        self.api_service: APIService = None
        self.message_handler: MessageHandler = None
        
        # 核心组件
        self.controller_manager: ControllerManager = None
        self.coordinator: MissionCoordinator = None
        self.safety_monitor: SafetyMonitor = None
        
        # 感知组件
        self.image_processor: ImageProcessor = None
        self.detector: TargetDetector = None
        self.mapper: MazeMapper = None
        
        # 规划组件
        self.global_planner: GlobalPlanner = None
        self.local_planner: LocalPlanner = None
        self.waypoint_generator: WaypointGenerator = None
        
        # 控制组件
        self.pid_set: PIDControllerSet = None
        self.aircraft_controller: AircraftMotionController = None
        self.vehicle_controller: VehicleMotionController = None
        self.gimbal_controller: GimbalController = None
        
        # 工具组件
        self.visualizer: VisualizationManager = None
        self.simulator: SimpleSimulator = None
    
    def initialize(self, mode: str = 'real'):
        """初始化系统"""
        logger.info("=" * 60)
        logger.info("无人机与无人车协同控制系统初始化")
        logger.info("=" * 60)
        
        # 1. 初始化日志
        setup_logging(log_level="INFO")
        logger.info("日志系统初始化完成")
        
        # 2. 初始化通信组件
        self._init_communication()
        
        # 3. 初始化核心组件
        self._init_core_components()
        
        # 4. 初始化感知组件
        self._init_perception()
        
        # 5. 初始化规划组件
        self._init_planning()
        
        # 6. 初始化控制组件
        self._init_control()
        
        # 7. 初始化工具组件
        self._init_utils(mode)
        
        # 8. 连接组件
        self._connect_components()
        
        logger.info("=" * 60)
        logger.info("系统初始化完成")
        logger.info("=" * 60)
    
    def _init_communication(self):
        """初始化通信组件"""
        logger.info("[初始化] 通信组件")
        
        # WebSocket客户端
        self.ws_client = WebSocketClient()
        
        # API服务
        self.api_service = APIService()
        
        # 消息处理器
        self.message_handler = MessageHandler()
        
        # 注册消息处理器
        self._register_message_handlers()
    
    def _register_message_handlers(self):
        """注册消息处理器"""
        # 遥测数据处理
        def handle_aircraft_telemetry(msg):
            data = msg.get('data', {})
            if 'gps' in data:
                position = data['gps']
                if self.controller_manager and self.controller_manager.aircraft:
                    self.controller_manager.aircraft.update_status({
                        'position': position,
                        'speed': data.get('speed', 0),
                        'power': data.get('power', 100),
                        'voltage': data.get('voltage', 0)
                    })
                    
                    # 更新安全监控
                    if self.safety_monitor:
                        self.safety_monitor.update_device_status('aircraft', {
                            'position': position,
                            'power': data.get('power', 100),
                            'voltage': data.get('voltage', 0)
                        })
        
        def handle_vehicle_telemetry(msg):
            data = msg.get('data', {})
            if 'gps' in data:
                position = data['gps']
                if self.controller_manager and self.controller_manager.vehicle:
                    self.controller_manager.vehicle.update_status({
                        'position': position,
                        'speed': data.get('speed', 0),
                        'power': data.get('power', 100),
                        'voltage': data.get('voltage', 0)
                    })
                    
                    # 更新安全监控
                    if self.safety_monitor:
                        self.safety_monitor.update_device_status('vehicle', {
                            'position': position,
                            'power': data.get('power', 100),
                            'voltage': data.get('voltage', 0)
                        })
        
        # 注册处理器
        if self.ws_client:
            self.ws_client.register_message_callback(handle_aircraft_telemetry)
            self.ws_client.register_message_callback(handle_vehicle_telemetry)
    
    def _init_core_components(self):
        """初始化核心组件"""
        logger.info("[初始化] 核心组件")
        
        # 控制器管理器
        self.controller_manager = ControllerManager()
        
        # 安全监控器
        self.safety_monitor = SafetyMonitor(self.controller_manager)
        
        # 协同调度器
        self.coordinator = MissionCoordinator(
            controller_manager=self.controller_manager,
            safety_monitor=self.safety_monitor
        )
    
    def _init_perception(self):
        """初始化感知组件"""
        logger.info("[初始化] 感知组件")
        
        # 图像处理器
        self.image_processor = ImageProcessor()
        
        # 目标检测器
        self.detector = TargetDetector(self.image_processor)
        
        # 地图构建器
        self.mapper = MazeMapper()
        config = MapConfig(
            width=480,
            height=1200,
            cell_size=0.052
        )
        self.mapper.initialize(config)
    
    def _init_planning(self):
        """初始化规划组件"""
        logger.info("[初始化] 规划组件")
        
        # 全局规划器
        if self.mapper:
            self.global_planner = GlobalPlanner(self.mapper.grid_map)
        
        # 局部规划器
        self.local_planner = LocalPlanner()
        
        # 航点生成器
        self.waypoint_generator = WaypointGenerator(
            spacing=0.5,
            smoothing_factor=0.5
        )
    
    def _init_control(self):
        """初始化控制组件"""
        logger.info("[初始化] 控制组件")
        
        # PID控制器集合
        self.pid_set = PIDControllerSet()
        
        # 位置控制PID
        self.pid_set.add_controller('x', PIDConfig(kp=1.0, ki=0.1, kd=0.5))
        self.pid_set.add_controller('z', PIDConfig(kp=1.0, ki=0.1, kd=0.5))
        self.pid_set.add_controller('yaw', PIDConfig(kp=2.0, ki=0.2, kd=1.0))
        self.pid_set.add_controller('altitude', PIDConfig(kp=1.5, ki=0.1, kd=0.3))
        
        # 运动控制器
        self.aircraft_controller = AircraftMotionController()
        self.vehicle_controller = VehicleMotionController()
        
        # 云台控制器
        self.gimbal_controller = GimbalController()
    
    def _init_utils(self, mode: str):
        """初始化工具组件"""
        logger.info("[初始化] 工具组件")
        
        # 可视化
        self.visualizer = VisualizationManager()
        
        # 仿真器（仅在仿真模式使用）
        if mode == 'simulation':
            self.simulator = SimpleSimulator()
    
    def _connect_components(self):
        """连接各组件"""
        logger.info("[初始化] 连接组件")
        
        # 设置控制器管理器的WebSocket客户端
        if self.ws_client:
            self.controller_manager.create_controllers()
            self.controller_manager.set_websocket_client(self.ws_client)
        
        # 设置运动控制器的WebSocket发送函数
        async def send_command(target, channel, value):
            if self.ws_client:
                await self.ws_client.send_control(target, channel, value)
        
        if self.aircraft_controller:
            self.aircraft_controller.send_command = send_command
        if self.vehicle_controller:
            self.vehicle_controller.send_command = send_command
        if self.gimbal_controller:
            self.gimbal_controller.send_command = send_command
        
        # 设置安全监控回调
        if self.safety_monitor:
            self.safety_monitor.register_emergency_callback(
                lambda reason: logger.critical(f"紧急停止: {reason}")
            )
    
    async def run(self):
        """运行系统"""
        logger.info("=" * 60)
        logger.info("系统启动")
        logger.info("=" * 60)
        
        self.running = True
        
        try:
            # 1. 连接WebSocket
            if self.ws_client:
                logger.info("[启动] 连接WebSocket")
                connected = await self.ws_client.connect()
                if not connected:
                    logger.error("WebSocket连接失败")
                    return False
            
            # 2. 认证
            if self.api_service:
                logger.info("[启动] API认证")
                auth_success = await self.api_service.authenticate()
                if not auth_success:
                    logger.error("API认证失败")
                    return False
            
            # 3. 启动安全监控
            if self.safety_monitor:
                logger.info("[启动] 安全监控")
                await self.safety_monitor.start_monitoring()
            
            # 4. 启动任务
            if self.coordinator:
                logger.info("[启动] 任务调度")
                await self.coordinator.start_mission()
            
            logger.info("=" * 60)
            logger.info("任务执行完成")
            logger.info("=" * 60)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("用户中断")
            return False
        except Exception as e:
            logger.exception(f"系统运行异常: {e}")
            return False
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """关闭系统"""
        logger.info("=" * 60)
        logger.info("系统关闭")
        logger.info("=" * 60)
        
        self.running = False
        
        # 停止安全监控
        if self.safety_monitor:
            await self.safety_monitor.stop_monitoring()
        
        # 断开WebSocket
        if self.ws_client:
            await self.ws_client.disconnect()
        
        # 停止可视化
        if self.visualizer:
            self.visualizer.stop()
        
        logger.info("系统已安全关闭")
    
    def handle_signal(self, signum, frame):
        """处理系统信号"""
        logger.info(f"收到信号: {signum}")
        self.running = False


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='无人机与无人车协同控制系统'
    )
    
    parser.add_argument(
        '--mode',
        choices=['real', 'simulation'],
        default='real',
        help='运行模式: real(真实设备) 或 simulation(仿真)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='启用可视化'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行测试'
    )
    
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_args()
    
    # 运行测试
    if args.test:
        logger.info("运行测试模式")
        from tests.test_unit import run_tests
        from tests.test_integration import run_integration_tests
        
        unit_success = run_tests()
        integration_success = run_integration_tests()
        
        if unit_success and integration_success:
            logger.info("所有测试通过")
            return 0
        else:
            logger.error("部分测试失败")
            return 1
    
    # 创建系统
    system = UAVUGVSystem()
    
    # 初始化
    system.initialize(mode=args.mode)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, system.handle_signal)
    signal.signal(signal.SIGTERM, system.handle_signal)
    
    # 启动可视化
    if args.visualize and system.visualizer:
        system.visualizer.start()
    
    # 运行系统
    success = await system.run()
    
    return 0 if success else 1


if __name__ == '__main__':
    # 运行主程序
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
