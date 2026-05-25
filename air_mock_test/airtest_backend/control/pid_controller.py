"""
PID控制器模块

实现自适应PID控制算法，用于无人机和无人车的运动控制。
"""

import time
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from loguru import logger


@dataclass
class PIDConfig:
    """PID配置参数"""
    kp: float = 1.0  # 比例系数
    ki: float = 0.1  # 积分系数
    kd: float = 0.5  # 微分系数
    
    # 输出限制
    output_min: float = -1.0
    output_max: float = 1.0
    
    # 积分限制
    integral_min: float = -10.0
    integral_max: float = 10.0
    
    # 自适应参数
    adaptive: bool = True
    adaptation_rate: float = 0.01


class PIDController:
    """PID控制器"""
    
    def __init__(self, config: Optional[PIDConfig] = None, name: str = "PID"):
        self.config = config or PIDConfig()
        self.name = name
        
        # 状态变量
        self.setpoint = 0.0
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()
        
        # 历史记录
        self.error_history = []
        self.max_history = 10
        
        # 自适应参数
        if self.config.adaptive:
            self.kp_base = self.config.kp
            self.ki_base = self.config.ki
            self.kd_base = self.config.kd
    
    def reset(self):
        """重置控制器"""
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()
        self.error_history.clear()
        
        if self.config.adaptive:
            self.config.kp = self.kp_base
            self.config.ki = self.ki_base
            self.config.kd = self.kd_base
    
    def set_setpoint(self, setpoint: float):
        """设置目标值"""
        self.setpoint = setpoint
    
    def compute(self, measurement: float, dt: Optional[float] = None) -> float:
        """
        计算控制输出
        
        Args:
            measurement: 当前测量值
            dt: 时间间隔，None则自动计算
            
        Returns:
            控制输出
        """
        current_time = time.time()
        
        if dt is None:
            dt = current_time - self.last_time
            if dt <= 0:
                dt = 0.01  # 默认时间步长
        
        # 计算误差
        error = self.setpoint - measurement
        
        # 更新历史
        self.error_history.append(error)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # 自适应调整参数
        if self.config.adaptive:
            self._adapt_parameters(error)
        
        # 计算积分
        self.integral += error * dt
        self.integral = max(self.config.integral_min, 
                          min(self.config.integral_max, self.integral))
        
        # 计算微分
        derivative = (error - self.last_error) / dt if dt > 0 else 0.0
        
        # 计算输出
        output = (self.config.kp * error + 
                 self.config.ki * self.integral + 
                 self.config.kd * derivative)
        
        # 限制输出
        output = max(self.config.output_min, 
                    min(self.config.output_max, output))
        
        # 更新状态
        self.last_error = error
        self.last_time = current_time
        
        return output
    
    def _adapt_parameters(self, error: float):
        """自适应调整PID参数"""
        if len(self.error_history) < 3:
            return
        
        # 计算误差变化趋势
        error_change = abs(error - self.error_history[-2])
        error_trend = sum(abs(self.error_history[i] - self.error_history[i-1])
                        for i in range(1, len(self.error_history))) / len(self.error_history)
        
        # 根据误差调整参数
        if abs(error) > 1.0:
            # 大误差：增大比例系数
            self.config.kp = min(self.kp_base * 2.0, 
                               self.config.kp + self.config.adaptation_rate)
        else:
            # 小误差：恢复基础值
            self.config.kp = max(self.kp_base, 
                               self.config.kp - self.config.adaptation_rate)
        
        if error_trend > 0.5:
            # 误差波动大：增大微分系数
            self.config.kd = min(self.kd_base * 2.0, 
                               self.config.kd + self.config.adaptation_rate)
        else:
            # 误差平稳：恢复基础值
            self.config.kd = max(self.kd_base, 
                               self.config.kd - self.config.adaptation_rate)
    
    def get_status(self) -> Dict:
        """获取控制器状态"""
        return {
            'name': self.name,
            'setpoint': self.setpoint,
            'last_error': self.last_error,
            'integral': self.integral,
            'kp': self.config.kp,
            'ki': self.config.ki,
            'kd': self.config.kd,
            'error_history': self.error_history.copy()
        }


class AdaptivePIDController(PIDController):
    """自适应PID控制器（带预测功能）"""
    
    def __init__(self, config: Optional[PIDConfig] = None, name: str = "AdaptivePID"):
        super().__init__(config, name)
        
        # 预测模型参数
        self.prediction_window = 0.5  # 预测窗口（秒）
        self.system_delay = 0.1  # 系统延迟（秒）
        
        # 速度估计
        self.velocity_estimate = 0.0
        self.acceleration_estimate = 0.0
    
    def compute_with_prediction(self, measurement: float, 
                               dt: Optional[float] = None) -> float:
        """带预测的控制计算"""
        current_time = time.time()
        
        if dt is None:
            dt = current_time - self.last_time
            if dt <= 0:
                dt = 0.01
        
        # 估计速度和加速度
        error = self.setpoint - measurement
        if len(self.error_history) >= 2:
            self.velocity_estimate = (error - self.error_history[-1]) / dt
            if len(self.error_history) >= 3:
                prev_velocity = (self.error_history[-1] - self.error_history[-2]) / dt
                self.acceleration_estimate = (self.velocity_estimate - prev_velocity) / dt
        
        # 预测未来误差
        predicted_error = error + self.velocity_estimate * self.system_delay + \
                        0.5 * self.acceleration_estimate * self.system_delay ** 2
        
        # 使用预测误差计算控制量
        temp_setpoint = self.setpoint
        self.setpoint = measurement + predicted_error
        
        output = self.compute(measurement, dt)
        
        # 恢复原始目标值
        self.setpoint = temp_setpoint
        
        return output


class PIDControllerSet:
    """PID控制器集合"""
    
    def __init__(self):
        self.controllers: Dict[str, PIDController] = {}
    
    def add_controller(self, name: str, config: Optional[PIDConfig] = None):
        """添加控制器"""
        self.controllers[name] = PIDController(config, name)
        logger.info(f"添加PID控制器: {name}")
    
    def get_controller(self, name: str) -> Optional[PIDController]:
        """获取控制器"""
        return self.controllers.get(name)
    
    def compute_all(self, measurements: Dict[str, float], 
                 dt: Optional[float] = None) -> Dict[str, float]:
        """计算所有控制器的输出"""
        outputs = {}
        for name, controller in self.controllers.items():
            if name in measurements:
                outputs[name] = controller.compute(measurements[name], dt)
        return outputs
    
    def reset_all(self):
        """重置所有控制器"""
        for controller in self.controllers.values():
            controller.reset()
    
    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有控制器状态"""
        return {name: controller.get_status() 
               for name, controller in self.controllers.items()}
