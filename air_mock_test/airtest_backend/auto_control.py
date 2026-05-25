import asyncio
import json
import requests
import websockets
from loguru import logger
from datetime import datetime
import os
from typing import Optional, Dict, Tuple
import time
import math

# ===================== 本地Mock服务器配置 =====================
HOST = "localhost"
HTTP_PORT = 30080
WS_PORT = 30081
USERNAME = "fcs002"
PASSWORD = "fcs002fcs002"

# ===================== 迷宫配置 =====================
CELL_SIZE = 25 / 480  # 网格单元大小
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

def grid_to_scene(grid_x: int, grid_z: int) -> Tuple[float, float]:
    """将网格坐标转换为场景坐标"""
    real_x = (grid_x - 240) * CELL_SIZE
    real_z = (grid_z - 600) * CELL_SIZE
    return real_x, real_z

# ===================== 通道定义 =====================
# 车辆通道
VEHICLE_CHANNEL_THROTTLE = 1    # 前进/后退 (1000后退, 1500停止, 2000前进)
VEHICLE_CHANNEL_DIRECTION = 2    # 左转/右转 (1000左转, 1500回中, 2000右转)

# 无人机通道
AIRCRAFT_CHANNEL_DIRECTION = 1    # 左转/右转 (1000左转, 1500停止, 2000右转)
AIRCRAFT_CHANNEL_ALTITUDE = 2    # 下降/上升 (1000下降, 1500停止, 2000上升)
AIRCRAFT_CHANNEL_MOVEMENT = 3    # 左移/右移 (1000左移, 1500停止, 2000右移)
AIRCRAFT_CHANNEL_THROTTLE = 4   # 后退/前进 (1000后退, 1500停止, 2000前进)
AIRCRAFT_CHANNEL_GIMBAL_PITCH = 5     # 云台俯仰 (1000俯, 1500停止, 2000仰)
AIRCRAFT_CHANNEL_GIMBAL_ROLL = 6     # 云台横滚 (1000右, 1500停止, 2000左)
AIRCRAFT_CHANNEL_TAKEOFF = 7    # 起飞 (2000执行)
AIRCRAFT_CHANNEL_LAND = 8        # 降落 (2000执行)
AIRCRAFT_CHANNEL_BACK = 9        # 返航 (2000执行)
AIRCRAFT_CHANNEL_GIMBAL_RESET = 10    # 云台复位 (2000执行)

# 控制值
MAX = 2000
MIN = 1000
MID = 1500
MIN_INTERVAL = 0.1  # 最小间隔100ms

logger.add(
    "auto_control.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="10MB"
)

class AutoControlSystem:
    def __init__(self):
        self.token: Optional[str] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.telemetry_data = {
            "aircraft": {"gps": [8.546, 16.756], "speed": 0, "power": 0, "voltage": 0},
            "vehicle": {"gps": [8.546, 16.756], "speed": 0, "power": 0, "voltage": 0}
        }
        self.recv_task = None
        self.capture_image_future = None  # 用于等待前端返回图片数据

    def get_token(self) -> str:
        """获取认证Token"""
        logger.info(">>> 开始获取认证Token")
        logger.info(f">>> 认证服务器: http://{HOST}:{HTTP_PORT}/api/auth/token")
        logger.info(f">>> 用户名: {USERNAME}")
        url = f"http://{HOST}:{HTTP_PORT}/api/auth/token"
        headers = {"Content-Type": "application/json"}
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        resp = requests.post(url, json=data, headers=headers)
        result = resp.json()
        if result.get("code") == "1":
            self.token = result["data"]["token"]
            logger.info(">>> Token获取成功")
            logger.info(f">>> Token: {self.token[:20]}...")
            return self.token
        else:
            logger.error(f">>> Token获取失败: {result.get('msg')}")
            raise Exception("获取Token失败：" + result.get("msg"))

    async def capture_image(self, save_path: str = "capture") -> str:
        """云台图像抓拍"""
        logger.info(">>> 开始抓拍云台图像")
        if not self.ws:
            raise Exception("WebSocket未连接")
        
        # 创建Future用于等待前端返回图片数据
        self.capture_image_future = asyncio.Future()
        
        # 通过WebSocket向前端发送抓拍请求
        msg = json.dumps({
            "type": "capture_image_request"
        })
        await self.ws.send(msg)
        logger.info(">>> 已向前端发送抓拍请求")
        
        # 等待前端返回图片数据（超时10秒）
        try:
            image_data = await asyncio.wait_for(self.capture_image_future, timeout=10.0)
            logger.info(">>> 收到前端返回的图片数据")
            
            # 解析base64图片数据
            import base64
            if image_data.startswith("data:image/jpeg;base64,"):
                image_data = image_data.split(",", 1)[1]
            image_bytes = base64.b64decode(image_data)
            
            # 保存图片
            os.makedirs(save_path, exist_ok=True)
            filename = f"{save_path}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            logger.info(f">>> 图片抓取成功，已保存至：{filename}")
            return filename
        except asyncio.TimeoutError:
            logger.error(">>> 抓拍超时，前端未响应")
            raise Exception("抓拍超时")
        finally:
            self.capture_image_future = None

    async def send_ctrl(self, target: str, channel: int, value: int):
        """发送控制指令"""
        if not self.ws:
            raise Exception("WebSocket未连接")
        
        msg = json.dumps({
            "type": "control",
            "target": target,
            "channel": channel,
            "value": value
        })
        await self.ws.send(msg)
        logger.info(f"[{target}] 通道{channel} 发送值 {value}")
        await asyncio.sleep(MIN_INTERVAL)

    async def connect_websocket(self):
        """连接WebSocket"""
        logger.info(">>> 开始连接WebSocket服务器")
        if not self.token:
            logger.info(">>> Token未获取，开始获取Token")
            self.get_token()
        
        ws_url = f"ws://{HOST}:{WS_PORT}?token={self.token}"
        logger.info(f">>> WebSocket连接URL: {ws_url}")
        
        self.ws = await websockets.connect(ws_url, ping_interval=None)
        self.is_connected = True
        logger.info(">>> WebSocket连接成功")
        
        # 启动接收任务
        logger.info(">>> 启动遥测数据接收任务")
        self.recv_task = asyncio.create_task(self._recv_loop())
        await asyncio.sleep(1)  # 等待连接稳定
        logger.info(">>> WebSocket连接稳定")

    async def _recv_loop(self):
        """接收遥测数据循环"""
        logger.info(">>> 遥测数据接收任务已启动")
        try:
            while self.is_connected:
                msg = await self.ws.recv()
                data = json.loads(msg)
                typ = data.get("type")
                
                if typ == "auth_success":
                    logger.info(">>> WebSocket登录成功")
                elif typ == "ping":
                    logger.debug(">>> 收到服务端心跳")
                elif typ == "capture_image_response":
                    # 收到前端返回的图片数据
                    logger.info(">>> 收到前端返回的图片数据")
                    if self.capture_image_future and not self.capture_image_future.done():
                        self.capture_image_future.set_result(data["data"])
                elif typ == "aircraft_telemetry_power":
                    self.telemetry_data["aircraft"]["power"] = data["data"]["power"]
                    self.telemetry_data["aircraft"]["voltage"] = data["data"]["voltage"]
                    logger.info(f">>> 无人机遥测 - 电量={data['data']['power']} 电压={data['data']['voltage']:.2f}V")
                elif typ == "aircraft_telemetry_gnss":
                    self.telemetry_data["aircraft"]["gps"] = data["data"]["gps"]
                    self.telemetry_data["aircraft"]["speed"] = data["data"]["speed"]
                    logger.info(f">>> 无人机遥测 - GPS=({data['data']['gps'][0]:.6f}, {data['data']['gps'][1]:.6f}) 速度={data['data']['speed']}")
                elif typ == "vehicle_telemetry_power":
                    self.telemetry_data["vehicle"]["power"] = data["data"]["power"]
                    self.telemetry_data["vehicle"]["voltage"] = data["data"]["voltage"]
                    logger.info(f">>> 车辆遥测 - 电量={data['data']['power']} 电压={data['data']['voltage']:.2f}V")
                elif typ == "vehicle_telemetry_gnss":
                    self.telemetry_data["vehicle"]["gps"] = data["data"]["gps"]
                    self.telemetry_data["vehicle"]["speed"] = data["data"]["speed"]
                    logger.info(f">>> 车辆遥测 - GPS=({data['data']['gps'][0]:.6f}, {data['data']['gps'][1]:.6f}) 速度={data['data']['speed']}")
                elif typ == "aircraft_safety_fence_over":
                    logger.warning(f">>> 警告：无人机超出围栏：{data}")
                elif typ == "vehicle_safety_fence_over":
                    logger.warning(f">>> 警告：车辆超出围栏：{data}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(">>> WebSocket连接已关闭")
        except Exception as e:
            logger.error(f">>> 接收消息异常：{str(e)}")

    # ===================== 无人机控制函数 =====================
    async def aircraft_takeoff(self):
        """无人机起飞"""
        logger.info(">>> 无人机起飞指令发送 (通道7, 值2000)")
        await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_TAKEOFF, MAX)
        logger.info(">>> 等待起飞稳定3秒")
        await asyncio.sleep(3)  # 起飞稳定3秒
        logger.info(">>> 起飞稳定完成")

    async def aircraft_land(self):
        """无人机降落"""
        logger.info(">>> 无人机降落指令发送 (通道8, 值2000)")
        await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_LAND, MAX)
        logger.info(">>> 降落指令发送完成")

    async def aircraft_forward(self, duration: float, value: int = 1600):
        """无人机前进"""
        logger.info(f">>> 无人机前进开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_THROTTLE, value)
            count += 1
        logger.info(f">>> 无人机前进完成，共发送 {count} 次控制指令")

    async def aircraft_backward(self, duration: float, value: int = 1400):
        """无人机后退"""
        logger.info(f">>> 无人机后退开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_THROTTLE, value)
            count += 1
        logger.info(f">>> 无人机后退完成，共发送 {count} 次控制指令")

    async def aircraft_left(self, duration: float, value: int = 1400):
        """无人机左移"""
        logger.info(f">>> 无人机左移开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_MOVEMENT, value)
            count += 1
        logger.info(f">>> 无人机左移完成，共发送 {count} 次控制指令")

    async def aircraft_right(self, duration: float, value: int = 1600):
        """无人机右移"""
        logger.info(f">>> 无人机右移开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_MOVEMENT, value)
            count += 1
        logger.info(f">>> 无人机右移完成，共发送 {count} 次控制指令")

    async def aircraft_turn_left(self, duration: float, value: int = MIN):
        """无人机左转"""
        logger.info(f">>> 无人机左转开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_DIRECTION, value)
            count += 1
        logger.info(f">>> 无人机左转完成，共发送 {count} 次控制指令")

    async def aircraft_turn_right(self, duration: float, value: int = MAX):
        """无人机右转"""
        logger.info(f">>> 无人机右转开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_DIRECTION, value)
            count += 1
        logger.info(f">>> 无人机右转完成，共发送 {count} 次控制指令")

    async def aircraft_up(self, duration: float, value: int = 1600):
        """无人机上升"""
        logger.info(f">>> 无人机上升开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_ALTITUDE, value)
            count += 1
        logger.info(f">>> 无人机上升完成，共发送 {count} 次控制指令")

    async def aircraft_down(self, duration: float, value: int = 1400):
        """无人机下降"""
        logger.info(f">>> 无人机下降开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_ALTITUDE, value)
            count += 1
        logger.info(f">>> 无人机下降完成，共发送 {count} 次控制指令")

    async def aircraft_gimbal_down(self, duration: float, value: int = 1400):
        """云台俯"""
        logger.info(f">>> 云台俯视开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_GIMBAL_PITCH, value)
            count += 1
        logger.info(f">>> 云台俯视完成，共发送 {count} 次控制指令")

    async def aircraft_gimbal_up(self, duration: float, value: int = 1600):
        """云台仰"""
        logger.info(f">>> 云台仰视开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_GIMBAL_PITCH, value)
            count += 1
        logger.info(f">>> 云台仰视完成，共发送 {count} 次控制指令")

    async def aircraft_gimbal_reset(self):
        """云台复位"""
        logger.info(">>> 云台复位指令发送 (通道10, 值2000)")
        await self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_GIMBAL_RESET, MAX)
        logger.info(">>> 云台复位完成")

    # ===================== 车辆控制函数 =====================
    async def vehicle_forward(self, duration: float, value: int = 1700):
        """车辆前进"""
        logger.info(f">>> 车辆前进开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("vehicle", VEHICLE_CHANNEL_THROTTLE, value)
            count += 1
        logger.info(f">>> 车辆前进完成，共发送 {count} 次控制指令")

    async def vehicle_backward(self, duration: float, value: int = 1300):
        """车辆后退"""
        logger.info(f">>> 车辆后退开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("vehicle", VEHICLE_CHANNEL_THROTTLE, value)
            count += 1
        logger.info(f">>> 车辆后退完成，共发送 {count} 次控制指令")

    async def vehicle_turn_left(self, duration: float, value: int = MIN):
        """车辆左转"""
        logger.info(f">>> 车辆左转开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("vehicle", VEHICLE_CHANNEL_DIRECTION, value)
            count += 1
        logger.info(f">>> 车辆左转完成，共发送 {count} 次控制指令")

    async def vehicle_turn_right(self, duration: float, value: int = MAX):
        """车辆右转"""
        logger.info(f">>> 车辆右转开始，持续时间: {duration:.2f}秒，控制值: {value}")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            await self.send_ctrl("vehicle", VEHICLE_CHANNEL_DIRECTION, value)
            count += 1
        logger.info(f">>> 车辆右转完成，共发送 {count} 次控制指令")

    # ===================== 协同控制函数 =====================
    async def sync_forward(self, duration: float):
        """无人机和车辆同时前进"""
        logger.info(f">>> 协同前进开始，持续时间: {duration:.2f}秒")
        logger.info(">>> 无人机前进控制值: 1600, 车辆前进控制值: 1700")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            t1 = asyncio.create_task(self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_THROTTLE, 1600))
            t2 = asyncio.create_task(self.send_ctrl("vehicle", VEHICLE_CHANNEL_THROTTLE, 1700))
            await asyncio.gather(t1, t2)
            count += 1
        logger.info(f">>> 协同前进完成，共发送 {count} 次协同控制指令")

    async def sync_backward(self, duration: float):
        """无人机和车辆同时后退"""
        logger.info(f">>> 协同后退开始，持续时间: {duration:.2f}秒")
        logger.info(">>> 无人机后退控制值: 1400, 车辆后退控制值: 1300")
        start = asyncio.get_event_loop().time()
        count = 0
        while asyncio.get_event_loop().time() - start < duration:
            t1 = asyncio.create_task(self.send_ctrl("aircraft", AIRCRAFT_CHANNEL_THROTTLE, 1400))
            t2 = asyncio.create_task(self.send_ctrl("vehicle", VEHICLE_CHANNEL_THROTTLE, 1300))
            await asyncio.gather(t1, t2)
            count += 1
        logger.info(f">>> 协同后退完成，共发送 {count} 次协同控制指令")

    async def disconnect(self):
        """断开连接"""
        logger.info(">>> 开始断开WebSocket连接")
        self.is_connected = False
        if self.recv_task:
            logger.info(">>> 取消遥测数据接收任务")
            self.recv_task.cancel()
            try:
                await self.recv_task
            except asyncio.CancelledError:
                logger.debug(">>> 遥测数据接收任务已取消")
        if self.ws:
            logger.info(">>> 关闭WebSocket连接")
            await self.ws.close()
        logger.info(">>> 连接已断开")

    # ===================== 导航控制函数 =====================
    async def navigate_to_position(self, target: str, target_x: float, target_z: float, tolerance: float = 0.5):
        """导航到指定坐标：先调整朝向，再前进"""
        logger.info(f"[{target}] ========== 开始导航 ==========")
        logger.info(f"[{target}] 目标位置: ({target_x:.4f}, {target_z:.4f})")
        
        # 计算距离和目标角度
        if target == "aircraft":
            current_x, current_z = self.telemetry_data["aircraft"]["gps"]
        else:
            current_x, current_z = self.telemetry_data["vehicle"]["gps"]
        
        dx = target_x - current_x
        dz = target_z - current_z
        distance = math.sqrt(dx * dx + dz * dz)
        
        logger.info(f"[{target}] 当前位置: ({current_x:.4f}, {current_z:.4f})")
        logger.info(f"[{target}] 距离目标: {distance:.4f}米")
        
        # 计算目标角度（弧度）
        target_angle = math.atan2(dx, dz)
        target_angle_deg = target_angle * 180 / math.pi
        logger.info(f"[{target}] 目标角度: {target_angle:.4f}弧度 ({target_angle_deg:.2f}度)")
        
        # 调整朝向到目标角度
        # 假设当前朝向为0度（正北），需要转到目标角度
        if abs(target_angle) > 0.1:  # 角度差大于0.1弧度时调整
            turn_duration = abs(target_angle) * 0.5  # 根据角度差计算转向时间
            logger.info(f"[{target}] 调整朝向 {turn_duration:.2f}秒")
            
            if target_angle > 0:
                # 目标在右侧，右转
                if target == "aircraft":
                    await self.aircraft_turn_right(turn_duration)
                else:
                    await self.vehicle_turn_right(turn_duration)
            else:
                # 目标在左侧，左转
                if target == "aircraft":
                    await self.aircraft_turn_left(turn_duration)
                else:
                    await self.vehicle_turn_left(turn_duration)
            
            await asyncio.sleep(1)
        
        # 前进到目标位置
        move_duration = distance / 5.0  # 每秒移动约5米
        logger.info(f"[{target}] 执行前进 {move_duration:.2f}秒")
        
        if target == "aircraft":
            await self.aircraft_forward(move_duration)
        else:
            await self.vehicle_forward(move_duration)
        
        logger.info(f"[{target}] ========== 导航完成 ==========")

    async def aircraft_cross_arch(self, arch: Dict):
        """无人机穿越指定拱门"""
        grid_x, grid_z = arch["x"], arch["z"]
        target_x, target_z = grid_to_scene(grid_x, grid_z)
        
        logger.info(f"========== 无人机穿越拱门 ==========")
        logger.info(f"拱门网格坐标: ({grid_x}, {grid_z})")
        logger.info(f"拱门场景坐标: ({target_x:.4f}, {target_z:.4f})")
        logger.info(f"拱门方向: {arch['dir']}")
        
        # 根据拱门方向确定穿越策略
        if arch['dir'] == 'vertical':
            # 竖拱门：从前后方向穿越
            approach_x = target_x
            approach_z = target_z - 2  # 拱门前2米
            logger.info(f"导航到拱门前位置: ({approach_x:.4f}, {approach_z:.4f})")
            await self.navigate_to_position("aircraft", approach_x, approach_z)
            await asyncio.sleep(1)
            
            # 穿越拱门
            logger.info(f"执行穿越拱门：前进4秒")
            await self.aircraft_forward(4)
            await asyncio.sleep(1)
        else:
            # 横拱门：从左右方向穿越
            approach_x = target_x - 2  # 拱门左侧2米
            approach_z = target_z
            logger.info(f"导航到拱门左侧位置: ({approach_x:.4f}, {approach_z:.4f})")
            await self.navigate_to_position("aircraft", approach_x, approach_z)
            await asyncio.sleep(1)
            
            # 穿越拱门
            logger.info(f"执行穿越拱门：右移4秒")
            await self.aircraft_right(4)
            await asyncio.sleep(1)
        
        logger.info(f"========== 无人机穿越拱门完成 ==========")

    async def vehicle_navigate_maze(self):
        """无人车穿越迷宫"""
        logger.info("========== 无人车开始穿越迷宫 ==========")
        
        # 定义迷宫路径（关键点）
        path_points = [
            {"x": 370, "z": 930},  # 第一个关键点
            {"x": 280, "z": 960},  # 第二个关键点
            {"x": 200, "z": 1020}, # 第三个关键点
            {"x": 280, "z": 1080}, # 第四个关键点
        ]
        
        logger.info(f"迷宫路径包含 {len(path_points)} 个关键点")
        
        for i, point in enumerate(path_points):
            target_x, target_z = grid_to_scene(point["x"], point["z"])
            logger.info(f"---------- 导航到第{i+1}个关键点 ----------")
            logger.info(f"关键点网格坐标: ({point['x']}, {point['z']})")
            logger.info(f"关键点场景坐标: ({target_x:.4f}, {target_z:.4f})")
            
            await self.navigate_to_position("vehicle", target_x, target_z)
            await asyncio.sleep(2)
            
            logger.info(f"第{i+1}个关键点到达完成")
        
        logger.info("========== 无人车穿越迷宫完成 ==========")

    # ===================== 自动化任务函数 =====================
    async def auto_mission(self):
        """自动化任务：无人机起飞观测 -> 引导车辆穿越 -> 精准降落 -> 冲刺"""
        logger.info("========================================")
        logger.info("========== 自动化任务开始 ==========")
        logger.info("========================================")
        
        try:
            # 1. 连接WebSocket
            logger.info("步骤1: 连接WebSocket服务器")
            await self.connect_websocket()
            logger.info("WebSocket连接成功")
            
            # 2. 无人机起飞
            logger.info("步骤2: 无人机起飞")
            await self.aircraft_takeoff()
            logger.info("无人机起飞完成")
            
            # 3. 无人机观测迷宫（云台控制）
            logger.info("步骤3: 无人机观测迷宫")
            logger.info("云台复位")
            await self.aircraft_gimbal_reset()
            await asyncio.sleep(2)
            logger.info("云台俯视3秒")
            await self.aircraft_gimbal_down(3)
            logger.info("云台仰视3秒")
            await self.aircraft_gimbal_up(3)
            logger.info("云台复位")
            await self.aircraft_gimbal_reset()
            
            # 4. 抓拍图像用于环境识别
            logger.info("步骤4: 抓拍环境图像")
            self.capture_image()
            
            # 5. 无人机自动穿越拱门
            logger.info("步骤5: 无人机开始穿越拱门")
            logger.info(f"共有 {len(ARCHES)} 个拱门需要穿越")
            for i, arch in enumerate(ARCHES):
                logger.info(f"========== 开始穿越第{i+1}/{len(ARCHES)}个拱门 ==========")
                await self.aircraft_cross_arch(arch)
                await asyncio.sleep(2)
                logger.info(f"========== 第{i+1}个拱门穿越完成 ==========")
            
            # 6. 无人车自动穿越迷宫
            logger.info("步骤6: 无人车自动穿越迷宫")
            await self.vehicle_navigate_maze()
            
            # 7. 无人机精准降落
            logger.info("步骤7: 无人机精准降落")
            logger.info("无人机下降3秒")
            await self.aircraft_down(3)
            logger.info("无人机降落")
            await self.aircraft_land()
            
            # 8. 车辆携带无人机冲刺
            logger.info("步骤8: 车辆携带无人机冲刺10秒")
            await self.vehicle_forward(10)
            
            logger.info("========================================")
            logger.info("========== 自动化任务完成 ==========")
            logger.info("========================================")
            
        except Exception as e:
            logger.error(f"========================================")
            logger.error(f"任务执行异常：{str(e)}")
            logger.error(f"========================================")
        finally:
            logger.info("断开连接")
            await self.disconnect()

    async def test_arch_crossing(self):
        """测试无人机穿越拱门"""
        try:
            await self.connect_websocket()
            await self.aircraft_takeoff()
            
            # 测试穿越第一个拱门
            await self.aircraft_cross_arch(ARCHES[1])  # 测试 x:370, z:930 的拱门
            
            await self.aircraft_land()
        except Exception as e:
            logger.error(f"测试异常：{str(e)}")
        finally:
            await self.disconnect()

    async def test_maze_navigation(self):
        """测试无人车穿越迷宫"""
        try:
            await self.connect_websocket()
            await self.vehicle_navigate_maze()
        except Exception as e:
            logger.error(f"测试异常：{str(e)}")
        finally:
            await self.disconnect()

if __name__ == "__main__":
    system = AutoControlSystem()
    asyncio.run(system.auto_mission())
