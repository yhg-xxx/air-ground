#!/usr/bin/env python3
"""
测试新的通信架构
"""

import asyncio
import requests
import json

# 后端API地址
BASE_URL = "http://localhost:8000"

async def test_connection_api():
    """测试连接管理API"""
    print("🧪 测试连接管理API...")
    
    # 1. 获取token
    print("\n1. 获取认证token...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/token")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "1":
                print("✅ Token获取成功")
                token = data["data"]["token"]
            else:
                print(f"❌ Token获取失败: {data.get('msg')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False
    
    # 2. 测试连接状态
    print("\n2. 测试连接状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/connection/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 连接状态: {data}")
        else:
            print(f"❌ 状态查询失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 状态查询异常: {e}")
    
    # 3. 测试连接命令
    print("\n3. 测试连接命令...")
    try:
        response = requests.post(f"{BASE_URL}/api/connection/connect")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "1":
                print("✅ 连接命令发送成功")
            else:
                print(f"❌ 连接失败: {data.get('msg')}")
        else:
            print(f"❌ 连接请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接异常: {e}")
    
    # 4. 等待一下再测试其他功能
    await asyncio.sleep(2)
    
    # 5. 测试控制命令
    print("\n4. 测试控制命令...")
    try:
        command = {
            "type": "control",
            "target": "aircraft",
            "channel": 5,  # 云台俯仰
            "value": 1600
        }
        response = requests.post(
            f"{BASE_URL}/api/connection/send_command",
            json=command
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "1":
                print("✅ 控制命令发送成功")
            else:
                print(f"❌ 控制命令失败: {data.get('msg')}")
        else:
            print(f"❌ 控制请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 控制异常: {e}")
    
    # 6. 测试消息历史
    print("\n5. 测试消息历史...")
    try:
        response = requests.get(f"{BASE_URL}/api/connection/messages")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "1":
                messages = data["data"]["messages"]
                print(f"✅ 消息历史获取成功，共 {len(messages)} 条消息")
                for i, msg in enumerate(messages[-3:]):  # 显示最后3条
                    print(f"   {i+1}. {msg.get('timestamp', '')}: {msg.get('message', {}).get('type', 'unknown')}")
            else:
                print(f"❌ 消息历史失败: {data.get('msg')}")
        else:
            print(f"❌ 消息历史请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 消息历史异常: {e}")
    
    # 7. 测试断开连接
    print("\n6. 测试断开连接...")
    try:
        response = requests.post(f"{BASE_URL}/api/connection/disconnect")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "1":
                print("✅ 断开连接成功")
            else:
                print(f"❌ 断开连接失败: {data.get('msg')}")
        else:
            print(f"❌ 断开请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 断开异常: {e}")
    
    print("\n🎉 测试完成！")
    return True

def test_health_check():
    """测试健康检查"""
    print("🏥 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试新的通信架构...")
    print("=" * 50)
    
    # 健康检查
    if not test_health_check():
        print("❌ 后端服务未启动，请先运行: python backend/main.py")
        return
    
    # 连接API测试
    await test_connection_api()

if __name__ == "__main__":
    asyncio.run(main())
