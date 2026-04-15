<template>
  <div class="control-center">
    <h1>控制中心</h1>
    
    <!-- 连接状态管理 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="connection-card">
          <template #header>
            <div class="card-header">
              <span>连接状态管理</span>
            </div>
          </template>
          <div class="connection-content">
            <div class="connection-item">
              <h4>WebSocket连接</h4>
              <el-tag :type="wsStatus.type">{{ wsStatus.text }}</el-tag>
              <div class="connection-buttons">
                <el-button 
                  type="primary"
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

            <div class="connection-item">
              <h4>官方服务器连接</h4>
              <el-tag :type="officialStatus.type">{{ officialStatus.text }}</el-tag>
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
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备遥测数据 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="telemetry-card">
          <template #header>
            <div class="card-header">
              <span>无人机遥测</span>
              <el-tag :type="telemetry.aircraft.online ? 'success' : 'danger'">
                {{ telemetry.aircraft.online ? '在线' : '离线' }}
              </el-tag>
            </div>
          </template>
          <div class="telemetry-content">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="电量">
                <el-progress 
                  :percentage="telemetry.aircraft.power" 
                  :color="getPowerColor(telemetry.aircraft.power)"
                />
              </el-descriptions-item>
              <el-descriptions-item label="电压">
                {{ telemetry.aircraft.voltage ? telemetry.aircraft.voltage + 'V' : '--' }}
              </el-descriptions-item>
              <el-descriptions-item label="GPS">
                {{ telemetry.aircraft.gps || '未获取' }}
              </el-descriptions-item>
              <el-descriptions-item label="速度">
                {{ telemetry.aircraft.speed ? telemetry.aircraft.speed + 'm/s' : '--' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="telemetry-card">
          <template #header>
            <div class="card-header">
              <span>无人车遥测</span>
              <el-tag :type="telemetry.vehicle.online ? 'success' : 'danger'">
                {{ telemetry.vehicle.online ? '在线' : '离线' }}
              </el-tag>
            </div>
          </template>
          <div class="telemetry-content">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="电量">
                <el-progress 
                  :percentage="telemetry.vehicle.power" 
                  :color="getPowerColor(telemetry.vehicle.power)"
                />
              </el-descriptions-item>
              <el-descriptions-item label="电压">
                {{ telemetry.vehicle.voltage ? telemetry.vehicle.voltage + 'V' : '--' }}
              </el-descriptions-item>
              <el-descriptions-item label="GPS">
                {{ telemetry.vehicle.gps || '未获取' }}
              </el-descriptions-item>
              <el-descriptions-item label="速度">
                {{ telemetry.vehicle.speed ? telemetry.vehicle.speed + 'm/s' : '--' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { controlAPI } from '@/services/api'
import {
  officialServerAPI,
  WebSocketManager
} from '@/services/officialAPI'

// 响应式数据
const wsConnected = ref(false)
const officialConnected = ref(false)

// 加载状态
const loading = reactive({
  ws: {
    connect: false,
    disconnect: false
  },
  official: {
    connect: false
  }
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
  ElMessage.info('已断开官方服务器连接')
}

// 组件卸载时
onUnmounted(() => {
  // 断开连接
  if (wsManager.value) {
    wsManager.value.disconnect()
  }
})
</script>

<style scoped>
.control-center {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.connection-card, .telemetry-card {
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

.telemetry-content {
  padding: 10px 0;
}
</style>