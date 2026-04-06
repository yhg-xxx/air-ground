<template>
  <div class="control-center">
    <!-- 顶部连接状态区域 -->
    <el-card class="connection-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>连接状态管理</span>
        </div>
      </template>
      
      <div class="connection-content">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="connection-item">
              <h4>WebSocket连接</h4>
              <el-tag :type="wsStatus.type" size="large">
                {{ wsStatus.text }}
              </el-tag>
              <div class="connection-buttons">
                <el-button 
                  type="success" 
                  @click="connectWebSocket"
                  :loading="loading.ws.connect"
                  :disabled="wsConnected"
                >
                  连接
                </el-button>
                <el-button 
                  type="danger" 
                  @click="disconnectWebSocket"
                  :loading="loading.ws.disconnect"
                  :disabled="!wsConnected"
                >
                  断开
                </el-button>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="connection-item">
              <h4>官方服务器连接</h4>
              <el-tag :type="officialStatus.type" size="large">
                {{ officialStatus.text }}
              </el-tag>
              <div class="connection-buttons">
                <el-button 
                  type="primary" 
                  @click="connectOfficialServer"
                  :loading="loading.official.connect"
                  :disabled="officialConnected"
                >
                  连接
                </el-button>
                <el-button 
                  type="danger" 
                  @click="disconnectOfficialServer"
                  :disabled="!officialConnected"
                >
                  断开
                </el-button>
              </div>
              <div class="token-info" v-if="officialToken">
                <el-text size="small" type="info">Token: {{ officialToken.substring(0, 20) }}...</el-text>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>



    <!-- 主要控制区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：设备控制 -->
      <el-col :span="12">
        <!-- 无人机控制 -->
        <el-card class="control-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>无人机控制</span>
              <el-tag :type="wsConnected || officialConnected ? 'success' : 'danger'">
                {{ wsConnected || officialConnected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
          </template>
          
          <div class="control-content">
            <!-- 方向控制 -->
            <el-divider content-position="left">方向控制</el-divider>
            <div class="direction-control">
              <el-row :gutter="5" justify="center">
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('aircraft', 'throttle', 1600)"
                    @mouseup="stopControl('aircraft', 'throttle')"
                    @mouseleave="stopControl('aircraft', 'throttle')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    前进
                  </el-button>
                </el-col>
              </el-row>
              
              <el-row :gutter="5" justify="center" style="margin-top: 5px;">
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('aircraft', 'direction', 1000)"
                    @mouseup="stopControl('aircraft', 'direction')"
                    @mouseleave="stopControl('aircraft', 'direction')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    左转
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="success" 
                    @mousedown="startControl('aircraft', 'altitude', 1600)"
                    @mouseup="stopControl('aircraft', 'altitude')"
                    @mouseleave="stopControl('aircraft', 'altitude')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    上升
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('aircraft', 'direction', 2000)"
                    @mouseup="stopControl('aircraft', 'direction')"
                    @mouseleave="stopControl('aircraft', 'direction')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    右转
                  </el-button>
                </el-col>
              </el-row>
              
              <el-row :gutter="5" justify="center" style="margin-top: 5px;">
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('aircraft', 'movement', 1000)"
                    @mouseup="stopControl('aircraft', 'movement')"
                    @mouseleave="stopControl('aircraft', 'movement')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    左移
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="warning" 
                    @mousedown="startControl('aircraft', 'throttle', 1400)"
                    @mouseup="stopControl('aircraft', 'throttle')"
                    @mouseleave="stopControl('aircraft', 'throttle')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    后退
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('aircraft', 'movement', 2000)"
                    @mouseup="stopControl('aircraft', 'movement')"
                    @mouseleave="stopControl('aircraft', 'movement')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    右移
                  </el-button>
                </el-col>
              </el-row>
              
              <el-row :gutter="5" justify="center" style="margin-top: 5px;">
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('aircraft', 'altitude', 1400)"
                    @mouseup="stopControl('aircraft', 'altitude')"
                    @mouseleave="stopControl('aircraft', 'altitude')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn"
                  >
                    下降
                  </el-button>
                </el-col>
              </el-row>
            </div>
            
            <!-- 云台控制 -->
            <el-divider content-position="left">云台控制</el-divider>
            <div class="gimbal-control">
              <el-row :gutter="10">
                <el-col :span="8">
                  <el-button 
                    type="info" 
                    @mousedown="startControl('aircraft', 'gimbal_pitch', 1400)"
                    @mouseup="stopControl('aircraft', 'gimbal_pitch')"
                    @mouseleave="stopControl('aircraft', 'gimbal_pitch')"
                    :disabled="!wsConnected && !officialConnected"
                    class="gimbal-btn"
                  >
                    云台下
                  </el-button>
                </el-col>
                <el-col :span="8">
                  <el-button 
                    type="warning" 
                    @click="gimbalReset"
                    :loading="loading.aircraft.gimbalReset"
                    :disabled="!wsConnected && !officialConnected"
                    class="gimbal-btn"
                  >
                    云台复位
                  </el-button>
                </el-col>
                <el-col :span="8">
                  <el-button 
                    type="info" 
                    @mousedown="startControl('aircraft', 'gimbal_pitch', 1600)"
                    @mouseup="stopControl('aircraft', 'gimbal_pitch')"
                    @mouseleave="stopControl('aircraft', 'gimbal_pitch')"
                    :disabled="!wsConnected && !officialConnected"
                    class="gimbal-btn"
                  >
                    云台上
                  </el-button>
                </el-col>
              </el-row>
            </div>

            <!-- 降落控制 -->
            <el-divider content-position="left">降落控制</el-divider>
            <div class="landing-control">
              <el-form :model="landingForm" label-width="120px" style="margin-bottom: 20px;">
                <el-form-item label="目标Aruco码ID">
                  <el-input-number 
                    v-model="landingForm.arucoId" 
                    :min="0" 
                    :max="255" 
                    :step="1"
                  />
                </el-form-item>
                <el-form-item label="降落状态">
                  <el-tag :type="getLandingStatusType()">
                    {{ landingStatus.status || '空闲' }}
                  </el-tag>
                  <el-text v-if="landingStatus.error_message" type="danger" style="margin-left: 10px;">
                    {{ landingStatus.error_message }}
                  </el-text>
                </el-form-item>
              </el-form>
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-button 
                    type="success" 
                    @click="startLanding" 
                    :loading="loading.landing.start"
                    :disabled="!wsConnected && !officialConnected || landingStatus.status === 'detecting' || landingStatus.status === 'aligning' || landingStatus.status === 'descending'"
                    class="landing-btn"
                  >
                    开始降落
                  </el-button>
                </el-col>
                <el-col :span="12">
                  <el-button 
                    type="danger" 
                    @click="cancelLanding" 
                    :loading="loading.landing.cancel"
                    :disabled="!wsConnected && !officialConnected || landingStatus.status === 'idle' || landingStatus.status === 'landed' || landingStatus.status === 'failed' || landingStatus.status === 'cancelled'"
                    class="landing-btn"
                  >
                    取消降落
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-card>

        <!-- 无人车控制 -->
        <el-card class="control-card" shadow="hover" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>无人车控制</span>
              <el-tag :type="wsConnected || officialConnected ? 'success' : 'danger'">
                {{ wsConnected || officialConnected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
          </template>
          
          <div class="control-content">
            <!-- 方向控制 -->
            <el-divider content-position="left">方向控制</el-divider>
            <div class="direction-control">
              <el-row :gutter="5" justify="center">
                <el-col :span="8">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('vehicle', 'throttle', 1700)"
                    @mouseup="stopControl('vehicle', 'throttle')"
                    @mouseleave="stopControl('vehicle', 'throttle')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn large"
                  >
                    前进
                  </el-button>
                </el-col>
              </el-row>
              
              <el-row :gutter="5" justify="center" style="margin-top: 10px;">
                <el-col :span="8">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('vehicle', 'direction', 1000)"
                    @mouseup="stopControl('vehicle', 'direction')"
                    @mouseleave="stopControl('vehicle', 'direction')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn large"
                  >
                    左转
                  </el-button>
                </el-col>
                <el-col :span="8">
                  <el-button 
                    type="warning" 
                    @mousedown="startControl('vehicle', 'throttle', 1300)"
                    @mouseup="stopControl('vehicle', 'throttle')"
                    @mouseleave="stopControl('vehicle', 'throttle')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn large"
                  >
                    后退
                  </el-button>
                </el-col>
                <el-col :span="8">
                  <el-button 
                    type="primary" 
                    @mousedown="startControl('vehicle', 'direction', 2000)"
                    @mouseup="stopControl('vehicle', 'direction')"
                    @mouseleave="stopControl('vehicle', 'direction')"
                    :disabled="!wsConnected && !officialConnected"
                    class="direction-btn large"
                  >
                    右转
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：遥测数据和图像管理 -->
      <el-col :span="12">
        <!-- 遥测数据 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="telemetry-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>无人机遥测</span>
                  <el-tag :type="telemetry.aircraft.online ? 'success' : 'danger'">
                    {{ telemetry.aircraft.online ? '在线' : '离线' }}
                  </el-tag>
                </div>
              </template>
              
              <div class="telemetry-content">
                <el-descriptions :column="1" size="small">
                  <el-descriptions-item label="电量">
                    <el-progress 
                      :percentage="telemetry.aircraft.power" 
                      :color="getPowerColor(telemetry.aircraft.power)"
                      :show-text="true"
                    />
                  </el-descriptions-item>
                  <el-descriptions-item label="电压">
                    {{ telemetry.aircraft.voltage !== null ? telemetry.aircraft.voltage + 'V' : '--' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="GPS">
                    {{ telemetry.aircraft.gps ? telemetry.aircraft.gps.join(', ') : '未定位' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="速度">
                    {{ telemetry.aircraft.speed !== null ? telemetry.aircraft.speed + ' m/s' : '--' }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card class="telemetry-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>无人车遥测</span>
                  <el-tag :type="telemetry.vehicle.online ? 'success' : 'danger'">
                    {{ telemetry.vehicle.online ? '在线' : '离线' }}
                  </el-tag>
                </div>
              </template>
              
              <div class="telemetry-content">
                <el-descriptions :column="1" size="small">
                  <el-descriptions-item label="电量">
                    <el-progress 
                      :percentage="telemetry.vehicle.power" 
                      :color="getPowerColor(telemetry.vehicle.power)"
                      :show-text="true"
                    />
                  </el-descriptions-item>
                  <el-descriptions-item label="电压">
                    {{ telemetry.vehicle.voltage !== null ? telemetry.vehicle.voltage + 'V' : '--' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="GPS">
                    {{ telemetry.vehicle.gps ? telemetry.vehicle.gps.join(', ') : '未定位' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="速度">
                    {{ telemetry.vehicle.speed !== null ? telemetry.vehicle.speed + ' m/s' : '--' }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 图像管理 -->
        <el-card class="image-card" shadow="hover" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>图像管理</span>
              <div class="header-actions">
                <el-button 
                  v-if="currentImage" 
                  type="success" 
                  size="small"
                  @click="downloadImage"
                >
                  下载图像
                </el-button>
                <el-button 
                  v-if="currentImage" 
                  type="warning" 
                  size="small"
                  @click="clearImage"
                >
                  清除图像
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="image-content">
            <!-- 图像抓拍控制 -->
            <el-form :model="form" label-width="80px" style="margin-bottom: 20px;">
              <el-form-item label="操作">
                <el-button 
                  type="primary" 
                  @click="captureImage" 
                  :loading="capturing"
                  :disabled="!wsConnected && !officialConnected"
                  size="large"
                >
                  抓拍图像
                </el-button>
              </el-form-item>
              
              <el-form-item label="自动抓拍">
                <el-switch 
                  v-model="autoCapture" 
                  active-text="开启" 
                  inactive-text="关闭"
                  @change="toggleAutoCapture"
                  :disabled="!wsConnected && !officialConnected"
                />
              </el-form-item>
              
              <el-form-item v-if="autoCapture" label="抓拍间隔">
                <el-input-number 
                  v-model="captureInterval" 
                  :min="1" 
                  :max="60" 
                  :step="1"
                  @change="updateAutoCapture"
                />
                <span style="margin-left: 10px;">秒</span>
              </el-form-item>
            </el-form>

            <!-- 图像预览 -->
            <div class="image-preview">
              <div v-if="currentImage" class="image-wrapper">
                <img 
                  :src="currentImage" 
                  alt="抓拍图像" 
                  class="captured-image"
                  @load="onImageLoad"
                  @error="onImageError"
                />
                <div class="image-info">
                  <p><strong>抓拍时间:</strong> {{ lastCaptureTime }}</p>
                  <p><strong>图像大小:</strong> {{ imageSize }}</p>
                </div>
              </div>
              <div v-else class="no-image">
                <el-empty 
                  description="暂无图像" 
                  :image-size="200"
                >
                  <el-button 
                    type="primary" 
                    @click="captureImage"
                    :loading="capturing"
                    :disabled="!wsConnected && !officialConnected"
                  >
                    开始抓拍
                  </el-button>
                </el-empty>
              </div>
            </div>

            <!-- 统计信息和历史记录 -->
            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="12">
                <div class="statistics">
                  <h4>统计信息</h4>
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="总抓拍次数">
                      {{ totalCaptures }}
                    </el-descriptions-item>
                    <el-descriptions-item label="成功次数">
                      <el-tag type="success">{{ successCaptures }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="失败次数">
                      <el-tag type="danger">{{ failedCaptures }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="最后抓拍">
                      {{ lastCaptureTime || '从未抓拍' }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="history">
                  <h4>操作历史</h4>
                  <el-timeline>
                    <el-timeline-item
                      v-for="(item, index) in history"
                      :key="index"
                      :timestamp="item.time"
                      :type="item.success ? 'success' : 'danger'"
                    >
                      {{ item.message }}
                    </el-timeline-item>
                  </el-timeline>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { controlAPI, gimbalAPI, landingAPI } from '@/services/api'
import {
  officialServerAPI,
  WebSocketManager,
  CONTROL_CHANNELS,
  CONTROL_VALUES
} from '@/services/officialAPI'

// 响应式数据
const wsConnected = ref(false)
const officialConnected = ref(false)
const officialToken = ref('')
const capturing = ref(false)
const currentImage = ref('')
const autoCapture = ref(false)
const captureInterval = ref(5)
const autoCaptureTimer = ref(null)

// 统计信息
const totalCaptures = ref(0)
const successCaptures = ref(0)
const failedCaptures = ref(0)
const lastCaptureTime = ref('')
const imageSize = ref('')

// 操作历史
const history = ref([])

// 加载状态
const loading = reactive({
  ws: {
    connect: false,
    disconnect: false
  },
  official: {
    connect: false
  },
  aircraft: {
    gimbalReset: false
  },
  landing: {
    start: false,
    cancel: false,
    status: false
  }
})

// 降落相关数据
const landingForm = reactive({
  arucoId: 0
})

const landingStatus = reactive({
  status: 'idle',
  error_message: ''
})

// 遥测数据
const telemetry = reactive({
  aircraft: {
    online: false,
    power: 0,
    voltage: null,
    gps: null,
    speed: null
  },
  vehicle: {
    online: false,
    power: 0,
    voltage: null,
    gps: null,
    speed: null
  }
})

// 控制定时器
const controlTimers = reactive({})

// WebSocket管理器
const wsManager = ref(null)

// 连接状态计算
const wsStatus = computed(() => {
  if (loading.ws.connect) return { type: 'warning', text: '连接中...' }
  if (wsConnected.value) return { type: 'success', text: '已连接' }
  return { type: 'danger', text: '未连接' }
})

const officialStatus = computed(() => {
  if (loading.official.connect) return { type: 'warning', text: '连接中...' }
  if (officialConnected.value) return { type: 'success', text: '已连接' }
  return { type: 'danger', text: '未连接' }
})

// 无人机通道映射
const aircraftChannels = {
  direction: 1,      // 左转/右转
  altitude: 2,        // 上升/下降
  movement: 3,        // 左移/右移
  throttle: 4,        // 前进/后退
  gimbal_pitch: 5,    // 云台俯仰
  gimbal_roll: 6,      // 云台横滚
  takeoff: 7,         // 起飞
  land: 8,           // 降落
  back: 9,           // 返航
  gimbal_reset: 10     // 云台复位
}

// 无人车通道映射
const vehicleChannels = {
  direction: 1,       // 左转/右转
  throttle: 2         // 前进/后退
}

// 电量颜色
const getPowerColor = (power) => {
  if (power > 50) return '#67c23a'
  if (power > 20) return '#e6a23c'
  return '#f56c6c'
}

// WebSocket连接
const connectWebSocket = async () => {
  loading.ws.connect = true
  try {
    const response = await controlAPI.connect()
    if (response.code === '1') {
      wsConnected.value = true
      ElMessage.success('WebSocket连接成功')
    } else {
      ElMessage.error(response.msg || '连接失败')
    }
  } catch (error) {
    console.error('连接失败:', error)
    ElMessage.error('连接失败: ' + (error.message || '网络错误'))
  } finally {
    loading.ws.connect = false
  }
}

// WebSocket断开
const disconnectWebSocket = async () => {
  loading.ws.disconnect = true
  try {
    const response = await controlAPI.disconnect()
    if (response.code === '1') {
      wsConnected.value = false
      ElMessage.success('WebSocket连接已断开')
    } else {
      ElMessage.error(response.msg || '断开失败')
    }
  } catch (error) {
    console.error('断开失败:', error)
    ElMessage.error('断开失败: ' + (error.message || '网络错误'))
  } finally {
    loading.ws.disconnect = false
  }
}

// 官方服务器连接
const connectOfficialServer = async () => {
  try {
    loading.official.connect = true
    const serverToken = await officialServerAPI.getToken()
    officialToken.value = serverToken
    localStorage.setItem('official_token', serverToken)

    wsManager.value = new WebSocketManager()

    wsManager.value.on('connected', () => {
      officialConnected.value = true
      ElMessage.success('官方服务器连接成功')
    })

    wsManager.value.on('disconnected', () => {
      officialConnected.value = false
      ElMessage.warning('官方服务器连接断开')
    })

    wsManager.value.on('aircraft_telemetry', (data) => {
      Object.assign(telemetry.aircraft, { ...data, online: true })
    })

    wsManager.value.on('vehicle_telemetry', (data) => {
      Object.assign(telemetry.vehicle, { ...data, online: true })
    })

    await wsManager.value.connect(serverToken)
  } catch (error) {
    ElMessage.error('连接失败: ' + error.message)
  } finally {
    loading.official.connect = false
  }
}

// 官方服务器断开
const disconnectOfficialServer = () => {
  if (wsManager.value) wsManager.value.disconnect()
  officialConnected.value = false
  officialToken.value = ''
  localStorage.removeItem('official_token')
  ElMessage.info('已断开官方服务器连接')
}

// 开始控制
const startControl = (target, controlType, value) => {
  if (!wsConnected.value && !officialConnected.value) {
    ElMessage.warning('请先连接设备')
    return
  }

  const key = `${target}_${controlType}`

  if (controlTimers[key]) clearInterval(controlTimers[key])

  if (officialConnected.value && wsManager.value) {
    // 使用官方服务器控制
    const channelName = target === 'aircraft' ? `AIRCRAFT_${controlType.toUpperCase()}` : `VEHICLE_${controlType.toUpperCase()}`
    const channel = CONTROL_CHANNELS[channelName]
    if (channel) {
      wsManager.value.sendControl(target, channel, value)
      controlTimers[key] = setInterval(() => {
        wsManager.value.sendControl(target, channel, value)
      }, 100)
    }
  } else if (wsConnected.value) {
    // 使用本地WebSocket控制
    const channel = target === 'aircraft' ? aircraftChannels[controlType] : vehicleChannels[controlType]
    if (channel) {
      const controlFunc = target === 'aircraft' ? controlAPI.controlAircraft : controlAPI.controlVehicle
      controlFunc(channel, value)
      controlTimers[key] = setInterval(() => {
        controlFunc(channel, value)
      }, 100)
    }
  }
}

// 停止控制
const stopControl = (target, controlType) => {
  const key = `${target}_${controlType}`
  if (controlTimers[key]) {
    clearInterval(controlTimers[key])
    delete controlTimers[key]
  }

  if (officialConnected.value && wsManager.value) {
    // 使用官方服务器控制
    const channelName = target === 'aircraft' ? `AIRCRAFT_${controlType.toUpperCase()}` : `VEHICLE_${controlType.toUpperCase()}`
    const channel = CONTROL_CHANNELS[channelName]
    if (channel) {
      wsManager.value.sendControl(target, channel, CONTROL_VALUES.MID)
    }
  } else if (wsConnected.value) {
    // 使用本地WebSocket控制
    const channel = target === 'aircraft' ? aircraftChannels[controlType] : vehicleChannels[controlType]
    if (channel) {
      const controlFunc = target === 'aircraft' ? controlAPI.controlAircraft : controlAPI.controlVehicle
      controlFunc(channel, 1500)
    }
  }
}

// 云台复位
const gimbalReset = async () => {
  loading.aircraft.gimbalReset = true
  try {
    if (officialConnected.value && wsManager.value) {
      wsManager.value.sendControl('aircraft', CONTROL_CHANNELS.AIRCRAFT_GIMBAL_RESET, 2000)
    } else if (wsConnected.value) {
      await controlAPI.controlAircraft(aircraftChannels.gimbal_reset, 2000)
    }
    ElMessage.success('云台复位指令发送成功')
    addToHistory('云台复位', true)
  } catch (error) {
    console.error('云台复位失败:', error)
    ElMessage.error('云台复位失败: ' + (error.message || '网络错误'))
    addToHistory('云台复位失败: ' + (error.message || '网络错误'), false)
  } finally {
    loading.aircraft.gimbalReset = false
  }
}

// 图像抓拍
const captureImage = async () => {
  if (!wsConnected.value && !officialConnected.value) {
    ElMessage.warning('请先连接设备')
    return
  }

  capturing.value = true
  totalCaptures.value++
  
  try {
    let imageData
    if (officialConnected.value && officialToken.value) {
      // 使用官方API抓拍
      imageData = await officialServerAPI.captureImage(officialToken.value)
      // 检查返回数据是否有效
      if (!imageData || (typeof imageData === 'object' && imageData.code !== '1')) {
        throw new Error('官方API返回失败')
      }
    } else if (wsConnected.value) {
      // 使用本地API抓拍
      const response = await gimbalAPI.captureImage()
      // 检查返回数据是否有效
      if (!response || (typeof response === 'object' && response.code !== '1')) {
        throw new Error('本地API返回失败')
      }
      imageData = response
    }
    
    if (imageData) {
      // 创建blob URL
      const blob = new Blob([imageData], { type: 'image/jpeg' })
      const imageUrl = URL.createObjectURL(blob)
      currentImage.value = imageUrl
      
      // 更新图像信息
      lastCaptureTime.value = new Date().toLocaleString()
      imageSize.value = `${(blob.size / 1024).toFixed(2)} KB`
      
      successCaptures.value++
      addToHistory('图像抓拍成功', true)
      ElMessage.success('图像抓拍成功')
    } else {
      throw new Error('未获取到图像数据')
    }
  } catch (error) {
    console.error('抓拍失败:', error)
    failedCaptures.value++
    const errorMessage = error.message || '网络错误'
    addToHistory('抓拍失败: ' + errorMessage, false)
    ElMessage.error('抓拍失败: ' + errorMessage)
  } finally {
    capturing.value = false
  }
}

// 切换自动抓拍
const toggleAutoCapture = (enabled) => {
  if (enabled) {
    startAutoCapture()
  } else {
    stopAutoCapture()
  }
}

// 开始自动抓拍
const startAutoCapture = () => {
  if (autoCaptureTimer.value) {
    clearInterval(autoCaptureTimer.value)
  }
  
  autoCaptureTimer.value = setInterval(() => {
    if (!capturing.value) {
      captureImage()
    }
  }, captureInterval.value * 1000)
  
  addToHistory(`开始自动抓拍，间隔 ${captureInterval.value} 秒`, true)
  ElMessage.success(`自动抓拍已开启，间隔 ${captureInterval.value} 秒`)
}

// 停止自动抓拍
const stopAutoCapture = () => {
  if (autoCaptureTimer.value) {
    clearInterval(autoCaptureTimer.value)
    autoCaptureTimer.value = null
  }
  
  addToHistory('停止自动抓拍', true)
  ElMessage.info('自动抓拍已停止')
}

// 更新自动抓拍间隔
const updateAutoCapture = () => {
  if (autoCapture.value) {
    stopAutoCapture()
    startAutoCapture()
  }
}

// 下载图像
const downloadImage = () => {
  if (!currentImage.value) return
  
  const link = document.createElement('a')
  link.href = currentImage.value
  link.download = `capture_${Date.now()}.jpg`
  link.click()
  
  ElMessage.success('图像下载已开始')
  addToHistory('下载图像', true)
}

// 清除图像
const clearImage = () => {
  if (currentImage.value) {
    URL.revokeObjectURL(currentImage.value)
    currentImage.value = ''
    imageSize.value = ''
    ElMessage.success('图像已清除')
    addToHistory('清除图像', true)
  }
}

// 添加到历史记录
const addToHistory = (message, success) => {
  history.value.unshift({
    time: new Date().toLocaleString(),
    message,
    success
  })
  
  // 限制历史记录数量
  if (history.value.length > 20) {
    history.value = history.value.slice(0, 20)
  }
}

// 图像加载完成
const onImageLoad = () => {
  // 可以在这里添加图像加载完成后的处理
}

// 图像加载错误
const onImageError = () => {
  ElMessage.error('图像加载失败')
  currentImage.value = ''
  addToHistory('图像加载失败', false)
}

// 开始降落
const startLanding = async () => {
  if (!wsConnected.value && !officialConnected.value) {
    ElMessage.warning('请先连接设备')
    return
  }

  loading.landing.start = true
  try {
    const response = await landingAPI.startLanding(landingForm.arucoId)
    if (response.status === 'success') {
      ElMessage.success('降落过程已开始')
      addToHistory(`开始降落，目标Aruco码ID: ${landingForm.arucoId}`, true)
      // 开始轮询降落状态
      startLandingStatusPolling()
    } else {
      ElMessage.error(response.message || '开始降落失败')
      addToHistory(`开始降落失败: ${response.message || '未知错误'}`, false)
    }
  } catch (error) {
    console.error('开始降落失败:', error)
    ElMessage.error('开始降落失败: ' + (error.message || '网络错误'))
    addToHistory(`开始降落失败: ${error.message || '网络错误'}`, false)
  } finally {
    loading.landing.start = false
  }
}

// 取消降落
const cancelLanding = async () => {
  loading.landing.cancel = true
  try {
    const response = await landingAPI.cancelLanding()
    if (response.status === 'success') {
      ElMessage.success('降落过程已取消')
      addToHistory('取消降落', true)
      // 停止轮询降落状态
      stopLandingStatusPolling()
      // 更新本地状态
      landingStatus.status = 'cancelled'
      landingStatus.error_message = ''
    } else {
      ElMessage.error(response.message || '取消降落失败')
      addToHistory(`取消降落失败: ${response.message || '未知错误'}`, false)
    }
  } catch (error) {
    console.error('取消降落失败:', error)
    ElMessage.error('取消降落失败: ' + (error.message || '网络错误'))
    addToHistory(`取消降落失败: ${error.message || '网络错误'}`, false)
  } finally {
    loading.landing.cancel = false
  }
}

// 获取降落状态类型
const getLandingStatusType = () => {
  const status = landingStatus.status
  switch (status) {
    case 'idle':
      return 'info'
    case 'initializing':
    case 'detecting':
    case 'aligning':
    case 'descending':
      return 'warning'
    case 'landed':
      return 'success'
    case 'failed':
    case 'cancelled':
      return 'danger'
    default:
      return 'info'
  }
}

// 降落状态轮询
let landingStatusPollingTimer = null

// 开始轮询降落状态
const startLandingStatusPolling = () => {
  // 先获取一次状态
  getLandingStatus()
  // 设置轮询
  if (landingStatusPollingTimer) {
    clearInterval(landingStatusPollingTimer)
  }
  landingStatusPollingTimer = setInterval(() => {
    getLandingStatus()
  }, 1000) // 每秒获取一次状态
}

// 停止轮询降落状态
const stopLandingStatusPolling = () => {
  if (landingStatusPollingTimer) {
    clearInterval(landingStatusPollingTimer)
    landingStatusPollingTimer = null
  }
}

// 获取降落状态
const getLandingStatus = async () => {
  try {
    const response = await landingAPI.getLandingStatus()
    landingStatus.status = response.status
    landingStatus.error_message = response.error_message || ''
    
    // 如果降落完成或失败，停止轮询
    if (response.status === 'landed' || response.status === 'failed' || response.status === 'cancelled') {
      stopLandingStatusPolling()
    }
  } catch (error) {
    console.error('获取降落状态失败:', error)
  }
}

// 组件挂载时
onMounted(() => {
  // 检查本地存储的token
  const token = localStorage.getItem('official_token')
  if (token) {
    officialToken.value = token
  }
})

// 组件卸载时
onUnmounted(() => {
  // 清理定时器
  Object.values(controlTimers).forEach(clearInterval)
  stopAutoCapture()
  stopLandingStatusPolling()
  
  // 断开连接
  if (wsManager.value) {
    wsManager.value.disconnect()
  }
  
  // 清除图像
  if (currentImage.value) {
    URL.revokeObjectURL(currentImage.value)
  }
})
</script>

<style scoped>
.control-center {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.connection-card, .quick-actions-card, .control-card, .telemetry-card, .image-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}

.connection-content {
  padding: 20px 0;
}

.connection-item {
  margin-bottom: 20px;
}

.connection-item h4 {
  margin-bottom: 10px;
  color: #303133;
}

.connection-buttons {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.token-info {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}



.control-content {
  padding: 10px 0;
}

.direction-control {
  text-align: center;
  margin: 20px 0;
}

.direction-btn {
  width: 80px;
  height: 40px;
  margin: 2px;
}

.direction-btn.large {
  width: 100px;
  height: 50px;
  margin: 5px;
}

.gimbal-btn {
  width: 100%;
  margin-bottom: 10px;
}

.landing-control {
  margin-top: 20px;
}

.landing-btn {
  width: 100%;
  height: 40px;
  font-size: 14px;
  font-weight: bold;
}

.telemetry-content {
  padding: 10px 0;
}

.image-content {
  padding: 10px 0;
}

.image-preview {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20px 0;
}

.image-wrapper {
  text-align: center;
  width: 100%;
}

.captured-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.image-info {
  margin-top: 15px;
  text-align: left;
  background-color: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
}

.image-info p {
  margin: 5px 0;
  font-size: 14px;
}

.no-image {
  width: 100%;
  text-align: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.statistics, .history {
  margin-top: 10px;
}

.statistics h4, .history h4 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 14px;
}

.history {
  max-height: 200px;
  overflow-y: auto;
}

/* 按钮按下效果 */
.el-button:active {
  transform: scale(0.95);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-center {
    padding: 10px;
  }
  
  .connection-buttons {
    flex-direction: column;
  }
  

  
  .direction-btn {
    width: 60px;
    height: 35px;
    font-size: 12px;
  }
  
  .direction-btn.large {
    width: 80px;
    height: 40px;
  }
  
  .image-preview {
    min-height: 200px;
  }
  
  .captured-image {
    max-height: 200px;
  }
}
</style>