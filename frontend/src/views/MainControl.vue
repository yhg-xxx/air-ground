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
                </div>

                <h4>云台控制</h4>
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
  
  // X轴控制转向：左负右正，需要反转（左转=2000, 右转=1000）
  // Y轴控制油门：上正下负（前进=2000, 后退=1000）
  vehicleSteering.value = 3000 - data.xValue // 反转X轴
  vehicleThrottle.value = data.yValue
  
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
  
  // X轴控制横滚
  // Y轴控制俯仰
  aircraftGimbalRoll.value = data.xValue
  aircraftGimbalPitch.value = data.yValue
  
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_PITCH, aircraftGimbalPitch.value)
  wsManager.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_ROLL, aircraftGimbalRoll.value)
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
  
  // 自动连接WebSocket
  connectWebSocket()
})

onUnmounted(() => {
  // 断开WebSocket连接
  wsManager.disconnect()
  // 清理图像资源
  clearImage()
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

/* 响应式调整 */
@media screen and (max-width: 1200px) {
  .el-col {
    margin-bottom: 20px;
  }
  
  .el-col:first-child,
  .el-col:last-child {
    margin-bottom: 0;
  }
}
</style>