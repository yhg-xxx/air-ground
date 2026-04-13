import http.server
import socketserver
import json
import base64
import random
import time
import threading
import websockets
import asyncio

# 全局变量
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
AUTH_USERNAME = "fcs002"
AUTH_PASSWORD = "fcs002fcs002"

# 模拟物体位置
aircraft_position = [0.5687, 1.3854]
vehicle_position = [0.5687, 1.3854]

# 全局变量
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
AUTH_USERNAME = "fcs002"
AUTH_PASSWORD = "fcs002fcs002"

# 模拟物体位置和状态
aircraft_position = [0.5687, 1.3854]
aircraft_altitude = 10.0  # 无人机高度
vehicle_position = [0.5687, 1.3854]

# 控制指令处理
def handle_control_command(command):
    global aircraft_position, aircraft_altitude, vehicle_position
    
    target = command.get('target')
    channel = command.get('channel')
    value = command.get('value')
    
    # 移动速度因子
    speed = 0.001
    altitude_speed = 0.1  # 高度变化速度
    
    if target == 'aircraft':
        if channel == 1:  # 左转/右转
            if value > 1500:  # 右转
                aircraft_position[0] += speed * (value - 1500) / 500
            elif value < 1500:  # 左转
                aircraft_position[0] -= speed * (1500 - value) / 500
        elif channel == 2:  # 上升/下降
            if value > 1500:  # 上升
                aircraft_altitude += altitude_speed * (value - 1500) / 500
            elif value < 1500:  # 下降
                aircraft_altitude -= altitude_speed * (1500 - value) / 500
                if aircraft_altitude < 0:  # 防止高度为负
                    aircraft_altitude = 0
        elif channel == 3:  # 左移/右移
            if value > 1500:  # 右移
                aircraft_position[0] += speed * (value - 1500) / 500
            elif value < 1500:  # 左移
                aircraft_position[0] -= speed * (1500 - value) / 500
        elif channel == 4:  # 前进/后退
            if value > 1500:  # 前进
                aircraft_position[1] += speed * (value - 1500) / 500
            elif value < 1500:  # 后退
                aircraft_position[1] -= speed * (1500 - value) / 500
        elif channel == 7:  # 起飞
            if value >= 1500:  # 执行起飞
                aircraft_altitude = 10.0  # 设置初始高度
        elif channel == 8:  # 降落
            if value >= 1500:  # 执行降落
                aircraft_altitude = 0.0  # 降落到地面
        elif channel == 9:  # 返航
            if value >= 1500:  # 执行返航
                aircraft_position = [0.5687, 1.3854]  # 返回到初始位置
        elif channel == 10:  # 云台复位
            if value >= 1500:  # 执行云台复位
                # 云台复位逻辑
                pass
    
    elif target == 'vehicle':
        if channel == 1:  # 前进/后退
            if value > 1500:  # 前进
                vehicle_position[1] += speed * (value - 1500) / 500
            elif value < 1500:  # 后退
                vehicle_position[1] -= speed * (1500 - value) / 500
        elif channel == 2:  # 左转/右转
            if value > 1500:  # 右转
                vehicle_position[0] += speed * (value - 1500) / 500
            elif value < 1500:  # 左转
                vehicle_position[0] -= speed * (1500 - value) / 500

# 模拟心跳和遥测数据发送
async def send_telemetry(websocket):
    while True:
        # 发送心跳
        await websocket.send(json.dumps({"type": "ping"}))
        await asyncio.sleep(1)
        
        # 发送无人机电量
        await websocket.send(json.dumps({
            "type": "aircraft_telemetry_power",
            "data": {
                "power": 1,
                "voltage": 9.6 + random.uniform(-0.1, 0.1)
            }
        }))
        await asyncio.sleep(1)
        
        # 发送无人机定位
        await websocket.send(json.dumps({
            "type": "aircraft_telemetry_gnss",
            "data": {
                "gps": [
                    aircraft_position[0] + random.uniform(-0.00005, 0.00005),
                    aircraft_position[1] + random.uniform(-0.00005, 0.00005)
                ],
                "speed": str(6.7 + random.uniform(-0.5, 0.5)),
                "altitude": str(aircraft_altitude + random.uniform(-0.1, 0.1))
            }
        }))
        await asyncio.sleep(1)
        
        # 发送车辆电量
        await websocket.send(json.dumps({
            "type": "vehicle_telemetry_power",
            "data": {
                "power": 1,
                "voltage": 9.6 + random.uniform(-0.1, 0.1)
            }
        }))
        await asyncio.sleep(1)
        
        # 发送车辆定位
        await websocket.send(json.dumps({
            "type": "vehicle_telemetry_gnss",
            "data": {
                "gps": [
                    vehicle_position[0] + random.uniform(-0.00005, 0.00005),
                    vehicle_position[1] + random.uniform(-0.00005, 0.00005)
                ],
                "speed": str(6.7 + random.uniform(-0.5, 0.5))
            }
        }))
        await asyncio.sleep(1)

# WebSocket 处理函数
async def websocket_handler(websocket):
    # 检查 token
    path = websocket.request.path
    token = path.split('?token=')[1] if '?token=' in path else None
    if token != TOKEN:
        await websocket.close()
        return
    
    # 发送认证成功消息
    await websocket.send(json.dumps({"code": 200, "type": "auth_success", "msg": "Success"}))
    
    # 启动遥测数据发送
    telemetry_task = asyncio.create_task(send_telemetry(websocket))
    
    try:
        while True:
            # 接收控制指令
            message = await websocket.recv()
            print(f"Received control command: {message}")
            # 处理控制指令
            try:
                command = json.loads(message)
                if command.get('type') == 'control':
                    handle_control_command(command)
            except json.JSONDecodeError:
                print("Invalid JSON command")
    except websockets.exceptions.ConnectionClosed:
        telemetry_task.cancel()
        print("WebSocket connection closed")

# HTTP 请求处理器
class RequestHandler(http.server.BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        # 认证接口
        if self.path == "/api/auth/token":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            if data.get("username") == AUTH_USERNAME and data.get("password") == AUTH_PASSWORD:
                response = {
                    "code": "1",
                    "msg": "success",
                    "data": {
                        "token": TOKEN
                    }
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                response = {
                    "code": "0",
                    "msg": "invalid credentials"
                }
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
        
        # 云台抓拍接口
        elif self.path == "/api/gimbal/capture":
            # 检查 Authorization 头
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self.send_response(401)
                self._set_cors_headers()
                self.end_headers()
                return
            
            token = auth_header.split(' ')[1]
            if token != TOKEN:
                self.send_response(401)
                self._set_cors_headers()
                self.end_headers()
                return
            
            # 生成模拟图片（1x1 像素的红色图片）
            # 实际项目中可以返回真实图片或更复杂的模拟图片
            img_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')
            
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', len(img_data))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(img_data)
        
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(b"webman")

    def do_GET(self):
        self.send_response(404)
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(b"webman")

# 启动 HTTP 服务器
def start_http_server():
    PORT = 30080
    Handler = RequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"HTTP server running at http://localhost:{PORT}")
        httpd.serve_forever()

# 启动 WebSocket 服务器
async def start_websocket_server():
    PORT = 30081
    async with websockets.serve(websocket_handler, "", PORT):
        print(f"WebSocket server running at ws://localhost:{PORT}")
        await asyncio.Future()  # 保持运行

# 主函数
async def main():
    # 在单独的线程中启动 HTTP 服务器
    import threading
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # 启动 WebSocket 服务器
    await start_websocket_server()

if __name__ == "__main__":
    asyncio.run(main())
