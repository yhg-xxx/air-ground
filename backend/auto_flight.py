"""
无人机自动飞行模块
自动起飞并按照路径规划穿越拱门1-8，然后飞到终点
"""

import json
import asyncio
import websockets
import time
from typing import List, Tuple
import math
from flight_config import (
    get_auth_token, 
    load_and_convert_waypoints, 
    SERVER_CONFIG, 
    FLIGHT_PARAMS
)

class AutoFlightController:
    def __init__(self, token: str = None):
        self.ws_url = f"ws://{SERVER_CONFIG['WS_HOST']}:{SERVER_CONFIG['WS_PORT']}"
        self.token = token
        self.ws = None
        self.is_connected = False
        
        # 飞行参数
        self.current_position = [0, 0, 0]  # [lat, lon, altitude]
        self.takeoff_altitude = None       # 起飞后的高度
        self.target_waypoint = None
        self.waypoint_index = 0
        self.flight_waypoints = []
        
        # 控制参数（从配置文件加载）
        self.position_tolerance = FLIGHT_PARAMS["POSITION_TOLERANCE"]
        self.altitude_tolerance = FLIGHT_PARAMS["ALTITUDE_TOLERANCE"] 
        self.max_speed = FLIGHT_PARAMS["MAX_SPEED"]
        self.control_frequency = FLIGHT_PARAMS["CONTROL_FREQUENCY"]
        
        # 控制通道
        self.CHANNELS = {
            'DIRECTION': 1,     # 左转右转
            'ALTITUDE': 2,      # 上升下降
            'MOVEMENT': 3,      # 左移右移
            'THROTTLE': 4,      # 前进后退
            'TAKEOFF': 7,       # 起飞
            'LAND': 8,          # 降落
        }
    
    async def connect(self):
        """连接WebSocket"""
        try:
            url = f"{self.ws_url}?token={self.token}" if self.token else self.ws_url
            print(f"连接WebSocket: {url}")
            self.ws = await websockets.connect(url)
            self.is_connected = True
            print("✅ WebSocket连接成功")
            return True
        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.ws:
            await self.ws.close()
            self.is_connected = False
            print("WebSocket已断开")
    
    async def send_control(self, channel: int, value: int):
        """发送控制指令"""
        if not self.is_connected or not self.ws:
            print("⚠️ WebSocket未连接，无法发送控制指令")
            return
        
        message = {
            "type": "control",
            "target": "aircraft",
            "channel": channel,
            "value": value
        }
        
        try:
            await self.ws.send(json.dumps(message))
            print(f"[aircraft] 通道{channel} → {value}")
        except Exception as e:
            print(f"❌ 发送控制指令失败: {e}")
    
    async def listen_telemetry(self):
        """监听遥测数据"""
        try:
            while self.is_connected and self.ws:
                message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(message)
                
                if data.get('type') == 'aircraft_telemetry_gnss':
                    gps_data = data.get('data', {})
                    gps = gps_data.get('gps', [])
                    altitude = gps_data.get('altitude', '0')
                    
                    if len(gps) >= 2:
                        self.current_position[0] = float(gps[0])
                        self.current_position[1] = float(gps[1])
                        try:
                            self.current_position[2] = float(altitude)
                        except:
                            self.current_position[2] = 0
                        
                        print(f"📍 当前位置: ({self.current_position[0]:.6f}, {self.current_position[1]:.6f}, {self.current_position[2]:.1f}m)")
                
        except asyncio.TimeoutError:
            pass  # 正常超时，继续循环
        except Exception as e:
            print(f"❌ 遥测数据接收错误: {e}")
    
    def load_flight_path(self, json_path: str = "output/drone_flight_path.json"):
        """加载飞行路径"""
        try:
            # 使用配置模块转换航点
            self.flight_waypoints = load_and_convert_waypoints(json_path)
            
            if self.flight_waypoints:
                print(f"✅ 成功加载飞行路径，共 {len(self.flight_waypoints)} 个航点")
                return True
            else:
                print("❌ 未能加载任何航点")
                return False
            
        except Exception as e:
            print(f"❌ 加载飞行路径失败: {e}")
            return False
    
    def calculate_control_values(self, target_pos: List[float]) -> dict:
        """计算到达目标位置的控制值"""
        if not self.current_position or not target_pos:
            return {'direction': 1500, 'altitude': 1500, 'movement': 1500, 'throttle': 1500}
        
        # 计算位置差
        dx = target_pos[0] - self.current_position[0]
        dy = target_pos[1] - self.current_position[1] 
        dz = target_pos[2] - self.current_position[2]
        
        # 计算控制值 (1000-2000范围，1500为中位)
        controls = {'direction': 1500, 'altitude': 1500, 'movement': 1500, 'throttle': 1500}
        
        # 高度控制
        if abs(dz) > self.altitude_tolerance:
            altitude_factor = min(abs(dz) / 5.0, 1.0) * 500  # 最大偏移500
            if dz > 0:  # 需要上升
                controls['altitude'] = int(1500 + altitude_factor)
            else:  # 需要下降
                controls['altitude'] = int(1500 - altitude_factor)
        
        # 水平距离
        horizontal_distance = math.sqrt(dx*dx + dy*dy)
        
        if horizontal_distance > self.position_tolerance:
            # 归一化方向向量
            if horizontal_distance > 0:
                dx_norm = dx / horizontal_distance
                dy_norm = dy / horizontal_distance
                
                # 限制最大移动速度
                move_factor = min(horizontal_distance / 10.0, 1.0) * 500
                
                # X轴移动（左右）
                if abs(dx) > 0.5:  # 0.5米容差
                    if dx > 0:  # 向右
                        controls['movement'] = int(1500 + move_factor * abs(dx_norm))
                    else:  # 向左
                        controls['movement'] = int(1500 - move_factor * abs(dx_norm))
                
                # Y轴移动（前后）
                if abs(dy) > 0.5:  # 0.5米容差
                    if dy > 0:  # 向前
                        controls['throttle'] = int(1500 + move_factor * abs(dy_norm))
                    else:  # 向后
                        controls['throttle'] = int(1500 - move_factor * abs(dy_norm))
        
        # 限制控制值范围
        for key in controls:
            controls[key] = max(1000, min(2000, controls[key]))
        
        return controls
    
    def is_waypoint_reached(self, target_pos: List[float]) -> bool:
        """检查是否到达航点"""
        if not self.current_position or not target_pos:
            return False
        
        dx = target_pos[0] - self.current_position[0]
        dy = target_pos[1] - self.current_position[1]
        dz = target_pos[2] - self.current_position[2]
        
        horizontal_distance = math.sqrt(dx*dx + dy*dy)
        
        return (horizontal_distance <= self.position_tolerance and 
                abs(dz) <= self.altitude_tolerance)
    
    async def takeoff(self):
        """起飞"""
        print("🚁 开始起飞...")
        await self.send_control(self.CHANNELS['TAKEOFF'], 2000)
        await asyncio.sleep(0.5)
        await self.send_control(self.CHANNELS['TAKEOFF'], 1500)
        
        # 等待起飞完成并记录起飞高度
        print("⏳ 等待起飞完成...")
        
        # 启动遥测监听来获取起飞高度
        telemetry_task = asyncio.create_task(self.listen_telemetry())
        
        # 等待获取到稳定的高度数据
        start_time = time.time()
        while time.time() - start_time < 10:  # 最多等待10秒
            if self.current_position[2] > 0.5:  # 高度大于0.5米说明已起飞
                self.takeoff_altitude = self.current_position[2]
                break
            await asyncio.sleep(0.5)
        
        telemetry_task.cancel()
        
        if self.takeoff_altitude:
            print(f"✅ 起飞完成，起飞高度: {self.takeoff_altitude:.1f}m")
            # 更新所有航点的高度为起飞高度
            for waypoint in self.flight_waypoints:
                if waypoint[2] is None:  # 如果高度为None，设为起飞高度
                    waypoint[2] = self.takeoff_altitude
        else:
            print("⚠️ 未能获取起飞高度，使用默认高度3.0m")
            self.takeoff_altitude = 3.0
            for waypoint in self.flight_waypoints:
                if waypoint[2] is None:
                    waypoint[2] = self.takeoff_altitude
    
    async def land(self):
        """降落"""
        print("🛬 开始降落...")
        await self.send_control(self.CHANNELS['LAND'], 2000)
        await asyncio.sleep(0.5)
        await self.send_control(self.CHANNELS['LAND'], 1500)
        print("✅ 降落指令已发送")
    
    async def hover(self):
        """悬停（所有控制值归中）"""
        await self.send_control(self.CHANNELS['DIRECTION'], 1500)
        await self.send_control(self.CHANNELS['ALTITUDE'], 1500)
        await self.send_control(self.CHANNELS['MOVEMENT'], 1500)
        await self.send_control(self.CHANNELS['THROTTLE'], 1500)
    
    async def execute_auto_flight(self):
        """执行自动飞行任务"""
        if not self.flight_waypoints:
            print("❌ 未加载飞行路径")
            return False
        
        print(f"🎯 开始自动飞行任务，共 {len(self.flight_waypoints)} 个航点")
        
        # 起飞
        await self.takeoff()
        
        # 创建遥测监听任务
        telemetry_task = asyncio.create_task(self.listen_telemetry())
        
        try:
            # 逐个飞向航点
            for i, waypoint in enumerate(self.flight_waypoints):
                self.waypoint_index = i
                self.target_waypoint = waypoint
                
                print(f"\n🎯 飞向航点 {i+1}/{len(self.flight_waypoints)}: ({waypoint[0]:.6f}, {waypoint[1]:.6f}, {waypoint[2]}m)")
                
                # 飞向航点
                start_time = time.time()
                timeout = 60  # 60秒超时
                
                while not self.is_waypoint_reached(waypoint):
                    # 检查超时
                    if time.time() - start_time > timeout:
                        print(f"⚠️ 航点 {i+1} 飞行超时")
                        break
                    
                    # 计算控制值
                    controls = self.calculate_control_values(waypoint)
                    
                    # 发送控制指令
                    await self.send_control(self.CHANNELS['DIRECTION'], controls['direction'])
                    await self.send_control(self.CHANNELS['ALTITUDE'], controls['altitude'])
                    await self.send_control(self.CHANNELS['MOVEMENT'], controls['movement'])
                    await self.send_control(self.CHANNELS['THROTTLE'], controls['throttle'])
                    
                    # 等待控制周期
                    await asyncio.sleep(1.0 / self.control_frequency)
                
                print(f"✅ 到达航点 {i+1}")
                
                # 短暂悬停
                await self.hover()
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"❌ 自动飞行出错: {e}")
            return False
        
        finally:
            telemetry_task.cancel()
        
        print("\n🎉 所有航点飞行完成！开始降落...")
        await self.land()
        
        return True


async def main():
    """主程序"""
    # 获取认证Token
    print("🔐 正在获取认证Token...")
    token = get_auth_token()
    if not token:
        print("❌ 无法获取Token，退出")
        return
    
    # 创建自动飞行控制器
    controller = AutoFlightController(token)
    
    try:
        # 加载飞行路径
        if not controller.load_flight_path():
            print("❌ 无法加载飞行路径，退出")
            return
        
        # 连接WebSocket
        if not await controller.connect():
            print("❌ 无法连接WebSocket，退出")
            return
        
        print("=" * 50)
        print("🚁 无人机自动飞行系统")
        print("📍 任务：穿越拱门1-8")
        print("=" * 50)
        
        # 执行自动飞行
        success = await controller.execute_auto_flight()
        
        if success:
            print("\n🎉 自动飞行任务完成！")
        else:
            print("\n❌ 自动飞行任务失败")
    
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断，停止飞行")
    
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
    
    finally:
        await controller.disconnect()


if __name__ == "__main__":
    print("🚁 无人机自动穿越拱门系统")
    print("⚡ 使用方法：python auto_flight.py")
    print("📋 确保已运行路径规划生成航点数据")
    print("-" * 40)
    
    # 运行主程序
    asyncio.run(main())
