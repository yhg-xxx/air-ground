import asyncio
import json
from loguru import logger
import websockets

from demo_auth import get_token

# ===================== 官方通道定义 =====================
"""     
        //1 左转 2000 回中 1500 右转 1000
        //2 前进 2000 停止 1500 后退 1000

        //无人机控制：
        //1 左转 1000 右转 2000
        //2 下降 1000 上升 2000
        //3 左移 1000 右移 2000
        //4 后退 1000 前进 2000
        //5 云台俯 1000 云台仰 2000
        //6 云台横滚 1000 2000

        //7 [起飞] 2000
        //8 [降落] 2000
        //9 [返航] 2000
        //10 [云台复位] 2000
"""
WS_HOST = "fcs.botzooo.com"
WS_PORT = 30081  
# 车辆通道
VEHICLE_CHANNEL_DIRECTION = 1    # 左转/右转
VEHICLE_CHANNEL_THROTTLE = 2    # 前进/后退
# 无人机通道
AIRCRAFT_CHANNEL_DIRECTION = 1    # 左转/右转
AIRCRAFT_CHANNEL_ALTITUDE = 2    # 下降/上升
AIRCRAFT_CHANNEL_MOVEMENT = 3    # 左移/右移
AIRCRAFT_CHANNEL_THROTTLE = 4   # 后退/前进
AIRCRAFT_CHANNEL_GIMBAL_PITCH = 5     # 云台俯仰 1000下 2000上
AIRCRAFT_CHANNEL_GIMBAL_ROLL = 6     # 云台横滚 1000右 2000左
AIRCRAFT_CHANNEL_TAKEOFF = 7    # 起飞
AIRCRAFT_CHANNEL_LAND = 8        # 降落
AIRCRAFT_CHANNEL_BACK = 9        # 返航
AIRCRAFT_CHANNEL_GIMBAL_RESET = 10    # 云台复位
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
    await asyncio.sleep(MIN_INTERVAL)

async def ws_demo(token):
    ws_url = f"ws://{WS_HOST}:{WS_PORT}?token={token}"
    logger.info("连接比赛官方WebSocket服务：", ws_url)
    # 标记连接状态
    is_connected = True
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        # 循环接收遥测 & 心跳
        async def recv_loop():
            nonlocal is_connected
            try:
                while is_connected:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    typ = data.get("type")

                    if typ == "auth_success":
                        logger.info("【官方】WebSocket 登录成功")
                    elif typ == "ping":
                        logger.info("【官方】收到服务端心跳")
                    elif typ == "aircraft_telemetry_power":
                        p = data["data"]["power"]
                        v = data["data"]["voltage"]
                        logger.info(f"【遥测】无人机 电量={p} 电压={v}V")
                    elif typ == "aircraft_telemetry_gnss":
                        gps = data["data"]["gps"]
                        speed = data["data"]["speed"]
                        logger.info(f"【遥测】无人机 GPS={gps} 速度={speed}")
                    elif typ == "vehicle_telemetry_power":
                        p = data["data"]["power"]
                        v = data["data"]["voltage"]
                        logger.info(f"【遥测】车辆 电量={p} 电压={v}V")
                    elif typ == "vehicle_telemetry_gnss":
                        gps = data["data"]["gps"]
                        speed = data["data"]["speed"]
                        logger.info(f"【遥测】车辆 GPS={gps} 速度={speed}")
            except websockets.exceptions.ConnectionClosed:
                # 捕获连接关闭异常，优雅处理
                print("WebSocket连接已正常关闭")
            except Exception as e:
                print(f"接收消息异常：{str(e)}")
        # 启动接收
        recv_task = asyncio.create_task(recv_loop())
        await asyncio.sleep(1)

        logger.info("\n===== 比赛官方API控制演示开始 =====")

        # # ------------------------------
        # # 1. 无人机起飞
        # # ------------------------------
        # logger.info("\n【步骤1】无人机起飞 起飞稳定15秒")
        # await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_TAKEOFF, 2000)
        # await asyncio.sleep(15)  # 起飞稳定15秒
        #
        # # ------------------------------
        # # 2. 无人机单独顺序动作
        # # ------------------------------
        # logger.info("\n【步骤2】无人机 顺序控制")
        # # 前进3秒
        # logger.info("→ 无人机前进 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_THROTTLE, 1600)
        #
        # # 后退3秒
        # logger.info("→ 无人机后退 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_THROTTLE, 1400)
        #
        # # 左移3秒
        # logger.info("→ 无人机左移 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_MOVEMENT, 1400)
        #
        # # 右移3秒
        # logger.info("→ 无人机右移 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_MOVEMENT, 1600)
        #
        #
        # # 左转3秒
        # logger.info("→ 无人机左转 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_DIRECTION, MIN)
        #
        # # 右转3秒
        # logger.info("→ 无人机右转 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_DIRECTION, MAX)
        #
        #
        # # 上升3秒
        # logger.info("→ 无人机上升 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_ALTITUDE, 1600)
        #
        # # 下降3秒
        # logger.info("→ 无人机下降 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_ALTITUDE, 1400)
        #
        # # 云台复位 等待3秒
        # logger.info("→ 云台复位 3秒")
        # await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_GIMBAL_RESET, MAX)
        # await asyncio.sleep(3)
        #
        #
        # # 云台俯仰3秒
        # logger.info("→ 云台俯 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_GIMBAL_PITCH, 1400)
        #
        # # 云台俯仰3秒
        # logger.info("→ 云台仰 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_GIMBAL_PITCH, 1600)
        #
        #
        # # 云台横滚3秒
        # logger.info("→ 云台右 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_GIMBAL_ROLL, 1450)
        #
        # # 云台横滚3秒
        # logger.info("→ 云台左 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_GIMBAL_ROLL, 1550)


        # ------------------------------
        # 3. 车辆单独顺序动作
        # ------------------------------
        logger.info("\n【步骤3】车辆 顺序控制")
        # 前进3秒
        # logger.info("→ 车辆前进 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_THROTTLE, 1700)

        # 后退3秒
        # logger.info("→ 车辆后退 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_THROTTLE, 1300)

        # # 左转3秒
        # logger.info("→ 车辆左转 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_DIRECTION, MIN)
        #
        # # 右转3秒
        # logger.info("→ 车辆右转 3秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 3:
        #     await send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_DIRECTION, MAX)


        # # ------------------------------
        # # 4. 无人机 + 车辆 同时：左转+前进 5秒
        # # ------------------------------
        # logger.info("\n【步骤4】无人机 + 车辆 同时 左移/转+前进 5秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 5:
        #     # 无人机：左转 + 前进
        #     t1 = asyncio.create_task(send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_DIRECTION, MIN))
        #     t2 = asyncio.create_task(send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_THROTTLE, 1600))
        #     # 车辆：左转 + 前进
        #     t3 = asyncio.create_task(send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_DIRECTION, MAX))
        #     t4 = asyncio.create_task(send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_THROTTLE, 1600))
        #     await asyncio.gather(t1, t2, t3, t4)
        #
        # # ------------------------------
        # # 5. 无人机 + 车辆 同时：左转+后退 5秒
        # # ------------------------------
        # logger.info("\n【步骤5】无人机 右移+后退 + 车辆 左移+后退 5秒")
        # start = asyncio.get_event_loop().time()
        # while asyncio.get_event_loop().time() - start < 5:
        #     # 无人机：右移 + 后退
        #     t1 = asyncio.create_task(send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_DIRECTION, MAX))
        #     t2 = asyncio.create_task(send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_THROTTLE, 1400))
        #     # 车辆：左转 + 后退
        #     t3 = asyncio.create_task(send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_DIRECTION, MAX))
        #     t4 = asyncio.create_task(send_ctrl(ws, "vehicle", VEHICLE_CHANNEL_THROTTLE, 1400))
        #     await asyncio.gather(t1, t2, t3, t4)

        # ------------------------------
        # 6. 停止发送 → 自动复位
        # ------------------------------
        logger.info("\n【步骤6】停止发送指令 → 100ms后设备自动复位停止")
        await asyncio.sleep(2)
    
        # ------------------------------
        # 7. 无人机降落
        # ------------------------------
        logger.info("\n【步骤7】无人机降落")
        await send_ctrl(ws, "aircraft", AIRCRAFT_CHANNEL_LAND, MAX)


        logger.info("\n===== 官方API演示完成 =====")
        # 标记连接关闭，停止接收任务
        is_connected = False

        # 停止接收任务
        recv_task.cancel()
        try:
            await recv_task
        except asyncio.CancelledError:
            # 静默处理取消异常，不打印任何信息
            pass


if __name__ == "__main__":
    try:
        token = get_token()
        asyncio.run(ws_demo(token))
    except Exception as e:
        print(f"\n异常：{str(e)}")
    finally:
        print("程序退出")