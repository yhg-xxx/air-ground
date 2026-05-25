# 自动降落功能使用说明

## 功能概述

本项目实现了基于Aruco码识别的无人机自动降落功能。通过无人机摄像头拍摄地面标记，后端使用OpenCV和Aruco算法识别标记位置，计算无人机与标记的相对位置，然后返回控制指令调整无人机位置，最终实现精确降落。

## 项目结构

```
air_mock_test/
├── airtest_backend/
│   ├── auto_landing.py          # 自动降落控制模块（Aruco识别算法）
│   ├── mock_server.py           # Mock服务器（包含自动降落API）
│   └── requirements.txt          # Python依赖包
└── airtest_frontend/
    └── src/
        └── components/
            ├── ApiTest.vue       # 前端控制界面（包含自动降落按钮）
            └── ThreeScene.vue    # 3D场景模拟（包含摄像头捕获功能）
```

## 安装依赖

### 后端依赖

在 `airtest_backend` 目录下安装Python依赖：

```bash
cd airtest_backend
pip install -r requirements.txt
```

依赖包包括：
- opencv-python >= 4.8.0
- opencv-contrib-python >= 4.8.0
- numpy >= 1.24.0
- Pillow >= 10.0.0
- websockets >= 12.0

### 前端依赖

前端使用Vue 3，在 `airtest_frontend` 目录下：

```bash
cd airtest_frontend
npm install
```

## 启动服务

### 1. 启动后端服务器

```bash
cd airtest_backend
python mock_server.py
```

服务器将启动：
- HTTP服务器：http://localhost:30080
- WebSocket服务器：ws://localhost:30081

### 2. 启动前端服务

```bash
cd airtest_frontend
npm run dev
```

前端将在默认端口运行（通常是 http://localhost:5173）

## 使用自动降落功能

### 步骤1：身份认证

1. 打开前端页面
2. 点击"获取 Token"按钮
3. 使用用户名：`fcs002`，密码：`fcs002fcs002` 进行认证

### 步骤2：连接WebSocket

1. 点击"连接 WebSocket"按钮
2. 确认连接成功消息

### 步骤3：起飞无人机

1. 点击"起飞"按钮
2. 无人机将升起到10米高度

### 步骤4：启动自动降落

1. 点击"开始自动降落"按钮（橙色按钮）
2. 系统将自动执行以下循环：
   - 从3D场景捕获无人机摄像头视角的图像
   - 将图像发送到后端API进行处理
   - 后端使用Aruco算法识别地面标记
   - 计算无人机与标记的相对位置（X、Y偏移和高度）
   - 根据位置偏差返回控制指令
   - 前端通过WebSocket发送控制指令调整无人机位置
3. 每隔2秒重复一次上述步骤
4. 当无人机高度降至目标高度（0.5米）时，自动执行降落
5. 降落完成后自动停止

### 步骤5：停止降落（可选）

如需手动停止自动降落，点击"停止降落"按钮（红色按钮）

## 自动降落逻辑

### ArUco识别参数

- 标记尺寸：0.1米（10厘米）
- 坐标系：中心坐标系
- 相机分辨率：1280x720
- ArUco字典：DICT_6X6_250

### 降落控制策略

1. **高度判断**：
   - 目标高度：0.5米
   - 降落阈值：0.1米
   - 当高度 ≤ 0.6米时，执行降落

2. **水平对齐**：
   - 水平阈值：0.2米
   - 当X和Y偏移都在 ±0.2米范围内时，降低高度

3. **位置调整**：
   - X偏移 > 0.2米：向右移动
   - X偏移 < -0.2米：向左移动
   - Y偏移 > 0.2米：向后移动
   - Y偏移 < -0.2米：向前移动

## API接口

### POST /api/landing/process

处理降落图像并返回控制指令

**请求头**：
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**：
```json
{
  "image": "base64_encoded_image_data"
}
```

**响应**：
```json
{
  "code": "1",
  "msg": "success",
  "data": {
    "success": true,
    "detection": {
      "marker_id": 2,
      "x": 0.15,
      "y": -0.08,
      "height": 2.5,
      "distance": 2.52
    },
    "command": {
      "action": "adjust",
      "message": "调整水平位置",
      "commands": [
        {
          "target": "aircraft",
          "channel": 3,
          "value": 2000,
          "message": "向右调整"
        }
      ]
    }
  }
}
```

## 控制指令说明

通过WebSocket发送控制指令：

```json
{
  "type": "control",
  "target": "aircraft",
  "channel": 2,
  "value": 1000
}
```

**通道说明**：
- channel 1: 左转/右转
- channel 2: 上升/下降（1000=下降，2000=上升）
- channel 3: 左移/右移（1000=左移，2000=右移）
- channel 4: 前进/后退（1000=后退，2000=前进）
- channel 7: 起飞
- channel 8: 降落

## 注意事项

1. **Aruco标记**：确保地面有清晰的Aruco标记（DICT_6X6_250格式）
2. **光照条件**：良好的光照条件有助于提高识别准确率
3. **摄像头视角**：确保无人机摄像头能够清晰看到地面标记
4. **网络延迟**：自动降落依赖网络通信，确保网络稳定
5. **安全距离**：在实际使用中，建议设置安全距离和紧急停止机制

## 故障排除

### 问题：未检测到Aruco标记

**可能原因**：
- 标记不在摄像头视野内
- 光照不足
- 标记模糊或角度过大
- 标记尺寸与配置不匹配

**解决方法**：
- 调整无人机位置使标记进入视野
- 改善光照条件
- 降低飞行高度
- 检查标记配置参数

### 问题：自动降落停止

**可能原因**：
- WebSocket连接断开
- 图像捕获失败
- 后端API错误

**解决方法**：
- 检查WebSocket连接状态
- 查看浏览器控制台错误信息
- 检查后端服务器日志

## 开发说明

### 修改降落参数

编辑 `auto_landing.py` 文件中的参数：

```python
self.target_height = 0.5  # 目标降落高度
self.landing_threshold = 0.1  # 降落判定阈值
self.horizontal_threshold = 0.2  # 水平对齐阈值
```

### 修改Aruco标记参数

```python
self.marker_length = 0.1  # 标记实际边长
self.coordinate_system = 1  # 坐标系类型
```

## 许可证

本项目仅用于学习和测试目的。
