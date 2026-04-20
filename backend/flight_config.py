"""
自动飞行配置文件
"""

import requests
import json

# ============ 服务器配置 ============
SERVER_CONFIG = {
    "HOST": "fcs.botzooo.com",
    "PORT": 30080,
    "WS_HOST": "fcs.botzooo.com", 
    "WS_PORT": 30081,
    "USERNAME": "fcs002",
    "PASSWORD": "wa729461"
}

# ============ 飞行参数 ============
FLIGHT_PARAMS = {
    "POSITION_TOLERANCE": 2.0,      # 位置容差（米）
    "ALTITUDE_TOLERANCE": 1.0,      # 高度容差（米）
    "USE_TAKEOFF_ALTITUDE": True,   # 使用起飞后的高度，不强制指定
    "MAX_SPEED": 5.0,               # 最大飞行速度
    "CONTROL_FREQUENCY": 10,        # 控制频率 (Hz)
    "WAYPOINT_TIMEOUT": 60,         # 单个航点超时时间（秒）
}

# ============ 坐标转换参数 ============
# 格栅坐标转GPS坐标的参数
COORDINATE_CONVERSION = {
    # 实际GPS坐标转换（需要实地标定）
    # 格栅(480x1200) 对应实际场地(17m x 44m)
    
    # 方式1：使用相对坐标（推荐用于模拟测试）
    "USE_RELATIVE_COORDINATES": True,
    "RELATIVE_SCALE": 0.001,  # 相对比例，便于模拟
    
    # 方式2：真实GPS坐标（需要实地测量）
    "USE_REAL_GPS": False,
    "BASE_GPS_LAT": 39.9042,    # 实际场地基准纬度（示例：北京）
    "BASE_GPS_LON": 116.4074,   # 实际场地基准经度（示例：北京）
    "METERS_TO_DEGREES_LAT": 1/111320.0,  # 纬度：1米≈9e-6度
    "METERS_TO_DEGREES_LON": 1/85390.0,   # 经度：1米≈1.17e-5度（北纬40度）
    
    # 格栅到米的转换（基于实际场地尺寸）
    "GRID_TO_METERS_X": 17.0 / 425.0,     # X方向：17米/425格
    "GRID_TO_METERS_Y": 44.0 / 1129.0,    # Y方向：44米/1129格
}

def get_auth_token():
    """获取认证Token"""
    try:
        url = f"http://{SERVER_CONFIG['HOST']}:{SERVER_CONFIG['PORT']}/auth/token"
        
        payload = {
            "username": SERVER_CONFIG["USERNAME"],
            "password": SERVER_CONFIG["PASSWORD"]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        print(f"正在获取Token: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "1":
                token = data["data"]["token"]
                print(f"✅ Token获取成功: {token[:20]}...")
                return token
            else:
                print(f"❌ Token获取失败: {data.get('msg')}")
                return None
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 获取Token异常: {e}")
        return None

def convert_grid_to_gps(grid_coords, altitude=None):
    """
    将格栅坐标转换为GPS坐标
    
    Args:
        grid_coords: [x, y] 格栅坐标
        altitude: 高度，如果不指定则使用None（保持起飞高度）
    
    Returns:
        [lat, lon, alt] GPS坐标和高度（altitude为None表示保持当前高度）
    """
    # 先转换为米坐标
    x_meters = grid_coords[0] * COORDINATE_CONVERSION["GRID_TO_METERS_X"]
    y_meters = grid_coords[1] * COORDINATE_CONVERSION["GRID_TO_METERS_Y"]
    
    if COORDINATE_CONVERSION.get("USE_RELATIVE_COORDINATES", True):
        # 模式1：相对坐标（用于测试和模拟）
        lat = y_meters * COORDINATE_CONVERSION["RELATIVE_SCALE"]
        lon = x_meters * COORDINATE_CONVERSION["RELATIVE_SCALE"]
        
    elif COORDINATE_CONVERSION.get("USE_REAL_GPS", False):
        # 模式2：真实GPS坐标（需要实地标定）
        lat = (COORDINATE_CONVERSION["BASE_GPS_LAT"] + 
               y_meters * COORDINATE_CONVERSION["METERS_TO_DEGREES_LAT"])
        lon = (COORDINATE_CONVERSION["BASE_GPS_LON"] + 
               x_meters * COORDINATE_CONVERSION["METERS_TO_DEGREES_LON"])
    else:
        # 默认：简化相对坐标
        lat = y_meters * 0.0001
        lon = x_meters * 0.0001
    
    return [lat, lon, altitude]

def load_and_convert_waypoints(json_path="output/drone_flight_path.json"):
    """
    加载并转换航点数据
    
    Args:
        json_path: 路径规划JSON文件路径
    
    Returns:
        List of GPS waypoints: [[lat1, lon1, alt1], [lat2, lon2, alt2], ...]
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            path_data = json.load(f)
        
        grid_waypoints = path_data.get('waypoints', [])
        gps_waypoints = []
        
        print(f"📍 转换 {len(grid_waypoints)} 个格栅航点到GPS坐标:")
        
        for i, grid_wp in enumerate(grid_waypoints):
            gps_wp = convert_grid_to_gps(grid_wp)  # altitude=None，保持起飞高度
            gps_waypoints.append(gps_wp)
            
            alt_text = "保持起飞高度" if gps_wp[2] is None else f"{gps_wp[2]}m"
            
            if i == 0:
                print(f"  起点: 格栅({grid_wp[0]}, {grid_wp[1]}) → GPS({gps_wp[0]:.6f}, {gps_wp[1]:.6f}, {alt_text})")
            elif i == len(grid_waypoints) - 1:
                print(f"  终点: 格栅({grid_wp[0]}, {grid_wp[1]}) → GPS({gps_wp[0]:.6f}, {gps_wp[1]:.6f}, {alt_text})")
            elif i <= 8:  # 拱门1-8
                print(f"  拱门{i}: 格栅({grid_wp[0]}, {grid_wp[1]}) → GPS({gps_wp[0]:.6f}, {gps_wp[1]:.6f}, {alt_text})")
        
        print(f"✅ 航点转换完成，总计 {len(gps_waypoints)} 个GPS航点")
        return gps_waypoints
        
    except Exception as e:
        print(f"❌ 航点转换失败: {e}")
        return []

if __name__ == "__main__":
    print("🔧 自动飞行配置测试")
    print("=" * 40)
    
    # 测试Token获取
    token = get_auth_token()
    if token:
        print("✅ Token测试通过")
    else:
        print("❌ Token测试失败")
    
    print()
    
    # 测试航点转换
    waypoints = load_and_convert_waypoints()
    if waypoints:
        print("✅ 航点转换测试通过")
    else:
        print("❌ 航点转换测试失败")
