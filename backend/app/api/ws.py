from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.ws_service import WebSocketService

router = APIRouter(prefix="/api/ws", tags=["websocket"])

# 全局WebSocket服务实例
ws_service = WebSocketService()

@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点
    
    Args:
        websocket: WebSocket连接对象
    """
    await websocket.accept()
    
    try:
        # 连接到外部WebSocket服务
        await ws_service.connect()
        
        # 定义消息处理器
        def handle_message(data):
            # 转发消息到客户端
            import asyncio
            asyncio.create_task(websocket.send_json(data))
        
        ws_service.message_handler = handle_message
        
        # 接收客户端消息
        while True:
            data = await websocket.receive_json()
            # 处理客户端发送的控制指令
            if data.get("type") == "control":
                target = data.get("target")
                channel = data.get("channel")
                value = data.get("value")
                if target and channel and value:
                    await ws_service.send_control(target, channel, value)
    except WebSocketDisconnect:
        print("客户端断开连接")
    except Exception as e:
        print(f"WebSocket错误：{str(e)}")
    finally:
        # 断开WebSocket连接
        await ws_service.disconnect()
