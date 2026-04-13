import asyncio
import json
from loguru import logger
import websockets
import sys
import os
import threading
import queue
import time

from demo_auth import get_token

# ===================== 官方通道定义 =====================
"""     
        //1 左转 2000 回中 1500 右转 1000
        //2 前进 2000 停止 1500 后退 1000
"""
WS_HOST = "fcs.botzooo.com"
WS_PORT = 30081
# 车辆通道
VEHICLE_CHANNEL_DIRECTION = 1  # 左转/右转
VEHICLE_CHANNEL_THROTTLE = 2  # 前进/后退

# 官方控制值
MAX = 2000
MIN = 1000
MID = 1500

# 最小间隔（官方定义）
MIN_INTERVAL = 0.1

logger.add(
    "api_demo.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="10MB"
)


async def send_ctrl(ws, target, channel, value):
    """官方标准控制指令发送函数"""
    msg = json.dumps({
        "type": "control",
        "target": target,
        "channel": channel,
        "value": value
    })
    await ws.send(msg)
    logger.info(f"[{target}] 通道{channel} 发送值 {value}")
    print(f"\n[控制] 通道{channel} = {value}")
    await asyncio.sleep(MIN_INTERVAL)


class KeyboardListener:
    def __init__(self):
        self.key_queue = queue.Queue()
        self.listener_thread = None
        self.running = False

    def start(self):
        """启动键盘监听线程"""
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        print("键盘监听已启动")

    def stop(self):
        """停止键盘监听"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1)

    def _listen_loop(self):
        """键盘监听循环"""
        if os.name == 'nt':  # Windows
            import msvcrt
            print("使用Windows键盘监听")
            while self.running:
                if msvcrt.kbhit():
                    try:
                        key = msvcrt.getch()
                        if key == b'\xe0':  # 特殊功能键
                            key = msvcrt.getch()
                            if key == b'H':  # 上箭头
                                self.key_queue.put('w')
                            elif key == b'P':  # 下箭头
                                self.key_queue.put('s')
                            elif key == b'K':  # 左箭头
                                self.key_queue.put('a')
                            elif key == b'M':  # 右箭头
                                self.key_queue.put('d')
                        elif key == b'\x1b':  # ESC
                            self.key_queue.put('esc')
                        elif key == b'\x03':  # Ctrl+C
                            self.key_queue.put('ctrl_c')
                        else:
                            try:
                                char = key.decode('utf-8', errors='ignore').lower()
                                if char in ['w', 's', 'a', 'd', 'x', 'q']:
                                    self.key_queue.put(char)
                            except:
                                pass
                    except Exception as e:
                        print(f"键盘输入错误: {e}")
                time.sleep(0.05)
        else:  # Unix/Linux
            import termios
            import tty
            import select
            import sys

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            print("使用Unix键盘监听")

            try:
                tty.setraw(fd)
                while self.running:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                    if rlist:
                        key = sys.stdin.read(1)
                        if key:
                            if ord(key) == 27:  # ESC
                                self.key_queue.put('esc')
                            elif ord(key) == 3:  # Ctrl+C
                                self.key_queue.put('ctrl_c')
                            elif key.lower() in ['w', 's', 'a', 'd', 'x', 'q']:
                                self.key_queue.put(key.lower())
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def get_key(self):
        """获取按键，非阻塞"""
        try:
            return self.key_queue.get_nowait()
        except queue.Empty:
            return None


async def ws_control(token):
    """WebSocket连接和键盘控制主函数"""
    ws_url = f"ws://{WS_HOST}:{WS_PORT}?token={token}"
    print(f"连接比赛官方WebSocket服务：{ws_url}")
    logger.info(f"连接比赛官方WebSocket服务：{ws_url}")

    is_connected = True
    keyboard = KeyboardListener()
    keyboard.start()

    # 当前控制状态
    current_direction = MID
    current_throttle = MID

    try:
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            # 接收遥测消息的任务
            async def recv_loop():
                nonlocal is_connected
                try:
                    while is_connected:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        typ = data.get("type")

                        if typ == "auth_success":
                            print("✓ WebSocket 登录成功")
                            logger.info("【官方】WebSocket 登录成功")
                        elif typ == "ping":
                            # 静默处理心跳
                            pass
                        elif typ == "vehicle_telemetry_power":
                            p = data["data"]["power"]
                            v = data["data"]["voltage"]
                            print(f"⚡ 电量: {p}% | 电压: {v}V")
                            logger.info(f"【车辆遥测】电量={p}% 电压={v}V")
                        elif typ == "vehicle_telemetry_gnss":
                            gps = data["data"]["gps"]
                            speed = data["data"]["speed"]
                            print(f"📍 GPS: {gps} | 速度: {speed}")
                            logger.info(f"【车辆遥测】GPS={gps} 速度={speed}")
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket连接已关闭")
                except Exception as e:
                    print(f"接收消息异常：{str(e)}")

            # 启动接收任务
            recv_task = asyncio.create_task(recv_loop())
            await asyncio.sleep(2)  # 等待连接稳定

            print("\n" + "=" * 60)
            print("🎮 车辆控制模式已启动")
            print("=" * 60)
            print("控制说明：")
            print("  W 或 ↑ - 前进")
            print("  S 或 ↓ - 后退")
            print("  A 或 ← - 左转")
            print("  D 或 → - 右转")
            print("  X     - 停止油门")
            print("  Q     - 方向回中")
            print("  ESC   - 退出程序")
            print("=" * 60)
            print("提示：按下按键后松开即可控制")
            print("控制台会显示发送的指令")
            print("=" * 60 + "\n")

            try:
                while True:
                    # 检查键盘输入
                    key = keyboard.get_key()

                    if key:
                        if key == 'esc':
                            print("\n收到ESC键，退出程序...")
                            break
                        elif key == 'ctrl_c':
                            print("\n收到Ctrl+C，退出程序...")
                            break

                        # 处理控制按键
                        new_direction = current_direction
                        new_throttle = current_throttle

                        if key == 'w':
                            new_throttle = 1700
                            print("↑ 前进")
                        elif key == 's':
                            new_throttle = 1300
                            print("↓ 后退")
                        elif key == 'x':
                            new_throttle = MID
                            print("⏹ 停止")
                        elif key == 'a':
                            new_direction = MIN
                            print("← 左转")
                        elif key == 'd':
                            new_direction = MAX
                            print("→ 右转")
                        elif key == 'q':
                            new_direction = MID
                            print("↺ 方向回中")

                        # 发送变化的控制指令
                        if new_direction != current_direction:
                            await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_DIRECTION, new_direction)
                            current_direction = new_direction

                        if new_throttle != current_throttle:
                            await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_THROTTLE, new_throttle)
                            current_throttle = new_throttle

                    # 短暂休眠，避免CPU占用过高
                    await asyncio.sleep(0.05)

            except KeyboardInterrupt:
                print("\n收到中断信号，退出程序...")
            finally:
                # 停止时发送停止指令
                print("\n发送停止指令...")
                await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_DIRECTION, MID)
                await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_THROTTLE, MID)

                # 关闭连接
                is_connected = False
                recv_task.cancel()
                try:
                    await recv_task
                except asyncio.CancelledError:
                    pass

                print("程序已安全退出")
    finally:
        keyboard.stop()


async def main():
    try:
        token = get_token()
        await ws_control(token)
    except Exception as e:
        print(f"程序异常: {e}")
        logger.error(f"程序异常: {e}")
    finally:
        print("\n程序结束")


if __name__ == "__main__":
    # 检查操作系统
    if os.name == 'nt':
        print("检测到Windows系统")
    else:
        print("检测到Unix/Linux系统")

    asyncio.run(main())