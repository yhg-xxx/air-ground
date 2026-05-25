"""
系统常量定义模块

定义系统中使用的所有常量，便于统一管理和维护。
"""

# ===================== 设备通道定义 =====================

# 无人机通道定义
class AircraftChannels:
    DIRECTION = 1      # 左转/右转 (1000左转, 1500停止, 2000右转)
    ALTITUDE = 2       # 下降/上升 (1000下降, 1500停止, 2000上升)
    MOVEMENT = 3       # 左移/右移 (1000左移, 1500停止, 2000右移)
    THROTTLE = 4       # 后退/前进 (1000后退, 1500停止, 2000前进)
    GIMBAL_PITCH = 5   # 云台俯仰 (1000俯, 1500停止, 2000仰)
    GIMBAL_ROLL = 6    # 云台横滚 (1000右, 1500停止, 2000左)
    TAKEOFF = 7        # 起飞 (2000执行)
    LAND = 8           # 降落 (2000执行)
    BACK = 9           # 返航 (2000执行)
    GIMBAL_RESET = 10  # 云台复位 (2000执行)


# 无人车通道定义
class VehicleChannels:
    THROTTLE = 1       # 前进/后退 (1000后退, 1500停止, 2000前进)
    DIRECTION = 2      # 左转/右转 (1000左转, 1500回中, 2000右转)


# ===================== 控制值常量 =====================
class ControlValues:
    MIN = 1000
    MID = 1500
    MAX = 2000
    MIN_INTERVAL = 0.1  # 最小控制间隔(秒)


# ===================== 运动控制常量 =====================
class MotionLimits:
    # 无人机限制
    AIRCRAFT_MAX_SPEED = 5.0       # 最大速度(m/s)
    AIRCRAFT_MAX_ALTITUDE = 15.0   # 最大高度(m)
    AIRCRAFT_MIN_ALTITUDE = 0.5    # 最小高度(m)
    
    # 无人车限制
    VEHICLE_MAX_SPEED = 3.0        # 最大速度(m/s)
    VEHICLE_MAX_ANGULAR_SPEED = 1.5  # 最大角速度(rad/s)
    VEHICLE_ACCELERATION = 1.0     # 加速度(m/s²)
    VEHICLE_DECELERATION = 2.0     # 减速度(m/s²)


# ===================== 视觉识别常量 =====================
class VisionConstants:
    # 相机参数
    CAMERA_RESOLUTION = (1280, 720)
    CAMERA_FPS = 30
    FOCAL_LENGTH = 1000
    
    # 图像处理参数
    GAUSSIAN_KERNEL = 5
    CANNY_THRESHOLD1 = 50
    CANNY_THRESHOLD2 = 150
    MORPH_KERNEL = 5
    
    # 拱门识别参数
    ARCH_ASPECT_RATIO_MIN = 0.3
    ARCH_ASPECT_RATIO_MAX = 2.0
    ARCH_AREA_MIN = 5000
    ARCH_AREA_MAX = 100000
    ARCH_CIRCULARITY_MIN = 0.3
    ARCH_CIRCULARITY_MAX = 0.9
    ARCH_CONFIDENCE_THRESHOLD = 0.5
    
    # ArUco标记参数
    ARUCO_MARKER_LENGTH = 0.2  # 米
    ARUCO_TARGET_HEIGHT = 0.3  # 米
    ARUCO_LANDING_THRESHOLD = 0.1  # 米
    ARUCO_HORIZONTAL_THRESHOLD = 0.15  # 米


# ===================== 路径规划常量 =====================
class PlanningConstants:
    # 栅格地图参数
    CELL_SIZE = 25 / 480  # 网格单元大小(米)
    GRID_WIDTH = 480
    GRID_HEIGHT = 1200
    
    # A*算法参数
    ASTAR_HEURISTIC_WEIGHT = 1.0
    ASTAR_DIAGONAL = True
    
    # 动态窗口法参数
    DWA_SAFE_DISTANCE = 0.3
    DWA_MAX_SPEED = 2.0
    DWA_MAX_ANGULAR_SPEED = 1.0
    DWA_VELOCITY_SAMPLES = 20
    DWA_ANGULAR_SAMPLES = 20
    DWA_PREDICTION_TIME = 2.0


# ===================== 安全监控常量 =====================
class SafetyConstants:
    # 电量阈值
    POWER_WARNING = 30
    POWER_CRITICAL = 15
    POWER_RETURN = 20
    
    # 边界限制
    BOUNDARY_MIN_X = -12.5
    BOUNDARY_MAX_X = 12.5
    BOUNDARY_MIN_Z = 0.0
    BOUNDARY_MAX_Z = 62.5
    
    # 碰撞检测
    SAFE_DISTANCE = 0.5
    EMERGENCY_DISTANCE = 0.2
    
    # 超时设置
    MISSION_TIMEOUT = 600  # 秒
    STAGE_TIMEOUT = 120  # 秒


# ===================== 通信常量 =====================
class CommunicationConstants:
    # 服务器配置
    HOST = "localhost"
    HTTP_PORT = 30080
    WS_PORT = 30081
    
    # 心跳配置
    HEARTBEAT_INTERVAL = 1.0
    HEARTBEAT_TIMEOUT = 3.0
    RECONNECT_INTERVAL = 1.0
    MAX_RECONNECT_ATTEMPTS = 10
    
    # 认证配置
    AUTH_USERNAME = "fcs002"
    AUTH_PASSWORD = "fcs002fcs002"


# ===================== 坐标转换常量 =====================
class CoordinateConstants:
    # 网格到场景坐标转换参数
    CELL_SIZE = 25 / 480
    GRID_CENTER_X = 240
    GRID_CENTER_Z = 600
    
    # 初始位置
    INITIAL_AIRCRAFT_POS = [8.546, 16.756]
    INITIAL_VEHICLE_POS = [8.546, 16.756]


# ===================== 任务阶段定义 =====================
class MissionStages:
    INITIALIZATION = "initialization"
    RECONNAISSANCE = "reconnaissance"
    ARCH_CROSSING = "arch_crossing"
    PATH_PLANNING = "path_planning"
    COORDINATED_NAVIGATION = "coordinated_navigation"
    PRECISION_LANDING = "precision_landing"
    FINAL_SPRINT = "final_sprint"


# ===================== 拱门配置 =====================
ARCHES = [
    {"x": 360, "z": 130, "dir": "vertical"},
    {"x": 370, "z": 930, "dir": "vertical"},
    {"x": 120, "z": 980, "dir": "vertical"},
    {"x": 280, "z": 960, "dir": "horizontal"},
    {"x": 20, "z": 1020, "dir": "vertical"},
    {"x": 200, "z": 1020, "dir": "vertical"},
    {"x": 380, "z": 1050, "dir": "horizontal"},
    {"x": 80, "z": 1080, "dir": "vertical"},
    {"x": 280, "z": 1080, "dir": "vertical"}
]


# ===================== 消息类型定义 =====================
class MessageTypes:
    # 控制消息
    CONTROL = "control"
    HEARTBEAT = "ping"
    AUTH_SUCCESS = "auth_success"
    
    # 设备遥测
    AIRCRAFT_TELEMETRY_POWER = "aircraft_telemetry_power"
    AIRCRAFT_TELEMETRY_GNSS = "aircraft_telemetry_gnss"
    AIRCRAFT_TELEMETRY_GIMBAL = "aircraft_telemetry_gimbal"
    VEHICLE_TELEMETRY_POWER = "vehicle_telemetry_power"
    VEHICLE_TELEMETRY_GNSS = "vehicle_telemetry_gnss"
    
    # 异常告警
    AIRCRAFT_SAFETY_FENCE_OVER = "aircraft_safety_fence_over"
    VEHICLE_SAFETY_FENCE_OVER = "vehicle_safety_fence_over"
    
    # 图像相关
    CAPTURE_IMAGE_REQUEST = "capture_image_request"
    CAPTURE_IMAGE_RESPONSE = "capture_image_response"
