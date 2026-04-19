#!/usr/bin/env python3
"""
无人机自动穿越拱门启动脚本
"""

import os
import sys
import asyncio
from pathlib import Path

def check_requirements():
    """检查运行环境和依赖"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3.7, 0):
        print("❌ 需要Python 3.7+")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查必要的依赖
    required_modules = ['websockets', 'requests', 'asyncio']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} 已安装")
        except ImportError:
            missing.append(module)
            print(f"❌ {module} 未安装")
    
    if missing:
        print(f"\n请安装缺失的依赖:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    # 检查路径规划结果文件
    path_file = Path("output/drone_flight_path.json")
    if not path_file.exists():
        print(f"❌ 未找到路径规划结果: {path_file}")
        print("请先运行: python path_planning.py")
        return False
    
    print(f"✅ 路径规划文件: {path_file}")
    
    return True

def show_mission_info():
    """显示任务信息"""
    print("\n" + "=" * 60)
    print("🚁 无人机自动穿越拱门系统")
    print("=" * 60)
    print("📋 任务说明:")
    print("  1. 自动起飞（使用无人机默认起飞高度）")
    print("  2. 记录起飞高度并保持该高度飞行")
    print("  3. 按顺序穿越拱门1-8的中心点")
    print("  4. 飞到终点位置")
    print("  5. 自动降落")
    print()
    print("⚠️  注意事项:")
    print("  • 确保无人机已连接且状态正常")
    print("  • 确保飞行区域安全无障碍")
    print("  • 随时准备手动接管控制")
    print("  • 按Ctrl+C可中断自动飞行")
    print("=" * 60)

async def start_auto_flight():
    """启动自动飞行"""
    try:
        # 导入自动飞行模块
        from auto_flight import main as flight_main
        
        print("\n🚀 启动自动飞行任务...")
        await flight_main()
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断飞行任务")
    except ImportError as e:
        print(f"❌ 无法导入飞行模块: {e}")
    except Exception as e:
        print(f"❌ 飞行任务异常: {e}")

def main():
    """主函数"""
    print("🚁 无人机自动穿越拱门系统启动器")
    print("-" * 40)
    
    # 检查环境
    if not check_requirements():
        print("\n❌ 环境检查失败，请解决问题后重试")
        return
    
    # 显示任务信息
    show_mission_info()
    
    # 用户确认
    try:
        response = input("\n确认开始自动飞行任务吗？(y/N): ").strip().lower()
        if response != 'y':
            print("❌ 任务已取消")
            return
    except KeyboardInterrupt:
        print("\n❌ 任务已取消")
        return
    
    # 启动飞行任务
    try:
        asyncio.run(start_auto_flight())
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
