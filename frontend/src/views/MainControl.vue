<template>
  <div class="main-control futuristic">
    <!-- 顶部状态栏 -->
    <div class="top-status-bar">
      <div class="system-title">
        <div class="title-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span class="main-title">空地协同</span>
      </div>

      <!-- 紧凑设备状态显示 -->
      <div class="compact-telemetry">
        <!-- 无人机 -->
        <div class="telemetry-chip aircraft">
          <span class="chip-icon">✈️</span>
          <div class="chip-data">
            <div class="chip-row">
              <span class="chip-label">电量</span>
              <div class="mini-progress">
                <div class="mini-fill" :class="getBatteryClass(telemetryData.aircraft.power)" 
                     :style="{ width: telemetryData.aircraft.power + '%' }"></div>
              </div>
              <span class="chip-value">{{ telemetryData.aircraft.power }}%</span>
            </div>
            <div class="chip-row">
              <span class="chip-label">电压</span>
              <span class="chip-value">{{ telemetryData.aircraft.voltage }}V</span>
              <span class="chip-divider">|</span>
              <span class="chip-label">速度</span>
              <span class="chip-value">{{ telemetryData.aircraft.speed }}m/s</span>
            </div>
            <div class="chip-row">
              <span class="chip-label">GPS</span>
              <span class="chip-value gps">{{ formatGps(telemetryData.aircraft.gps) }}</span>
            </div>
          </div>
        </div>

        <!-- 无人车 -->
        <div class="telemetry-chip vehicle">
          <span class="chip-icon">🚗</span>
          <div class="chip-data">
            <div class="chip-row">
              <span class="chip-label">电量</span>
              <div class="mini-progress">
                <div class="mini-fill" :class="getBatteryClass(telemetryData.vehicle.power)" 
                     :style="{ width: telemetryData.vehicle.power + '%' }"></div>
              </div>
              <span class="chip-value">{{ telemetryData.vehicle.power }}%</span>
            </div>
            <div class="chip-row">
              <span class="chip-label">电压</span>
              <span class="chip-value">{{ telemetryData.vehicle.voltage }}V</span>
              <span class="chip-divider">|</span>
              <span class="chip-label">速度</span>
              <span class="chip-value">{{ telemetryData.vehicle.speed }}m/s</span>
            </div>
            <div class="chip-row">
              <span class="chip-label">GPS</span>
              <span class="chip-value gps">{{ formatGps(telemetryData.vehicle.gps) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="connection-indicator">
        <div class="status-dot" :class="wsConnected ? 'online' : 'offline'"></div>
        <span class="status-text">{{ wsConnected ? '在线' : '离线' }}</span>
        <el-button 
          :type="wsConnected ? 'success' : 'primary'" 
          size="small" 
          @click="connectWebSocket" 
          :disabled="wsConnected"
          class="connect-btn"
        >
          {{ wsConnected ? '已连接' : '连接' }}
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <el-row :gutter="16" class="main-content">
      <!-- 控制界面 -->
      <el-col :span="16">
        <el-card class="control-card">
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>设备控制</span>
            </div>
          </template>

          <!-- 双设备控制面板 -->
          <div class="dual-control-panel">
            <!-- 无人车控制 -->
            <div class="control-section vehicle-section">
              <h4 class="section-title">🚗 无人车控制</h4>
              <div class="control-panel joystick-mode">
                <div class="joystick-wrapper">
                  <VirtualJoystick
                    :size="160"
                    label="移动控制"
                    topLabel="前进"
                    bottomLabel="后退"
                    leftLabel="左转"
                    rightLabel="右转"
                    :showSpeedLimit="true"
                    @change="handleVehicleJoystick"
                  />
                </div>
                <div class="control-tips compact">
                  <p>• 上下：前进/后退</p>
                  <p>• 左右：左转/右转</p>
                </div>
              </div>
            </div>

            <!-- 无人机控制 -->
            <div class="control-section aircraft-section">
              <h4 class="section-title">✈️ 无人机控制</h4>
              <div class="control-panel joystick-mode">
                <!-- 移动摇杆 -->
                <div class="joystick-wrapper">
                  <VirtualJoystick
                    :size="160"
                    label="移动控制"
                    topLabel="前进"
                    bottomLabel="后退"
                    leftLabel="左移"
                    rightLabel="右移"
                    :showSpeedLimit="true"
                    @change="handleAircraftRightJoystick"
                  />
                </div>

                <!-- 键盘控制 -->
                <div class="keyboard-control-section compact">
                  <div class="keyboard-header">
                    <span>WASD姿态控制</span>
                    <el-switch
                      v-model="keyboardControlEnabled"
                      @change="toggleKeyboardControl"
                      size="small"
                    />
                  </div>
                  
                  <div v-if="keyboardControlEnabled" class="keyboard-tips">
                    <div class="wasd-layout compact">
                      <div class="wasd-row">
                        <div class="wasd-key small" :class="{ 'active': pressedKeys.has('W') }">W<span>升</span></div>
                      </div>
                      <div class="wasd-row">
                        <div class="wasd-key small" :class="{ 'active': pressedKeys.has('A') }">A<span>左</span></div>
                        <div class="wasd-key small" :class="{ 'active': pressedKeys.has('S') }">S<span>降</span></div>
                        <div class="wasd-key small" :class="{ 'active': pressedKeys.has('D') }">D<span>右</span></div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 云台控制 -->
                <div class="gimbal-section">
                  <div class="gimbal-header">
                    <span>云台</span>
                    <span class="sensitivity-value">{{ Math.round(gimbalSensitivity * 100) }}%</span>
                  </div>
                  <el-slider
                    v-model="gimbalSensitivity"
                    :min="0.1"
                    :max="1.0"
                    :step="0.1"
                    :show-tooltip="false"
                    size="small"
                    style="margin: 5px 0;"
                  />
                  <div class="gimbal-joystick-wrapper compact">
                    <VirtualJoystick
                      :size="100"
                      topLabel="仰"
                      bottomLabel="俯"
                      leftLabel="左"
                      rightLabel="右"
                      :autoCenter="true"
                      @change="handleGimbalJoystick"
                    />
                  </div>
                </div>

                <div class="drone-buttons compact">
                  <el-button type="primary" size="small" @click="sendDroneCommand('takeoff')">
                    起飞
                  </el-button>
                  <el-button type="warning" size="small" @click="sendDroneCommand('land')">
                    降落
                  </el-button>
                  <el-button type="danger" size="small" @click="sendDroneCommand('back')">
                    返航
                  </el-button>
                  <el-button type="info" size="small" @click="sendDroneCommand('gimbalReset')">
                    云台复位
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：图像显示和抓拍功能 -->
      <el-col :span="8">
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
// const activeControlTab = ref('vehicle')  // 不再需要tab切换
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

// 电量样式类
const getBatteryClass = (power) => {
  if (power > 60) return 'battery-good'
  if (power > 20) return 'battery-medium'
  return 'battery-low'
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
/* 和谐深色主题 */
.main-control.futuristic {
  padding: 0;
  min-height: 100vh;
  background: linear-gradient(135deg, #1e2732 0%, #2d3748 50%, #1a202c 100%);
}

/* 顶部状态栏 */
.top-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(45, 55, 72, 0.8);
  border-bottom: 1px solid rgba(74, 85, 104, 0.3);
  backdrop-filter: blur(15px);
}

.system-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #3b82f6, #10b981);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
}

.title-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.title-text {
  display: flex;
  flex-direction: column;
}

.main-title {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 2px;
}

.sub-title {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 1px;
}

.connection-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-dot.online {
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
}

.status-dot.offline {
  background: #ef4444;
  box-shadow: 0 0 10px #ef4444;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

.connect-btn {
  border-radius: 20px;
}

/* 紧凑遥测芯片 */
.compact-telemetry {
  display: flex;
  gap: 16px;
}

.telemetry-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 8px 14px;
  backdrop-filter: blur(10px);
}

.telemetry-chip.aircraft {
  border-left: 3px solid #3b82f6;
}

.telemetry-chip.vehicle {
  border-left: 3px solid #10b981;
}

.chip-icon {
  font-size: 20px;
}

.chip-data {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chip-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.chip-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}

.chip-value {
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
}

.chip-value.gps {
  font-size: 10px;
  font-family: 'Monaco', 'Consolas', monospace;
  color: rgba(255, 255, 255, 0.8);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip-divider {
  color: rgba(255, 255, 255, 0.3);
  margin: 0 2px;
}

.mini-progress {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.mini-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.mini-fill.battery-good {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.mini-fill.battery-medium {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.mini-fill.battery-low {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

/* 和谐玻璃卡片效果 */
.glass-card {
  background: rgba(45, 55, 72, 0.4);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(74, 85, 104, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  padding: 20px;
  height: 100%;
}

/* 状态面板 */
.status-panel {
  background: rgba(255, 255, 255, 0.98);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
}

.header-icon {
  font-size: 20px;
}

/* 设备卡片 */
.device-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.device-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.device-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.device-icon {
  font-size: 28px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.device-info {
  flex: 1;
}

.device-name {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  display: block;
}

.device-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  display: inline-block;
  margin-top: 2px;
}

.device-status.status-good {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

.device-status.status-warning {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

/* 遥测数据网格 */
.telemetry-grid {
  display: grid;
  gap: 10px;
}

.telemetry-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}

.telemetry-item:last-child {
  border-bottom: none;
}

.item-label {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.item-icon {
  font-size: 14px;
}

.item-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  width: 60px;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-fill.battery-good {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.progress-fill.battery-medium {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.progress-fill.battery-low {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.value-text {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  min-width: 36px;
  text-align: right;
}

.value-number {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.value-unit {
  font-size: 11px;
  color: #94a3b8;
  margin-left: 2px;
}

.gps-value {
  font-size: 11px;
  color: #475569;
  font-family: 'Monaco', 'Consolas', monospace;
}

/* 主内容区 */
.main-content {
  padding: 16px;
  margin-top: 0;
}

/* 和谐控制卡片 */
.control-card,
.image-card {
  height: 100%;
  border-radius: 16px;
  border: 1px solid rgba(74, 85, 104, 0.2);
  background: rgba(45, 55, 72, 0.3);
  backdrop-filter: blur(15px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #e2e8f0;
}

/* 保留原有样式 */
.page-header {
  margin-bottom: 20px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.status-card {
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
  background: rgba(74, 85, 104, 0.2);
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: #cbd5e0;
  width: 100%;
  max-width: 300px;
}

.control-tips.compact {
  font-size: 11px;
  padding: 6px 10px;
  max-width: 160px;
}

.control-tips.compact p {
  margin: 2px 0;
}

.control-tips p {
  margin: 4px 0;
}

.control-tips strong {
  color: #e2e8f0;
}

.drone-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.drone-buttons.compact {
  gap: 6px;
  margin-top: 12px;
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
  border: 1px solid rgba(74, 85, 104, 0.3);
  border-radius: 8px;
  background: rgba(74, 85, 104, 0.1);
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
  color: #a0aec0;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 10px;
  color: #718096;
}

.capture-controls {
  display: flex;
  gap: 10px;
}

.keyboard-control-section {
  margin: 20px 0;
  padding: 15px;
  background: rgba(74, 85, 104, 0.15);
  border-radius: 8px;
  border: 1px solid rgba(74, 85, 104, 0.3);
}

.keyboard-control-section h4 {
  margin: 0 0 15px 0;
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
}

.keyboard-tips {
  margin-top: 10px;
  color: #e2e8f0;
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
  border: 2px solid rgba(74, 85, 104, 0.4);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  font-weight: bold;
  font-size: 14px;
  color: #4a5568;
  transition: all 0.2s ease;
  position: relative;
}

.wasd-key span {
  font-size: 10px;
  font-weight: normal;
  margin-top: 2px;
  color: #718096;
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
  margin-top: 5px;
}

/* 响应式调整 */
/* 双设备控制面板布局 */
.dual-control-panel {
  display: flex;
  gap: 20px;
  justify-content: space-between;
}

.control-section {
  flex: 1;
  padding: 15px;
  border-radius: 8px;
  background: rgba(74, 85, 104, 0.15);
  border: 1px solid rgba(74, 85, 104, 0.3);
}

.section-title {
  margin: 0 0 15px 0;
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
  text-align: center;
}

/* 紧凑样式 */
.control-tips.compact {
  padding: 8px 12px;
  font-size: 12px;
  max-width: 200px;
}

.keyboard-control-section.compact {
  margin: 10px 0;
  padding: 10px;
}

.keyboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #e2e8f0;
}

.wasd-layout.compact {
  gap: 4px;
  margin-bottom: 0;
}

.wasd-key.small {
  width: 36px;
  height: 36px;
  font-size: 12px;
}

.wasd-key.small span {
  font-size: 9px;
  margin-top: 1px;
}

/* 云台区域 */
.gimbal-section {
  margin: 10px 0;
  padding: 10px;
  background: rgba(74, 85, 104, 0.15);
  border-radius: 6px;
}

.gimbal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 5px;
  color: #e2e8f0;
}

.sensitivity-value {
  color: #3b82f6;
  font-size: 12px;
}

.gimbal-joystick-wrapper.compact {
  margin: 8px 0 0 0;
}

/* 紧凑按钮组 */
.drone-buttons.compact {
  margin-top: 10px;
  gap: 6px;
  justify-content: center;
}

/* 响应式调整 */
@media screen and (max-width: 1400px) {
  .dual-control-panel {
    flex-direction: column;
  }
  
  .control-section {
    width: 100%;
  }
}

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