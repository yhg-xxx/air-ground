"""
单元测试模块

测试各个独立模块的功能。
"""

import unittest
import asyncio
import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.constants import (
    AircraftChannels, VehicleChannels, ControlValues,
    PlanningConstants
)
from planning.global_planner import AStarPlanner, Node
from planning.local_planner import DynamicWindowApproach, RobotState
from planning.waypoint_generator import WaypointGenerator, Waypoint
from perception.mapper import GridMap, MapConfig, CellType
from control.pid_controller import PIDController, PIDConfig
from utils.simulator import SimpleSimulator, MazeSimulator


class TestConfig(unittest.TestCase):
    """测试配置常量"""
    
    def test_aircraft_channels(self):
        """测试无人机通道"""
        self.assertEqual(AircraftChannels.TAKEOFF, 7)
        self.assertEqual(AircraftChannels.LAND, 8)
    
    def test_control_values(self):
        """测试控制值"""
        self.assertEqual(ControlValues.MIN, 1000)
        self.assertEqual(ControlValues.MID, 1500)
        self.assertEqual(ControlValues.MAX, 2000)


class TestAStarPlanner(unittest.TestCase):
    """测试A*规划器"""
    
    def setUp(self):
        """测试前准备"""
        config = MapConfig(width=20, height=20)
        self.grid_map = GridMap(config)
        self.planner = AStarPlanner(self.grid_map)
    
    def test_heuristic(self):
        """测试启发式函数"""
        h = self.planner.heuristic(0, 0, 3, 4)
        self.assertAlmostEqual(h, 5.0, places=1)  # 3-4-5三角形
    
    def test_simple_path(self):
        """测试简单路径规划"""
        # 设置起点和终点为可通行
        self.grid_map.set_cell(0, 0, CellType.FREE)
        self.grid_map.set_cell(5, 5, CellType.FREE)
        
        # 清除路径上的障碍物
        for i in range(6):
            for j in range(6):
                self.grid_map.set_cell(i, j, CellType.FREE)
        
        path = self.planner.plan((0, 0), (5, 5))
        
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (5, 5))
    
    def test_no_path(self):
        """测试无路径情况"""
        # 设置障碍物阻挡
        for i in range(20):
            self.grid_map.set_cell(10, i, CellType.OCCUPIED)
        
        self.grid_map.set_cell(0, 0, CellType.FREE)
        self.grid_map.set_cell(19, 19, CellType.FREE)
        
        path = self.planner.plan((0, 0), (19, 19))
        self.assertIsNone(path)


class TestDWA(unittest.TestCase):
    """测试动态窗口法"""
    
    def setUp(self):
        """测试前准备"""
        self.dwa = DynamicWindowApproach()
    
    def test_calculate_dynamic_window(self):
        """测试动态窗口计算"""
        state = RobotState(v=1.0, omega=0.5)
        window = self.dwa.calculate_dynamic_window(state)
        
        # 检查窗口范围
        self.assertLessEqual(window[0], 1.0)  # v_min <= current_v
        self.assertGreaterEqual(window[1], 1.0)  # v_max >= current_v
    
    def test_plan(self):
        """测试规划"""
        state = RobotState(x=0, z=0, yaw=0, v=0, omega=0)
        goal = (5.0, 0.0)
        
        v, omega = self.dwa.plan(state, goal)
        
        # 检查输出范围
        self.assertGreaterEqual(v, -self.dwa.max_speed)
        self.assertLessEqual(v, self.dwa.max_speed)
        self.assertGreaterEqual(omega, -self.dwa.max_angular_speed)
        self.assertLessEqual(omega, self.dwa.max_angular_speed)


class TestPIDController(unittest.TestCase):
    """测试PID控制器"""
    
    def setUp(self):
        """测试前准备"""
        config = PIDConfig(kp=1.0, ki=0.1, kd=0.5)
        self.pid = PIDController(config, "TestPID")
    
    def test_compute(self):
        """测试控制计算"""
        self.pid.set_setpoint(10.0)
        
        # 测试输出
        output = self.pid.compute(5.0, dt=0.1)
        
        # 误差为5，比例项为5，应该有正输出
        self.assertGreater(output, 0)
    
    def test_reset(self):
        """测试重置"""
        self.pid.set_setpoint(10.0)
        self.pid.compute(5.0, dt=0.1)
        
        # 重置
        self.pid.reset()
        
        # 积分项应该为0
        self.assertEqual(self.pid.integral, 0.0)
        self.assertEqual(self.pid.last_error, 0.0)


class TestWaypointGenerator(unittest.TestCase):
    """测试航点生成器"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = WaypointGenerator(spacing=1.0)
    
    def test_generate_from_path(self):
        """测试从路径生成航点"""
        path = [(0, 0), (1, 0), (2, 0), (3, 0)]
        
        waypoints = self.generator.generate_from_path(path)
        
        self.assertGreater(len(waypoints), 0)
        self.assertEqual(waypoints[0].x, 0)
        self.assertEqual(waypoints[0].z, 0)
    
    def test_calculate_yaw(self):
        """测试朝向计算"""
        current = (0, 0)
        target = (1, 0)  # 正东方向
        
        yaw = self.generator._calculate_yaw(current, target)
        self.assertAlmostEqual(yaw, 0, places=5)
        
        target = (0, 1)  # 正北方向
        yaw = self.generator._calculate_yaw(current, target)
        self.assertAlmostEqual(yaw, np.pi/2, places=5)


class TestGridMap(unittest.TestCase):
    """测试栅格地图"""
    
    def setUp(self):
        """测试前准备"""
        config = MapConfig(width=10, height=10, cell_size=0.1)
        self.map = GridMap(config)
    
    def test_world_to_grid(self):
        """测试坐标转换"""
        x, z = 0.5, 0.5
        gx, gz = self.map.world_to_grid(x, z)
        
        self.assertEqual(gx, 5)
        self.assertEqual(gz, 5)
    
    def test_grid_to_world(self):
        """测试坐标反向转换"""
        gx, gz = 5, 5
        x, z = self.map.grid_to_world(gx, gz)
        
        self.assertAlmostEqual(x, 0.5, places=1)
        self.assertAlmostEqual(z, 0.5, places=1)
    
    def test_set_and_get_cell(self):
        """测试栅格设置和获取"""
        self.map.set_cell(5, 5, CellType.OCCUPIED)
        
        cell = self.map.get_cell(5, 5)
        self.assertEqual(cell, CellType.OCCUPIED)
    
    def test_is_free(self):
        """测试可通行检查"""
        self.map.set_cell(5, 5, CellType.FREE)
        self.assertTrue(self.map.is_free(5, 5))
        
        self.map.set_cell(6, 6, CellType.OCCUPIED)
        self.assertFalse(self.map.is_free(6, 6))


class TestSimulator(unittest.TestCase):
    """测试仿真器"""
    
    def setUp(self):
        """测试前准备"""
        self.simulator = SimpleSimulator(dt=0.1)
    
    def test_update_aircraft(self):
        """测试无人机更新"""
        initial_x = self.simulator.aircraft.x
        
        self.simulator.update_aircraft(1.0, 0.0, 0.0)
        
        # 应该向前移动
        self.assertGreater(self.simulator.aircraft.x, initial_x)
    
    def test_update_vehicle(self):
        """测试无人车更新"""
        initial_x = self.simulator.vehicle.x
        
        self.simulator.update_vehicle(1.0, 0.0)
        
        # 应该向前移动
        self.assertGreater(self.simulator.vehicle.x, initial_x)
    
    def test_reset(self):
        """测试重置"""
        self.simulator.update_aircraft(1.0, 0.0, 0.0)
        self.simulator.reset()
        
        self.assertEqual(self.simulator.aircraft.x, 0.0)
        self.assertEqual(self.simulator.aircraft.z, 0.0)


class TestMazeSimulator(unittest.TestCase):
    """测试迷宫仿真器"""
    
    def setUp(self):
        """测试前准备"""
        self.maze = MazeSimulator(width=20, height=20)
    
    def test_is_collision(self):
        """测试碰撞检测"""
        # 边界应该有障碍物
        self.assertTrue(self.maze.is_collision(0, 0, cell_size=1.0))
        
        # 内部应该是可通行的
        self.assertFalse(self.maze.is_collision(10, 10, cell_size=1.0))


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestConfig,
        TestAStarPlanner,
        TestDWA,
        TestPIDController,
        TestWaypointGenerator,
        TestGridMap,
        TestSimulator,
        TestMazeSimulator
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
