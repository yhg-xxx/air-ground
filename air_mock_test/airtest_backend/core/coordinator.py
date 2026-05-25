"""
协同调度器模块

负责无人机与无人车的协同任务调度与角色分配。
"""

import asyncio
import json
import time
from typing import Optional, Dict, List, Any, Callable
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from config.constants import MissionStages, ARCHES


class TaskPhase(Enum):
    """任务阶段枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RECONNAISSANCE = "reconnaissance"
    ARCH_CROSSING = "arch_crossing"
    PATH_PLANNING = "path_planning"
    COORDINATED_NAVIGATION = "coordinated_navigation"
    PRECISION_LANDING = "precision_landing"
    FINAL_SPRINT = "final_sprint"
    COMPLETED = "completed"
    EMERGENCY = "emergency"


@dataclass
class TaskContext:
    """任务上下文"""
    phase: TaskPhase
    start_time: float
    progress: float
    data: Dict[str, Any]


class MissionCoordinator:
    """任务协同调度器"""
    
    def __init__(self, controller_manager=None, planner=None, safety_monitor=None):
        self.controller_manager = controller_manager
        self.planner = planner
        self.safety_monitor = safety_monitor
        
        # 任务状态
        self.current_phase = TaskPhase.IDLE
        self.context = TaskContext(
            phase=TaskPhase.IDLE,
            start_time=0,
            progress=0.0,
            data={}
        )
        
        # 回调函数
        self.phase_callbacks: Dict[TaskPhase, List[Callable]] = {}
        self.status_callbacks: List[Callable] = []
        
        # 运行标志
        self._running = False
        self._task = None
    
    def register_phase_callback(self, phase: TaskPhase, callback: Callable):
        """注册阶段回调函数"""
        if phase not in self.phase_callbacks:
            self.phase_callbacks[phase] = []
        self.phase_callbacks[phase].append(callback)
        logger.debug(f"注册阶段回调: {phase.value}")
    
    def register_status_callback(self, callback: Callable):
        """注册状态回调函数"""
        self.status_callbacks.append(callback)
    
    async def _notify_phase_change(self):
        """通知阶段变化"""
        callbacks = self.phase_callbacks.get(self.current_phase, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.current_phase, self.context)
                else:
                    callback(self.current_phase, self.context)
            except Exception as e:
                logger.error(f"阶段回调执行失败: {e}")
        
        # 通知状态监听器
        for callback in self.status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.get_status())
                else:
                    callback(self.get_status())
            except Exception as e:
                logger.error(f"状态回调执行失败: {e}")
    
    async def transition_to(self, phase: TaskPhase, data: Optional[Dict] = None):
        """转换到指定阶段"""
        old_phase = self.current_phase
        self.current_phase = phase
        
        if data:
            self.context.data.update(data)
        
        logger.info(f"[协同调度] 阶段转换: {old_phase.value} -> {phase.value}")
        await self._notify_phase_change()
    
    async def start_mission(self):
        """启动任务"""
        logger.info("=" * 50)
        logger.info("=" * 50)
        logger.info("========== 协同任务开始 ==========")
        logger.info("=" * 50)
        logger.info("=" * 50)
        
        self._running = True
        self.context.start_time = time.time()
        
        try:
            # 阶段1: 初始化
            await self._phase_initialization()
            
            # 阶段2: 侦察建图
            await self._phase_reconnaissance()
            
            # 阶段3: 拱门穿越
            await self._phase_arch_crossing()
            
            # 阶段4: 路径规划
            await self._phase_path_planning()
            
            # 阶段5: 协同导航
            await self._phase_coordinated_navigation()
            
            # 阶段6: 精准降落
            await self._phase_precision_landing()
            
            # 阶段7: 联合冲线
            await self._phase_final_sprint()
            
            # 任务完成
            await self.transition_to(TaskPhase.COMPLETED)
            logger.info("=" * 50)
            logger.info("========== 协同任务完成 ==========")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            await self.transition_to(TaskPhase.EMERGENCY, {'error': str(e)})
            if self.safety_monitor:
                await self.safety_monitor.emergency_stop()
        finally:
            self._running = False
    
    async def _phase_initialization(self):
        """初始化阶段"""
        await self.transition_to(TaskPhase.INITIALIZING)
        logger.info("[阶段1/7] 系统初始化")
        
        # 检查设备连接
        if self.controller_manager:
            if not self.controller_manager.aircraft:
                raise Exception("无人机控制器未初始化")
            if not self.controller_manager.vehicle:
                raise Exception("无人车控制器未初始化")
        
        logger.info("设备检查完成")
        await asyncio.sleep(1)
    
    async def _phase_reconnaissance(self):
        """侦察建图阶段"""
        await self.transition_to(TaskPhase.RECONNAISSANCE)
        logger.info("[阶段2/7] 侦察建图")
        
        if self.controller_manager and self.controller_manager.aircraft:
            aircraft = self.controller_manager.aircraft
            
            # 起飞
            logger.info("无人机起飞")
            await aircraft.takeoff(10.0)
            await asyncio.sleep(2)
            
            # 云台复位
            logger.info("云台复位")
            await aircraft.gimbal_reset()
            await asyncio.sleep(1)
            
            # 俯视侦察
            logger.info("云台俯视侦察")
            await aircraft.gimbal_pitch_down(3)
            
            # 模拟扫描动作
            logger.info("执行螺旋式扫描航线")
            for i in range(4):
                logger.info(f"扫描第{i+1}/4圈")
                await aircraft.turn_right(2)
                await asyncio.sleep(0.5)
            
            # 云台复位
            await aircraft.gimbal_reset()
        
        logger.info("侦察建图完成")
        await asyncio.sleep(1)
    
    async def _phase_arch_crossing(self):
        """拱门穿越阶段"""
        await self.transition_to(TaskPhase.ARCH_CROSSING)
        logger.info("[阶段3/7] 拱门穿越")
        
        if self.controller_manager and self.controller_manager.aircraft:
            aircraft = self.controller_manager.aircraft
            
            total_arches = len(ARCHES)
            logger.info(f"共有 {total_arches} 个拱门需要穿越")
            
            for i, arch in enumerate(ARCHES):
                logger.info(f"========== 开始穿越第{i+1}/{total_arches}个拱门 ==========")
                
                # 根据拱门方向选择穿越策略
                if arch['dir'] == 'vertical':
                    # 竖拱门：从前方穿越
                    logger.info(f"竖拱门穿越: 位置({arch['x']}, {arch['z']})")
                    await aircraft.move_forward(4)
                else:
                    # 横拱门：从侧方穿越
                    logger.info(f"横拱门穿越: 位置({arch['x']}, {arch['z']})")
                    await aircraft.move_right(4)
                
                await asyncio.sleep(1)
                logger.info(f"========== 第{i+1}个拱门穿越完成 ==========")
        
        logger.info("拱门穿越完成")
        await asyncio.sleep(1)
    
    async def _phase_path_planning(self):
        """路径规划阶段"""
        await self.transition_to(TaskPhase.PATH_PLANNING)
        logger.info("[阶段4/7] 路径规划")
        
        # 触发路径规划
        if self.planner:
            logger.info("开始全局路径规划")
            # 这里调用路径规划算法
            await asyncio.sleep(1)  # 模拟规划时间
        
        logger.info("路径规划完成")
        await asyncio.sleep(1)
    
    async def _phase_coordinated_navigation(self):
        """协同导航阶段"""
        await self.transition_to(TaskPhase.COORDINATED_NAVIGATION)
        logger.info("[阶段5/7] 协同导航")
        
        # 定义迷宫路径关键点
        path_points = [
            {"x": 370, "z": 930},
            {"x": 280, "z": 960},
            {"x": 200, "z": 1020},
            {"x": 280, "z": 1080},
        ]
        
        for i, point in enumerate(path_points):
            logger.info(f"---------- 导航到第{i+1}个关键点 ----------")
            
            # 这里调用导航控制
            if self.controller_manager:
                if self.controller_manager.vehicle:
                    await self.controller_manager.vehicle.move_forward(3)
                if self.controller_manager.aircraft:
                    await self.controller_manager.aircraft.move_forward(3)
            
            await asyncio.sleep(2)
            logger.info(f"第{i+1}个关键点到达完成")
        
        logger.info("协同导航完成")
        await asyncio.sleep(1)
    
    async def _phase_precision_landing(self):
        """精准降落阶段"""
        await self.transition_to(TaskPhase.PRECISION_LANDING)
        logger.info("[阶段6/7] 精准降落")
        
        if self.controller_manager:
            # 无人车到达降落区域并停车
            if self.controller_manager.vehicle:
                logger.info("无人车到达降落区域")
                await self.controller_manager.vehicle.stop()
                await asyncio.sleep(1)
            
            # 无人机执行降落
            if self.controller_manager.aircraft:
                logger.info("无人机开始降落")
                await self.controller_manager.aircraft.descend(3)
                await self.controller_manager.aircraft.land()
        
        logger.info("精准降落完成")
        await asyncio.sleep(1)
    
    async def _phase_final_sprint(self):
        """联合冲线阶段"""
        await self.transition_to(TaskPhase.FINAL_SPRINT)
        logger.info("[阶段7/7] 联合冲线")
        
        if self.controller_manager and self.controller_manager.vehicle:
            logger.info("无人车携带无人机冲向终点")
            await self.controller_manager.vehicle.move_forward(10)
        
        logger.info("联合冲线完成")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        elapsed = time.time() - self.context.start_time if self.context.start_time > 0 else 0
        return {
            'phase': self.current_phase.value,
            'running': self._running,
            'elapsed_time': elapsed,
            'progress': self.context.progress,
            'data': self.context.data
        }
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running
    
    async def emergency_stop(self):
        """紧急停止"""
        logger.warning("[协同调度] 执行紧急停止")
        self._running = False
        await self.transition_to(TaskPhase.EMERGENCY)
        if self.controller_manager:
            await self.controller_manager.emergency_stop()
