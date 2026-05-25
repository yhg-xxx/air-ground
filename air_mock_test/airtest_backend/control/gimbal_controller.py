"""
云台控制器模块

负责无人机机载云台的俯仰和横滚控制。
"""

import asyncio
from typing import Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from config.constants import AircraftChannels, ControlValues


@dataclass
class GimbalState:
    """云台状态"""
    pitch: float = 0.0  # 俯仰角（度）
    roll: float = 0.0   # 横滚角（度）
    
    def __post_init__(self):
        # 限制范围
        self.pitch = max(-90, min(90, self.pitch))
        self.roll = max(-45, min(45, self.roll))


class GimbalController:
    """云台控制器"""
    
    def __init__(self, send_command_func=None):
        self.send_command = send_command_func
        
        # 当前状态
        self.state = GimbalState()
        
        # 目标状态
        self.target_pitch: Optional[float] = None
        self.target_roll: Optional[float] = None
        
        # 速度限制（度/秒）
        self.max_pitch_speed = 30.0
        self.max_roll_speed = 30.0
        
        # 控制频率
        self.control_frequency = 10.0
        self.dt = 1.0 / self.control_frequency
    
    def update_state(self, pitch: float, roll: float):
        """更新云台状态"""
        self.state = GimbalState(pitch, roll)
        logger.debug(f"[云台] 状态更新: pitch={pitch:.1f}°, roll={roll:.1f}°")
    
    def set_target(self, pitch: Optional[float] = None, roll: Optional[float] = None):
        """设置目标角度"""
        if pitch is not None:
            self.target_pitch = max(-90, min(90, pitch))
        if roll is not None:
            self.target_roll = max(-45, min(45, roll))
    
    async def control_step(self) -> Tuple[bool, dict]:
        """执行一步控制"""
        commands = {}
        reached = True
        
        # 俯仰控制
        if self.target_pitch is not None:
            pitch_error = self.target_pitch - self.state.pitch
            
            if abs(pitch_error) > 1.0:  # 容差1度
                reached = False
                
                # 计算控制输出
                pitch_speed = max(-self.max_pitch_speed,
                                 min(self.max_pitch_speed, pitch_error * 2.0))
                
                # 转换为控制值
                if pitch_speed > 0:
                    # 向上
                    pitch_value = int(ControlValues.MID + 
                                     (pitch_speed / self.max_pitch_speed) * 500)
                else:
                    # 向下
                    pitch_value = int(ControlValues.MID + 
                                     (pitch_speed / self.max_pitch_speed) * 500)
                
                pitch_value = max(ControlValues.MIN, min(ControlValues.MAX, pitch_value))
                commands[AircraftChannels.GIMBAL_PITCH] = pitch_value
        
        # 横滚控制
        if self.target_roll is not None:
            roll_error = self.target_roll - self.state.roll
            
            if abs(roll_error) > 1.0:  # 容差1度
                reached = False
                
                # 计算控制输出
                roll_speed = max(-self.max_roll_speed,
                               min(self.max_roll_speed, roll_error * 2.0))
                
                # 转换为控制值
                roll_value = int(ControlValues.MID + 
                                (roll_speed / self.max_roll_speed) * 500)
                roll_value = max(ControlValues.MIN, min(ControlValues.MAX, roll_value))
                commands[AircraftChannels.GIMBAL_ROLL] = roll_value
        
        # 发送控制指令
        if self.send_command and commands:
            for channel, value in commands.items():
                await self.send_command('aircraft', channel, value)
                await asyncio.sleep(0.01)
        
        return reached, commands
    
    async def move_to(self, pitch: Optional[float] = None, 
                     roll: Optional[float] = None,
                     timeout: float = 5.0) -> bool:
        """移动到目标角度"""
        logger.info(f"[云台] 移动到 pitch={pitch}, roll={roll}")
        
        self.set_target(pitch, roll)
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            reached, _ = await self.control_step()
            
            if reached:
                logger.info("[云台] 到达目标角度")
                return True
            
            await asyncio.sleep(self.dt)
        
        logger.warning("[云台] 移动超时")
        return False
    
    async def pitch_up(self, angle: float = 30.0, duration: Optional[float] = None):
        """向上俯仰"""
        if duration:
            logger.info(f"[云台] 向上俯仰 {duration}秒")
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < duration:
                if self.send_command:
                    await self.send_command('aircraft', AircraftChannels.GIMBAL_PITCH, 
                                        ControlValues.MAX)
                await asyncio.sleep(0.1)
        else:
            target = self.state.pitch + angle
            await self.move_to(pitch=target)
    
    async def pitch_down(self, angle: float = 30.0, duration: Optional[float] = None):
        """向下俯仰"""
        if duration:
            logger.info(f"[云台] 向下俯仰 {duration}秒")
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < duration:
                if self.send_command:
                    await self.send_command('aircraft', AircraftChannels.GIMBAL_PITCH, 
                                        ControlValues.MIN)
                await asyncio.sleep(0.1)
        else:
            target = self.state.pitch - angle
            await self.move_to(pitch=target)
    
    async def roll_left(self, angle: float = 15.0):
        """向左横滚"""
        target = self.state.roll - angle
        await self.move_to(roll=target)
    
    async def roll_right(self, angle: float = 15.0):
        """向右横滚"""
        target = self.state.roll + angle
        await self.move_to(roll=target)
    
    async def reset(self):
        """复位云台"""
        logger.info("[云台] 复位")
        if self.send_command:
            await self.send_command('aircraft', AircraftChannels.GIMBAL_RESET, 
                                   ControlValues.MAX)
        self.state = GimbalState(0.0, 0.0)
        self.target_pitch = 0.0
        self.target_roll = 0.0
        await asyncio.sleep(1)
    
    def get_status(self) -> dict:
        """获取云台状态"""
        return {
            'pitch': self.state.pitch,
            'roll': self.state.roll,
            'target_pitch': self.target_pitch,
            'target_roll': self.target_roll
        }
    
    def stop(self):
        """停止运动"""
        self.target_pitch = None
        self.target_roll = None
