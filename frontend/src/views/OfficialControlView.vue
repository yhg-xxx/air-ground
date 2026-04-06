<template>
  <div class="official-control">
    <!-- 连接状态卡片 -->
    <el-card class="status-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>连接状态</span>
          <el-tag :type="connectionStatus.type" size="large">
            {{ connectionStatus.text }}
          </el-tag>
        </div>
      </template>
      
      <div class="status-content">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-button 
              type="primary" 
              @click="connectServer" 
              :loading="connecting"
              :disabled="isConnected"
            >
              连接官方服务器
            </el-button>
          </el-col>
          <el-col :span="12">
            <el-button 
              type="danger" 
              @click="disconnectServer" 
              :disabled="!isConnected"
            >
              断开连接
            </el-button>
          </el-col>
        </el-row>
        
        <div class="token-info" v-if="token">
          <el-text size="small" type="info">Token: {{ token.substring(0, 20) }}...</el-text>
        </div>
      </div>
    </el-card>

    <!-- 遥测数据卡片 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="telemetry-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>无人机遥测</span>
              <el-icon><CaretTop /></el-icon>
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
                {{ telemetry.aircraft.voltage }}V
              </el-descriptions-item>
              <el-descriptions-item label="GPS">
                {{ telemetry.aircraft.gps || '未定位' }}
              </el-descriptions-item>
              <el-descriptions-item label="速度">
                {{ telemetry.aircraft.speed }} m/s
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
              <el-icon><CaretBottom /></el-icon>
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
                {{ telemetry.vehicle.voltage }}V
              </el-descriptions-item>
              <el-descriptions-item label="GPS">
                {{ telemetry.vehicle.gps || '未定位' }}
              </el-descriptions-item>
              <el-descriptions-item label="速度">
                {{ telemetry.vehicle.speed }} m/s
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 控制面板 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 无人机控制 -->
      <el-col :span="12">
        <el-card class="control-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>无人机控制</span>
              <el-icon><VideoPlay /></el-icon>
            </div>
          </template>
          
          <div class="control-content">
            <!-- 基础控制 -->
            <el-divider content-position="left">基础控制</el-divider>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-button 
                  type="success" 
                  @click="controlAircraft('TAKEOFF', 2000)"
                  :disabled="!isConnected"
                >
                  起飞
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button 
                  type="warning" 
                  @click="controlAircraft('LAND', 2000)"
                  :disabled="!isConnected"
                >
                  降落
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button 
                  type="info" 
                  @click="controlAircraft('BACK', 2000)"
                  :disabled="!isConnected"
                >
                  返航
                </el-button>
              </el-col>
            </el-row>
            
            <!-- 方向控制 -->
            <el-divider content-position="left">方向控制</el-divider>
            <div class="direction-control">
              <el-row :gutter="5">
                <el-col :span="6">
                  <el-button 
                    @mousedown="startControl('aircraft', 'AIRCRAFT_DIRECTION', 1000)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_DIRECTION')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_DIRECTION')"
                    :disabled="!isConnected"
                  >
                    左转
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('aircraft', 'AIRCRAFT_THROTTLE', 1600)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_THROTTLE')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_THROTTLE')"
                    :disabled="!isConnected"
                  >
                    前进
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('aircraft', 'AIRCRAFT_THROTTLE', 1400)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_THROTTLE')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_THROTTLE')"
                    :disabled="!isConnected"
                  >
                    后退
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('aircraft', 'AIRCRAFT_DIRECTION', 2000)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_DIRECTION')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_DIRECTION')"
                    :disabled="!isConnected"
                  >
                    右转
                  </el-button>
                </el-col>
              </el-row>

              <el-row :gutter="5" style="margin-top: 10px;">
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('aircraft', 'AIRCRAFT_MOVEMENT', 1400)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_MOVEMENT')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_MOVEMENT')"
                    :disabled="!isConnected"
                  >
                    左移
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('aircraft', 'AIRCRAFT_ALTITUDE', 1600)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_ALTITUDE')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_ALTITUDE')"
                    :disabled="!isConnected"
                  >
                    上升
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('aircraft', 'AIRCRAFT_ALTITUDE', 1400)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_ALTITUDE')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_ALTITUDE')"
                    :disabled="!isConnected"
                  >
                    下降
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('aircraft', 'AIRCRAFT_MOVEMENT', 1600)"
                    @mouseup="stopControl('aircraft', 'AIRCRAFT_MOVEMENT')"
                    @mouseleave="stopControl('aircraft', 'AIRCRAFT_MOVEMENT')"
                    :disabled="!isConnected"
                  >
                    右移
                  </el-button>
                </el-col>
              </el-row>
            </div>

            <!-- 云台控制 -->
            <el-divider content-position="left">云台控制</el-divider>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-button
                  @mousedown="startControl('aircraft', 'AIRCRAFT_GIMBAL_PITCH', 1400)"
                  @mouseup="stopControl('aircraft', 'AIRCRAFT_GIMBAL_PITCH')"
                  @mouseleave="stopControl('aircraft', 'AIRCRAFT_GIMBAL_PITCH')"
                  :disabled="!isConnected"
                >
                  云台下
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button
                  @mousedown="startControl('aircraft', 'AIRCRAFT_GIMBAL_PITCH', 1600)"
                  @mouseup="stopControl('aircraft', 'AIRCRAFT_GIMBAL_PITCH')"
                  @mouseleave="stopControl('aircraft', 'AIRCRAFT_GIMBAL_PITCH')"
                  :disabled="!isConnected"
                >
                  云台上
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button
                  type="info"
                  @click="controlAircraft('GIMBAL_RESET', 2000)"
                  :disabled="!isConnected"
                >
                  云台复位
                </el-button>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>

      <!-- 无人车控制 -->
      <el-col :span="12">
        <el-card class="control-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>无人车控制</span>
              <el-icon><Operation /></el-icon>
            </div>
          </template>

          <div class="control-content">
            <!-- 方向控制 -->
            <el-divider content-position="left">方向控制</el-divider>
            <div class="direction-control">
              <el-row :gutter="5">
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('vehicle', 'VEHICLE_DIRECTION', 1000)"
                    @mouseup="stopControl('vehicle', 'VEHICLE_DIRECTION')"
                    @mouseleave="stopControl('vehicle', 'VEHICLE_DIRECTION')"
                    :disabled="!isConnected"
                  >
                    左转
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('vehicle', 'VEHICLE_THROTTLE', 1700)"
                    @mouseup="stopControl('vehicle', 'VEHICLE_THROTTLE')"
                    @mouseleave="stopControl('vehicle', 'VEHICLE_THROTTLE')"
                    :disabled="!isConnected"
                  >
                    前进
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('vehicle', 'VEHICLE_THROTTLE', 1300)"
                    @mouseup="stopControl('vehicle', 'VEHICLE_THROTTLE')"
                    @mouseleave="stopControl('vehicle', 'VEHICLE_THROTTLE')"
                    :disabled="!isConnected"
                  >
                    后退
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button
                    @mousedown="startControl('vehicle', 'VEHICLE_DIRECTION', 2000)"
                    @mouseup="stopControl('vehicle', 'VEHICLE_DIRECTION')"
                    @mouseleave="stopControl('vehicle', 'VEHICLE_DIRECTION')"
                    :disabled="!isConnected"
                  >
                    右转
                  </el-button>
                </el-col>
              </el-row>
            </div>

            <!-- 图像抓拍 -->
            <el-divider content-position="left">图像抓拍</el-divider>
            <el-button
              type="primary"
              @click="captureImage"
              :loading="capturing"
              :disabled="!isConnected"
            >
              抓拍图像
            </el-button>

            <div class="captured-image" v-if="capturedImage">
              <el-image
                :src="capturedImage"
                fit="contain"
                style="width: 100%; max-height: 200px; margin-top: 10px;"
                :preview-src-list="[capturedImage]"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CaretTop,
  CaretBottom,
  VideoPlay,
  Operation
} from '@element-plus/icons-vue'
import {
  officialServerAPI,
  WebSocketManager,
  CONTROL_CHANNELS,
  CONTROL_VALUES
} from '@/services/officialAPI'

const token = ref('')
const isConnected = ref(false)
const connecting = ref(false)
const capturing = ref(false)
const capturedImage = ref('')
const wsManager = ref(null)
const controlTimers = reactive({})

const telemetry = reactive({
  aircraft: { power: 0, voltage: 0, gps: '', speed: 0 },
  vehicle: { power: 0, voltage: 0, gps: '', speed: 0 }
})

const connectionStatus = computed(() => {
  if (connecting.value) return { type: 'warning', text: '连接中...' }
  if (isConnected.value) return { type: 'success', text: '已连接' }
  return { type: 'danger', text: '未连接' }
})

const getPowerColor = (power) => {
  if (power > 50) return '#67c23a'
  if (power > 20) return '#e6a23c'
  return '#f56c6c'
}

const connectServer = async () => {
  try {
    connecting.value = true
    const serverToken = await officialServerAPI.getToken()
    token.value = serverToken
    localStorage.setItem('official_token', serverToken)

    wsManager.value = new WebSocketManager()

    wsManager.value.on('connected', () => {
      isConnected.value = true
      ElMessage.success('连接成功')
    })

    wsManager.value.on('disconnected', () => {
      isConnected.value = false
      ElMessage.warning('连接断开')
    })

    wsManager.value.on('aircraft_telemetry', (data) => {
      Object.assign(telemetry.aircraft, data)
    })

    wsManager.value.on('vehicle_telemetry', (data) => {
      Object.assign(telemetry.vehicle, data)
    })

    await wsManager.value.connect(serverToken)
  } catch (error) {
    ElMessage.error('连接失败: ' + error.message)
  } finally {
    connecting.value = false
  }
}

const disconnectServer = () => {
  if (wsManager.value) wsManager.value.disconnect()
  isConnected.value = false
  token.value = ''
  localStorage.removeItem('official_token')
  ElMessage.info('已断开连接')
}

// ✅ 已修复：直接使用完整通道名
const startControl = (target, channelName, value) => {
  if (!wsManager.value || !isConnected.value) return
  const channel = CONTROL_CHANNELS[channelName]
  const key = `${target}_${channelName}`

  if (controlTimers[key]) clearInterval(controlTimers[key])
  wsManager.value.sendControl(target, channel, value)

  controlTimers[key] = setInterval(() => {
    wsManager.value.sendControl(target, channel, value)
  }, 100)
}

const stopControl = (target, channelName) => {
  const key = `${target}_${channelName}`
  if (controlTimers[key]) {
    clearInterval(controlTimers[key])
    delete controlTimers[key]
  }
  if (wsManager.value && isConnected.value) {
    wsManager.value.sendControl(target, CONTROL_CHANNELS[channelName], CONTROL_VALUES.MID)
  }
}

const controlAircraft = (action, value) => {
  if (!wsManager.value) return
  const channel = CONTROL_CHANNELS[`AIRCRAFT_${action}`]
  wsManager.value.sendControl('aircraft', channel, value)
  ElMessage.success(`已执行：${action}`)
}

const captureImage = async () => {
  if (!token.value) return ElMessage.warning('请先连接')
  try {
    capturing.value = true
    const url = await officialServerAPI.captureImage(token.value)
    capturedImage.value = url
    ElMessage.success('抓拍成功')
  } catch (e) {
    ElMessage.error('抓拍失败：' + e.message)
  } finally {
    capturing.value = false
  }
}

onMounted(() => {
  const t = localStorage.getItem('official_token')
  if (t) token.value = t
})

onUnmounted(() => {
  Object.values(controlTimers).forEach(clearInterval)
  if (wsManager.value) wsManager.value.disconnect()
})
</script>

<style scoped>
.official-control { padding: 20px; }
.status-card, .telemetry-card, .control-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.token-info { margin-top: 15px; padding: 10px; background: #f5f7fa; border-radius: 4px; }
.el-button { width: 100%; margin-bottom: 5px; }
.captured-image { margin-top: 15px; }
</style>