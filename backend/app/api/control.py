from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import asyncio
from backend.app.services.ws_service import WebSocketService
from backend.app.config.settings import *

router = APIRouter(prefix="/api/control", tags=["control"])

class ControlRequest(BaseModel):
    """控制请求模型"""
    target: str  # aircraft/vehicle
    channel: int  # 通道号
    value: int  # 控制值 1000-2000

# 全局WebSocket服务实例
ws_service = WebSocketService()

@router.post("/aircraft")
async def control_aircraft(channel: int, value: int):
    """控制无人机
    
    Args:
        channel: 通道号
        value: 控制值 1000-2000
        
    Returns:
        dict: 控制结果
    """
    try:
        # 验证通道号
        if not 1 <= channel <= 10:
            return {"code": "0", "msg": "无人机通道号必须在1-10之间"}
        
        # 验证控制值
        if not 1000 <= value <= 2000:
            return {"code": "0", "msg": "控制值必须在1000-2000之间"}
        
        # 发送控制指令
        await ws_service.send_control("aircraft", channel, value)
        
        return {
            "code": "1", 
            "msg": "无人机控制指令发送成功",
            "data": {
                "target": "aircraft",
                "channel": channel,
                "value": value
            }
        }
            
    except Exception as e:
        return {"code": "0", "msg": f"控制失败: {str(e)}"}

@router.post("/vehicle")
async def control_vehicle(channel: int, value: int):
    """控制无人车
    
    Args:
        channel: 通道号
        value: 控制值 1000-2000
        
    Returns:
        dict: 控制结果
    """
    try:
        # 验证通道号
        if not 1 <= channel <= 2:
            return {"code": "0", "msg": "无人车通道号必须在1-2之间"}
        
        # 验证控制值
        if not 1000 <= value <= 2000:
            return {"code": "0", "msg": "控制值必须在1000-2000之间"}
        
        # 发送控制指令
        await ws_service.send_control("vehicle", channel, value)
        
        return {
            "code": "1", 
            "msg": "无人车控制指令发送成功",
            "data": {
                "target": "vehicle",
                "channel": channel,
                "value": value
            }
        }
            
    except Exception as e:
        return {"code": "0", "msg": f"控制失败: {str(e)}"}

@router.post("/universal")
async def control_universal(request: ControlRequest):
    """通用控制接口
    
    Args:
        request: 通用控制请求
        
    Returns:
        dict: 控制结果
    """
    try:
        # 验证目标设备
        if request.target not in ["aircraft", "vehicle"]:
            return {"code": "0", "msg": "目标设备必须是aircraft或vehicle"}
        
        # 验证通道号
        if request.target == "aircraft" and not 1 <= request.channel <= 10:
            return {"code": "0", "msg": "无人机通道号必须在1-10之间"}
        elif request.target == "vehicle" and not 1 <= request.channel <= 2:
            return {"code": "0", "msg": "无人车通道号必须在1-2之间"}
        
        # 验证控制值
        if not 1000 <= request.value <= 2000:
            return {"code": "0", "msg": "控制值必须在1000-2000之间"}
        
        # 发送控制指令
        await ws_service.send_control(request.target, request.channel, request.value)
        
        return {
            "code": "1", 
            "msg": f"{request.target}控制指令发送成功",
            "data": {
                "target": request.target,
                "channel": request.channel,
                "value": request.value
            }
        }
            
    except Exception as e:
        return {"code": "0", "msg": f"控制失败: {str(e)}"}

@router.get("/status")
async def get_control_status():
    """获取控制状态
    
    Returns:
        dict: 控制状态
    """
    try:
        return {
            "code": "1",
            "msg": "获取状态成功",
            "data": {
                "websocket_connected": ws_service.is_connected,
                "channels": {
                    "aircraft": {
                        "direction": AIRCRAFT_CHANNEL_DIRECTION,
                        "altitude": AIRCRAFT_CHANNEL_ALTITUDE,
                        "movement": AIRCRAFT_CHANNEL_MOVEMENT,
                        "throttle": AIRCRAFT_CHANNEL_THROTTLE,
                        "gimbal_pitch": AIRCRAFT_CHANNEL_GIMBAL_PITCH,
                        "gimbal_roll": AIRCRAFT_CHANNEL_GIMBAL_ROLL,
                        "takeoff": AIRCRAFT_CHANNEL_TAKEOFF,
                        "land": AIRCRAFT_CHANNEL_LAND,
                        "back": AIRCRAFT_CHANNEL_BACK,
                        "gimbal_reset": AIRCRAFT_CHANNEL_GIMBAL_RESET
                    },
                    "vehicle": {
                        "direction": VEHICLE_CHANNEL_DIRECTION,
                        "throttle": VEHICLE_CHANNEL_THROTTLE
                    }
                }
            }
        }
    except Exception as e:
        return {"code": "0", "msg": f"获取状态失败: {str(e)}"}

@router.post("/connect")
async def connect_websocket():
    """连接WebSocket
    
    Returns:
        dict: 连接结果
    """
    try:
        await ws_service.connect()
        return {"code": "1", "msg": "WebSocket连接成功"}
    except Exception as e:
        return {"code": "0", "msg": f"连接失败: {str(e)}"}

@router.post("/disconnect")
async def disconnect_websocket():
    """断开WebSocket连接
    
    Returns:
        dict: 断开结果
    """
    try:
        await ws_service.disconnect()
        return {"code": "1", "msg": "WebSocket连接已断开"}
    except Exception as e:
        return {"code": "0", "msg": f"断开失败: {str(e)}"}
