"""
集成测试模块

测试多个模块协同工作的功能。
"""

import unittest
import asyncio
import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from perception.mapper import GridMap, MapConfig, CellType, MazeMapper
from planning.global_planner import GlobalPlanner
from planning.local_planner import LocalPlanner
from planning.waypoint_generator import WaypointGenerator
from control.pid_controller import PIDControllerSet, PIDConfig
from utils.simulator import SimpleSimulator


class TestPerceptionPlanningIntegration(unittest.TestCase):
    """测试感知与规划集成"""
    
    def setUp(self):
        """测试前准备"""
        # 创建地图
        config = MapConfig(width=50, height=50, cell_size=0.1)
        self.mapper = MazeMapper()
        self.mapper.initialize(config)
        
        # 创建规划器
        self.global_planner = GlobalPlanner(self.mapper.grid_map)
    
    def test_map_to_path_planning(self):
        """测试从地图到路径规划"""
        # 设置起点和终点
        self.mapper.set_start((1.0, 1.0))
        self.mapper.set_goal((4.0, 4.0))
        
        # 清除路径上的障碍物
        for i in range(5):
            for j in range(5):
                self.mapper.grid_map.set_cell(i, j, CellType.FREE)
        
        # 规划路径
        waypoints = self.global_planner.plan_path((1.0, 1.0), (4.0, 4.0))
        
        self.assertIsNotNone(waypoints)
        self.assertGreater(len(waypoints), 0)
    
    def test_full_pipeline(self):
        """测试完整流程"""
        # 1. 构建地图
        for i in range(10):
            for j in range(10):
                self.mapper.grid_map.set_cell(i, j, CellType.FREE)
        
        # 2. 设置起点终点
        start = (0.5, 0.5)
        goal = (2.5, 2.5)
        
        # 3. 全局规划
        waypoints = self.global_planner.plan_path(start, goal)
        self.assertIsNotNone(waypoints)
        
        # 4. 生成航点
        generator = WaypointGenerator(spacing=0.3)
        path_grid = [self.mapper.grid_map.world_to_grid(w[0], w[1]) 
                     for w in waypoints]
        detailed_waypoints = generator.generate_from_path(waypoints)
        
        self.assertGreater(len(detailed_waypoints), 0)


class TestPlanningControlIntegration(unittest.TestCase):
    """测试规划与控制集成"""
    
    def setUp(self):
        """测试前准备"""
        # 创建地图和规划器
        config = MapConfig(width=30, height=30, cell_size=0.1)
        self.grid_map = GridMap(config)
        
        # 设置可通行区域
        for i in range(10):
            for j in range(10):
                self.grid_map.set_cell(i, j, CellType.FREE)
        
        self.planner = GlobalPlanner(self.grid_map)
        self.pid_set = PIDControllerSet()
    
    def test_path_to_control(self):
        """测试从路径到控制"""
        # 规划路径
        waypoints = self.planner.plan_path((0.5, 0.5), (2.0, 2.0))
        self.assertIsNotNone(waypoints)
        
        # 配置PID控制器
        self.pid_set.add_controller('x', PIDConfig(kp=1.0, ki=0.1, kd=0.5))
        self.pid_set.add_controller('z', PIDConfig(kp=1.0, ki=0.1, kd=0.5))
        
        # 模拟跟随路径
        current_pos = [0.5, 0.5]
        target = waypoints[0]
        
        # 计算控制输出
        x_pid = self.pid_set.get_controller('x')
        z_pid = self.pid_set.get_controller('z')
        
        x_pid.set_setpoint(target[0])
        z_pid.set_setpoint(target[1])
        
        x_output = x_pid.compute(current_pos[0], dt=0.1)
        z_output = z_pid.compute(current_pos[1], dt=0.1)
        
        # 检查输出非零
        self.assertNotEqual(x_output, 0)
        self.assertNotEqual(z_output, 0)


class TestLocalGlobalPlanningIntegration(unittest.TestCase):
    """测试局部与全局规划集成"""
    
    def setUp(self):
        """测试前准备"""
        # 创建地图
        config = MapConfig(width=40, height=40, cell_size=0.1)
        self.grid_map = GridMap(config)
        
        # 设置可通行区域
        for i in range(20):
            for j in range(20):
                self.grid_map.set_cell(i, j, CellType.FREE)
        
        self.global_planner = GlobalPlanner(self.grid_map)
        self.local_planner = LocalPlanner()
    
    def test_global_to_local_planning(self):
        """测试全局到局部规划"""
        # 全局规划
        start = (1.0, 1.0)
        goal = (5.0, 5.0)
        
        global_waypoints = self.global_planner.plan_path(start, goal)
        self.assertIsNotNone(global_waypoints)
        
        # 设置局部规划航点
        self.local_planner.set_waypoints(global_waypoints)
        
        # 模拟局部规划
        current_state = (1.0, 1.0, 0.0)  # x, z, yaw
        self.local_planner.update_state(*current_state)
        
        # 执行一步局部规划
        v, omega, reached = asyncio.run(self._async_step())
        
        # 检查输出
        self.assertIsInstance(v, float)
        self.assertIsInstance(omega, float)
        self.assertIsInstance(reached, bool)
    
    async def _async_step(self):
        """异步执行局部规划步"""
        return self.local_planner.step()


class TestControlSimulationIntegration(unittest.TestCase):
    """测试控制与仿真集成"""
    
    def setUp(self):
        """测试前准备"""
        self.simulator = SimpleSimulator(dt=0.1)
        self.pid_set = PIDControllerSet()
        
        # 配置PID
        self.pid_set.add_controller('linear', PIDConfig(kp=1.5, ki=0.1, kd=0.3))
        self.pid_set.add_controller('angular', PIDConfig(kp=2.0, ki=0.0, kd=0.5))
    
    def test_closed_loop_control(self):
        """测试闭环控制"""
        # 目标位置
        target = (5.0, 0.0)
        
        # 仿真步数
        for _ in range(50):
            # 获取当前状态
            state = self.simulator.get_vehicle_state()
            current_pos = (state['x'], state['z'])
            
            # 计算控制指令
            linear_pid = self.pid_set.get_controller('linear')
            angular_pid = self.pid_set.get_controller('angular')
            
            # 计算距离和角度
            dx = target[0] - current_pos[0]
            dz = target[1] - current_pos[1]
            distance = np.sqrt(dx**2 + dz**2)
            target_angle = np.arctan2(dz, dx)
            
            # PID控制
            linear_pid.set_setpoint(0)  # 目标是消除距离
            angular_pid.set_setpoint(target_angle)
            
            linear_cmd = linear_pid.compute(-distance, dt=0.1)
            angular_cmd = angular_pid.compute(state['yaw'], dt=0.1)
            
            # 归一化指令
            linear_cmd = max(-1, min(1, linear_cmd / 5.0))
            angular_cmd = max(-1, min(1, angular_cmd))
            
            # 更新仿真
            commands = {
                'vehicle': {
                    'linear': linear_cmd,
                    'angular': angular_cmd
                }
            }
            self.simulator.step(commands)
        
        # 检查是否接近目标
        final_state = self.simulator.get_vehicle_state()
        final_distance = np.sqrt((target[0] - final_state['x'])**2 + 
                                (target[1] - final_state['z'])**2)
        
        # 应该比之前更接近目标
        self.assertLess(final_state['x'], target[0] + 1.0)


class TestFullSystemIntegration(unittest.TestCase):
    """测试完整系统集成"""
    
    def setUp(self):
        """测试前准备"""
        # 创建地图
        config = MapConfig(width=50, height=50, cell_size=0.1)
        self.mapper = MazeMapper()
        self.mapper.initialize(config)
        
        # 设置迷宫环境
        for i in range(20):
            for j in range(20):
                self.mapper.grid_map.set_cell(i, j, CellType.FREE)
        
        # 添加拱门
        self.mapper.add_arch((5.0, 5.0))
        
        # 起点和终点
        self.mapper.set_start((1.0, 1.0))
        self.mapper.set_goal((10.0, 10.0))
        
        # 创建组件
        self.global_planner = GlobalPlanner(self.mapper.grid_map)
        self.waypoint_gen = WaypointGenerator()
        self.local_planner = LocalPlanner()
        self.simulator = SimpleSimulator()
    
    def test_mission_execution_simulation(self):
        """测试任务执行仿真"""
        # 1. 全局规划
        start = (1.0, 1.0)
        goal = (10.0, 10.0)
        
        global_path = self.global_planner.plan_path(start, goal)
        self.assertIsNotNone(global_path)
        self.assertGreater(len(global_path), 0)
        
        # 2. 生成航点
        waypoints = self.waypoint_gen.generate_from_path(global_path)
        self.assertGreater(len(waypoints), 0)
        
        # 3. 设置局部规划
        self.local_planner.set_waypoints(global_path)
        
        # 4. 模拟执行
        max_steps = 100
        for step in range(max_steps):
            # 获取当前状态
            vehicle_state = self.simulator.get_vehicle_state()
            
            # 更新局部规划状态
            self.local_planner.update_state(
                vehicle_state['x'],
                vehicle_state['z'],
                vehicle_state['yaw']
            )
            
            # 执行局部规划
            v, omega, reached = asyncio.run(self._async_step())
            
            # 更新仿真
            commands = {
                'vehicle': {
                    'linear': v / 3.0,  # 归一化
                    'angular': omega / 1.5
                }
            }
            self.simulator.step(commands)
            
            # 检查是否完成
            if reached:
                break
        
        # 检查是否到达终点
        final_state = self.simulator.get_vehicle_state()
        distance_to_goal = np.sqrt(
            (goal[0] - final_state['x'])**2 + 
            (goal[1] - final_state['z'])**2
        )
        
        # 应该比之前更接近目标
        self.assertLess(distance_to_goal, 15.0)  # 允许一定误差
    
    async def _async_step(self):
        """异步执行局部规划步"""
        return self.local_planner.step()


def run_integration_tests():
    """运行集成测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestPerceptionPlanningIntegration,
        TestPlanningControlIntegration,
        TestLocalGlobalPlanningIntegration,
        TestControlSimulationIntegration,
        TestFullSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
