融瓴智能制造官方 API 示例程序，包含：
1.身份认证：获取 Token，用于所有接口鉴权。
2.云台抓拍：获取无人机实时图像。
3.实时控制与遥测：
    o控制无人机：起飞、降落、前进、后退、云台控制等
    o控制无人车：前进、后退、左转、右转
    o实时接收电量、电压、GPS、速度等数据
    o支持双设备并行控制

示例代码开发语言：Python 3.8+
环境依赖安装
bash
运行
pip install requests
pip install websockets
pip install loguru