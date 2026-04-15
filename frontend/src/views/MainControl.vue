<template>
  <div class="main-control">
    <!-- 页面标题 -->
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <el-icon><Monitor /></el-icon>
          <span>空地协同控制中心</span>
        </div>
      </template>
      <div class="connection-status">
        <el-tag :type="wsConnected ? 'success' : 'danger'" effect="dark">
          {{ wsConnected ? 'WebSocket已连接' : 'WebSocket未连接' }}
        </el-tag>
        <el-button type="primary" size="small" @click="connectWebSocket" :disabled="wsConnected">
          连接WebSocket
        </el-button>
      </div>
    </el-card>

    <!-- 主内容区 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧：设备状态和遥测数据 -->
      <el-col :span="6">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>设备状态</span>
            </div>
          </template>

          <!-- 无人机状态 -->
          <el-collapse v-model="activeStatusTab">
            <el-collapse-item title="无人机状态" name="aircraft">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="电量">
                  {{ telemetryData.aircraft.power }}%
                </el-descriptions-item>
                <el-descriptions-item label="电压">
                  {{ telemetryData.aircraft.voltage }}V
                </el-descriptions-item>
                <el-descriptions-item label="GPS">
                  {{ formatGps(telemetryData.aircraft.gps) }}
                </el-descriptions-item>
                <el-descriptions-item label="速度">
                  {{ telemetryData.aircraft.speed }}m/s
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>

            <!-- 无人车状态 -->
            <el-collapse-item title="无人车状态" name="vehicle">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="电量">
                  {{ telemetryData.vehicle.power }}%
                </el-descriptions-item>
                <el-descriptions-item label="电压">
                  {{ telemetryData.vehicle.voltage }}V
                </el-descriptions-item>
                <el-descriptions-item label="GPS">
                  {{ formatGps(telemetryData.vehicle.gps) }}
                </el-descriptions-item>
                <el-descriptions-item label="速度">
                  {{ telemetryData.vehicle.speed }}m/s
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>

      <!-- 中间：控制界面 -->
      <el-col :span="12">
        <el-card class="control-card">
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>设备控制</span>
            </div>
          </template>

          <!-- 控制选项卡 -->
          <el-tabs v-model="activeControlTab">
            <!-- 无人车控制 -->
            <el-tab-pane label="无人车控制" name="vehicle">
              <div class="control-panel joystick-mode">
                <div class="joystick-wrapper">
                  <VirtualJoystick
                    :size="200"
                    label="移动控制"
                    topLabel="前进"
                    bottomLabel="后退"
                    leftLabel="左转"
                    rightLabel="右转"
                    :showSpeedLimit="true"
                    @change="handleVehicleJoystick"
                  />
                </div>
                <div class="control-tips">
                  <p><strong>操作说明：</strong></p>
                  <p>• 上下：前进/后退</p>
                  <p>• 左右：左转/右转</p>
                  <p>• 松手自动归中停止</p>
                </div>
              </div>
            </el-tab-pane>

            <!-- 无人机控制 -->
            <el-tab-pane label="无人机控制" name="aircraft">
              <div class="control-panel joystick-mode">
                <div class="dual-joystick-container">
                  <!-- 左摇杆：上升下降 + 左转右转 -->
                  <div class="joystick-wrapper">
                    <VirtualJoystick
                      :size="180"
                      label="姿态控制"
                      topLabel="上升"
                      bottomLabel="下降"
                      leftLabel="左转"
                      rightLabel="右转"
                      :showSpeedLimit="true"
                      @change="handleAircraftLeftJoystick"
                    />
                  </div>
                  
                  <!-- 右摇杆：前进后退 + 左移右移 -->
                  <div class="joystick-wrapper">
                    <VirtualJoystick
                      :size="180"
                      label="移动控制"
                      topLabel="前进"
                      bottomLabel="后退"
                      leftLabel="左移"
                      rightLabel="右移"
                      :showSpeedLimit="true"
                      @change="handleAircraftRightJoystick"
                    />
                  </div>
                </div>
                
                <div class="control-tips small">
                  <p><strong>左摇杆：</strong>上升/下降 + 左转/右转</p>
                  <p><strong>右摇杆：</strong>前进/后退 + 左移/右移</p>
                  <p><strong>WASD键盘：</strong>可替代左摇杆进行姿态控制</p>
                </div>

                <!-- 键盘控制 -->
                <div class="keyboard-control-section">
                  <h4>
                    姿态键盘控制
                    <el-switch
                      v-model="keyboardControlEnabled"
                      @change="toggleKeyboardControl"
                      style="margin-left: 10px;"
                    />
                  </h4>
                  
                  <div v-if="keyboardControlEnabled" class="keyboard-tips">
                    <div class="wasd-layout">
                      <div class="wasd-row">
                        <div class="wasd-key" :class="{ 'active': pressedKeys.has('W') }">W<span>上升</span></div>
                      </div>
                      <div class="wasd-row">
                        <div class="wasd-key" :class="{ 'active': pressedKeys.has('A') }">A<span>左转</span></div>
                        <div class="wasd-key" :class="{ 'active': pressedKeys.has('S') }">S<span>下降</span></div>
                        <div class="wasd-key" :class="{ 'active': pressedKeys.has('D') }">D<span>右转</span></div>
                      </div>
                    </div>
                    <p class="keyboard-status">
                      状态: <span :class="keyboardControlEnabled ? 'status-enabled' : 'status-disabled'">
                        {{ keyboardControlEnabled ? '已启用' : '已禁用' }}
                      </span>
                    </p>
                  </div>
                </div>

                <h4>云台控制</h4>
                
                <!-- 云台灵敏度调节 -->
                <div class="gimbal-sensitivity-section">
                  <div class="sensitivity-label">
                    <span>灵敏度: {{ Math.round(gimbalSensitivity * 100) }}%</span>
                  </div>
                  <el-slider
                    v-model="gimbalSensitivity"
                    :min="0.1"
                    :max="1.0"
                    :step="0.1"
                    :show-tooltip="false"
                    style="margin: 10px 0;"
                  />
                  <div class="sensitivity-tips">
                    <span>低</span>
                    <span>高</span>
                  </div>
                </div>
                
                <div class="gimbal-joystick-wrapper">
                  <VirtualJoystick
                    :size="120"
                    topLabel="上仰"
                    bottomLabel="下俯"
                    leftLabel="左滚"
                    rightLabel="右滚"
                    :autoCenter="false"
                    @change="handleGimbalJoystick"
                  />
                </div>

                <div class="drone-buttons">
                  <el-button type="primary" @click="sendDroneCommand('takeoff')">
                    起飞
                  </el-button>
                  <el-button type="warning" @click="sendDroneCommand('land')">
                    降落
                  </el-button>
                  <el-button type="danger" @click="sendDroneCommand('back')">
                    返航
                  </el-button>
                  <el-button type="info" @click="sendDroneCommand('gimbalReset')">
                    云台复位
                  </el-button>
                </div>

                <!-- 降落测试按钮 -->
                <div class="landing-buttons">
                  <h4>降落测试</h4>
                  <el-button type="success" @click="startLandingTest">
                    开始降落测试
                  </el-button>
                  <el-button type="info" @click="getLandingStatusTest">
                    获取降落状态
                  </el-button>
                  <el-button type="danger" @click="cancelLandingTest">
                    取消降落
                  </el-button>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <!-- 右侧：图像显示和抓拍功能 -->
      <el-col :span="6">
        <el-card class="image-card">
          <template #header>
            <div class="card-header">
              <el-icon><Picture /></el-icon>
              <span>图像抓拍</span>
            </div>
          </template>

          <div class="image-container">
            <img v-if="capturedImage" :src="capturedImage" alt="抓拍图像" class="captured-image" />
            <div v-else class="image-placeholder">
              <el-icon class="placeholder-icon"><Camera /></el-icon>
              <span>未抓拍图像</span>
            </div>
          </div>

          <div class="capture-controls">
            <el-button type="primary" @click="captureImage" :loading="isCapturing">
              {{ isCapturing ? '抓拍中...' : '抓拍图像' }}
            </el-button>
            <el-button @click="clearImage" :disabled="!capturedImage">
              清除图像
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {onMounted, onUnmounted, ref} from 'vue'
import {ElMessage} from 'element-plus'
import {CONTROL_CHANNELS, officialServerAPI, WebSocketManager} from '../services/officialAPI'
import {Camera, DataAnalysis, Monitor, Operation} from "@element-plus/icons-vue";
import VirtualJoystick from '../components/VirtualJoystick.vue'

// WebSocket管理
const wsManager = new WebSocketManager()
const wsConnected = ref(false)

// 遥测数据
const telemetryData = ref({
  aircraft: { power: 0, voltage: 0, gps: '', speed: 0 },
  vehicle: { power: 0, voltage: 0, gps: '', speed: 0 }
})

// 控制值
const vehicleThrottle = ref(1500)  // 油门（前进后退）：前进=2000, 中=1500, 后退=1000
const vehicleSteering = ref(1500)  // 转向：左转=2000, 中=1500, 右转=1000

const aircraftDirection = ref(1500) // 左转右转
const aircraftAltitude = ref(1500) // 上升下降
const aircraftMovement = ref(1500) // 左移右移
const aircraftThrottle = ref(1500) // 前进后退
const aircraftGimbalPitch = ref(1500) // 云台俯仰
const aircraftGimbalRoll = ref(1500) // 云台横滚

// 界面状态
const activeStatusTab = ref(['aircraft'])
const activeControlTab = ref('vehicle')
const capturedImage = ref(null)
const isCapturing = ref(false)

// 键盘控制状态
const keyboardControlEnabled = ref(true)
const pressedKeys = ref(new Set())
const keyboardControlInterval = ref(null)

// 云台控制灵敏度 (0.1-1.0，默认0.5)
const gimbalSensitivity = ref(0.5)

// GPS格式化函数
const formatGps = (gps) => {
  if (!gps) return '无数据'
  if (Array.isArray(gps) && gps.length >= 2) {
    return `[ ${gps[0].toFixed(6)}, ${gps[1].toFixed(6)} ]`
  }
  if (typeof gps === 'string' && gps.trim()) return gps
  return '无数据'
}

// 连接WebSocket
const connectWebSocket = async () => {
  try {
    const token = localStorage.getItem('official_token')
    if (!token) {
      ElMessage.error('未获取到认证token，请重新认证')
      return
    }
    
    if (wsConnected.value) {
      ElMessage.info('WebSocket已经连接')
      return
    }
    
    await wsManager.connect(token)
    // wsConnected.value会在WebSocket事件中自动更新
  } catch (error) {
    ElMessage.error('WebSocket连接失败：' + error.message)
  }
}

// 处理无人车控制
const handleVehicleControl = () => {
  if (!wsConnected.value) {
    ElMessage.warning('WebSocket未连接，无法发送控制指令')
    return
  }
  
  // 通道1=转向，通道2=油门（前进后退）
  wsManager.sendControl('vehicle', CONTROL_CHANNELS.VEHICLE_STEERING, vehicleSteering.value)
  wsManager.sendControl('vehicle', CONTROL_CHANNELS.VEHICLE_THROTTLE, vehicleThrottle.value)
}

// 处理无人机控制
const handleAircraftControl = () => {
  if (!wsConnected.value) {
    ElMessage.warning('WebSocket未连接，无法发送控制指令')
    return
  }
  
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_DIRECTION, aircraftDirection.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_ALTITUDE, aircraftAltitude.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_MOVEMENT, aircraftMovement.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_THROTTLE, aircraftThrottle.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_PITCH, aircraftGimbalPitch.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_ROLL, aircraftGimbalRoll.value)
}

// 处理无人车摇杆控制
const handleVehicleJoystick = (data) => {
  if (!wsConnected.value) return
  
  // 官方定义：通道1转向（左转=1000, 右转=2000）通道2油门（前进=1700, 后退=1300）
  // X轴控制转向：左=1000, 右=2000（直接使用）
  // Y轴控制油门：需要映射到1300-1700范围
  vehicleSteering.value = data.xValue
  // 将1000-2000映射到1300-1700: (value - 1000) / 1000 * 400 + 1300
  vehicleThrottle.value = Math.round((data.yValue - 1000) / 1000 * 400 + 1300)
  
  wsManager.sendControl('vehicle', CONTROL_CHANNELS.VEHICLE_STEERING, vehicleSteering.value)
  wsManager.sendControl('vehicle', CONTROL_CHANNELS.VEHICLE_THROTTLE, vehicleThrottle.value)
}

// 处理无人机左摇杆（上升下降 + 左转右转）
const handleAircraftLeftJoystick = (data) => {
  if (!wsConnected.value) return
  
  // X轴控制左转右转
  // Y轴控制上升下降
  aircraftDirection.value = data.xValue
  aircraftAltitude.value = data.yValue
  
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_DIRECTION, aircraftDirection.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_ALTITUDE, aircraftAltitude.value)
}

// 处理无人机右摇杆（前进后退 + 左移右移）
const handleAircraftRightJoystick = (data) => {
  if (!wsConnected.value) return
  
  // X轴控制左移右移
  // Y轴控制前进后退
  aircraftMovement.value = data.xValue
  aircraftThrottle.value = data.yValue
  
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_MOVEMENT, aircraftMovement.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_THROTTLE, aircraftThrottle.value)
}

// 处理云台摇杆控制
const handleGimbalJoystick = (data) => {
  if (!wsConnected.value) return
  
  // 应用灵敏度调整
  // 计算相对于中心位置(1500)的偏移量，然后应用灵敏度
  const centerValue = 1500
  const rollOffset = (data.xValue - centerValue) * gimbalSensitivity.value
  const pitchOffset = (data.yValue - centerValue) * gimbalSensitivity.value
  
  // 计算最终控制值，确保在有效范围内
  aircraftGimbalRoll.value = Math.max(1000, Math.min(2000, centerValue + rollOffset))
  aircraftGimbalPitch.value = Math.max(1000, Math.min(2000, centerValue + pitchOffset))
  
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_PITCH, aircraftGimbalPitch.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_ROLL, aircraftGimbalRoll.value)
}

// 键盘事件处理
const handleKeyDown = (event) => {
  if (!keyboardControlEnabled.value || !wsConnected.value) return
  
  const key = event.key.toUpperCase()
  if (['W', 'A', 'S', 'D'].includes(key)) {
    event.preventDefault()
    pressedKeys.value.add(key)
    updateAircraftControlFromKeyboard()
  }
}

const handleKeyUp = (event) => {
  if (!keyboardControlEnabled.value) return
  
  const key = event.key.toUpperCase()
  if (['W', 'A', 'S', 'D'].includes(key)) {
    event.preventDefault()
    pressedKeys.value.delete(key)
    updateAircraftControlFromKeyboard()
  }
}

// 根据键盘输入更新无人机姿态控制
const updateAircraftControlFromKeyboard = () => {
  if (!wsConnected.value) return
  
  // 重置姿态控制值到中位
  let newAltitude = 1500   // 上升下降
  let newDirection = 1500  // 左转右转
  
  // 根据按键状态设置姿态控制值
  if (pressedKeys.value.has('W')) {
    newAltitude = 2000  // 上升
  } else if (pressedKeys.value.has('S')) {
    newAltitude = 1000  // 下降
  }
  
  if (pressedKeys.value.has('A')) {
    newDirection = 1000  // 左转
  } else if (pressedKeys.value.has('D')) {
    newDirection = 2000  // 右转
  }
  
  // 更新姿态控制值并发送指令
  aircraftAltitude.value = newAltitude
  aircraftDirection.value = newDirection
  
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_ALTITUDE, aircraftAltitude.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_DIRECTION, aircraftDirection.value)
}

// 切换键盘控制模式
const toggleKeyboardControl = () => {
  keyboardControlEnabled.value = !keyboardControlEnabled.value
  if (!keyboardControlEnabled.value) {
    // 关闭键盘控制时，重置按键状态和姿态控制
    pressedKeys.value.clear()
    aircraftAltitude.value = 1500   // 重置上升下降
    aircraftDirection.value = 1500  // 重置左转右转
    if (wsConnected.value) {
      wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_ALTITUDE, aircraftAltitude.value)
      wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_DIRECTION, aircraftDirection.value)
    }
  }
  ElMessage.info(`键盘姿态控制${keyboardControlEnabled.value ? '已开启' : '已关闭'}`)
}

// 发送无人机命令
const sendDroneCommand = (command) => {
  if (!wsConnected.value) {
    ElMessage.warning('WebSocket未连接，无法发送控制指令')
    return
  }
  
  switch (command) {
    case 'takeoff':
      wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_TAKEOFF, 2000)
      setTimeout(() => {
        wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_TAKEOFF, 1500)
      }, 500)
      break
    case 'land':
      wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_LAND, 2000)
      setTimeout(() => {
        wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_LAND, 1500)
      }, 500)
      break
    case 'back':
      wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_BACK, 2000)
      setTimeout(() => {
        wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_BACK, 1500)
      }, 500)
      break
    case 'gimbalReset':
      wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_RESET, 2000)
      setTimeout(() => {
        wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_RESET, 1500)
      }, 500)
      break
  }
}

// 抓拍图像
const captureImage = async () => {
  try {
    isCapturing.value = true
    const token = localStorage.getItem('official_token')
    if (!token) {
      ElMessage.error('未获取到认证token，请重新认证')
      return
    }

    capturedImage.value = await officialServerAPI.captureImage(token)
    ElMessage.success('图像抓拍成功')
  } catch (error) {
    ElMessage.error('图像抓拍失败：' + error.message)
  } finally {
    isCapturing.value = false
  }
}

// 清除图像
const clearImage = () => {
  if (capturedImage.value) {
    URL.revokeObjectURL(capturedImage.value)
    capturedImage.value = null
  }
}

// 开始降落测试
const startLandingTest = async () => {
  try {
    const result = await officialServerAPI.startLanding(0)
    if (result.status === 'success') {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 获取降落状态
const getLandingStatusTest = async () => {
  try {
    const result = await officialServerAPI.getLandingStatus()
    ElMessage.info(`降落状态: ${result.status}, 错误信息: ${result.error_message || '无'}`)
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 取消降落
const cancelLandingTest = async () => {
  try {
    const result = await officialServerAPI.cancelLanding()
    if (result.status === 'success') {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 生命周期钩子
onMounted(() => {
  // 注册WebSocket事件
  wsManager.on('connected', () => {
    wsConnected.value = true
  })
  
  wsManager.on('disconnected', () => {
    wsConnected.value = false
  })
  
  wsManager.on('aircraft_telemetry', (data) => {
    telemetryData.value.aircraft = data
  })
  
  wsManager.on('vehicle_telemetry', (data) => {
    telemetryData.value.vehicle = data
  })
  
  // 添加键盘事件监听器
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('keyup', handleKeyUp)
  
  // 自动连接WebSocket
  connectWebSocket()
})

onUnmounted(() => {
  // 断开WebSocket连接
  wsManager.disconnect()
  // 清理图像资源
  clearImage()
  // 清理键盘事件监听器
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('keyup', handleKeyUp)
  // 清理定时器
  if (keyboardControlInterval.value) {
    clearInterval(keyboardControlInterval.value)
  }
})
</script>

<style scoped>
.main-control {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.main-content {
  margin-top: 20px;
}

.status-card,
.control-card,
.image-card {
  height: 100%;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
  margin-top: 5px;
  margin-bottom: 20px;
}

.control-panel h4 {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 500;
}

.gimbal-controls {
  margin-bottom: 20px;
}

.gimbal-item {
  margin-bottom: 15px;
}

.gimbal-item span {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  font-weight: 500;
}

.joystick-mode {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.joystick-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.dual-joystick-container {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.gimbal-joystick-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.control-tips {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: #606266;
  width: 100%;
  max-width: 300px;
}

.control-tips.small {
  font-size: 12px;
  padding: 8px 12px;
}

.control-tips p {
  margin: 4px 0;
}

.control-tips strong {
  color: #303133;
}

.drone-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.landing-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.landing-buttons h4 {
  width: 100%;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 500;
}

.image-container {
  height: 300px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  overflow: hidden;
}

.captured-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-placeholder {
  text-align: center;
  color: #909399;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.capture-controls {
  display: flex;
  gap: 10px;
}

.keyboard-control-section {
  margin: 20px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.keyboard-control-section h4 {
  margin: 0 0 15px 0;
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
}

.keyboard-tips {
  margin-top: 10px;
}

.wasd-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
}

.wasd-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.wasd-key {
  width: 50px;
  height: 50px;
  border: 2px solid #d4dae4;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  font-weight: bold;
  font-size: 14px;
  color: #606266;
  transition: all 0.2s ease;
  position: relative;
}

.wasd-key span {
  font-size: 10px;
  font-weight: normal;
  margin-top: 2px;
  color: #909399;
}

.wasd-key.active {
  background: #409eff;
  color: white;
  border-color: #337ecc;
  transform: scale(0.95);
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.wasd-key.active span {
  color: rgba(255, 255, 255, 0.8);
}

.keyboard-status {
  margin: 10px 0 0 0;
  font-size: 12px;
  color: #606266;
  text-align: center;
}

.status-enabled {
  color: #67c23a;
  font-weight: 500;
}

.status-disabled {
  color: #f56c6c;
  font-weight: 500;
}

/* 云台灵敏度调节样式 */
.gimbal-sensitivity-section {
  margin: 15px 0;
  padding: 12px;
  background: #fafbfc;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.sensitivity-label {
  text-align: center;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.sensitivity-tips {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

/* 响应式调整 */
@media screen and (max-width: 1200px) {
  .el-col {
    margin-bottom: 20px;
  }
  
  .el-col:first-child,
  .el-col:last-child {
    margin-bottom: 0;
  }
  
  .wasd-key {
    width: 40px;
    height: 40px;
    font-size: 12px;
  }
  
  .wasd-key span {
    font-size: 8px;
  }
}
</style>