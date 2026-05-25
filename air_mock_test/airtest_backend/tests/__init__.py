"""测试模块

包含单元测试和集成测试。
"""

from .test_unit import (
    TestConfig,
    TestAStarPlanner,
    TestDWA,
    TestPIDController,
    TestWaypointGenerator,
    TestGridMap,
    TestSimulator,
    TestMazeSimulator
)

from .test_integration import (
    TestPerceptionPlanningIntegration,
    TestPlanningControlIntegration,
    TestLocalGlobalPlanningIntegration,
    TestControlSimulationIntegration,
    TestFullSystemIntegration
)

__all__ = [
    # 单元测试
    'TestConfig',
    'TestAStarPlanner',
    'TestDWA',
    'TestPIDController',
    'TestWaypointGenerator',
    'TestGridMap',
    'TestSimulator',
    'TestMazeSimulator',
    # 集成测试
    'TestPerceptionPlanningIntegration',
    'TestPlanningControlIntegration',
    'TestLocalGlobalPlanningIntegration',
    'TestControlSimulationIntegration',
    'TestFullSystemIntegration'
]
