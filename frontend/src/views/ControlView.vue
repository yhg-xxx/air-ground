<template>
  <div class="control-container">
    <el-row :gutter="20">
      <!-- 无人机控制 -->
      <el-col :span="12">
        <el-card class="control-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>无人机控制</span>
              <el-tag :type="wsConnected ? 'success' : 'danger'">
                {{ wsConnected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
          </template>
          
          <div class="control-content">
            <!-- 基础控制 -->
            <el-divider content-position="left">基础控制</el-divider>
            
            <el-row :gutter="10">
              <el-col :span="8">
                <el-button 
                  type="primary" 
                  @click="aircraftTakeoff"
                  :loading="loading.aircraft.takeoff"
                  class="control-btn"
                >
                  起飞
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button 
                  type="warning" 
                  @click="aircraftLand"
                  :loading="loading.aircraft.land"
                  class="control-btn"
                >
                  降落
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button 
                  type="info" 
                  @click="aircraftBack"
                  :loading="loading.aircraft.back"
                  class="control-btn"
                >
                  返航
                </el-button>
              </el-col>
            </el-row>
            
            <!-- 方向控制 -->
            <el-divider content-position="left">方向控制</el-divider>
            
            <div class="direction-control">
              <el-row :gutter="5" justify="center">
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @click="aircraftControl('throttle', 2000)"
                    @mouseup="aircraftControl('throttle', 1500)"
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
                    @click="aircraftControl('direction', 1000)"
                    @mouseup="aircraftControl('direction', 1500)"
                    class="direction-btn"
                  >
                    左转
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="success" 
                    @click="aircraftControl('altitude', 2000)"
                    @mouseup="aircraftControl('altitude', 1500)"
                    class="direction-btn"
                  >
                    上升
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @click="aircraftControl('direction', 2000)"
                    @mouseup="aircraftControl('direction', 1500)"
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
                    @click="aircraftControl('movement', 1000)"
                    @mouseup="aircraftControl('movement', 1500)"
                    class="direction-btn"
                  >
                    左移
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="warning" 
                    @click="aircraftControl('throttle', 1000)"
                    @mouseup="aircraftControl('throttle', 1500)"
                    class="direction-btn"
                  >
                    后退
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @click="aircraftControl('movement', 2000)"
                    @mouseup="aircraftControl('movement', 1500)"
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
                    @click="aircraftControl('altitude', 1000)"
                    @mouseup="aircraftControl('altitude', 1500)"
                    class="direction-btn"
                  >
                    下降
                  </el-button>
                </el-col>
              </el-row>
            </div>
            
            <!-- 云台控制 -->
            <el-divider content-position="left">云台控制</el-divider>
            
            <el-row :gutter="10">
              <el-col :span="8">
                <el-button 
                  type="info" 
                  @click="aircraftControl('gimbal_pitch', 1000)"
                  @mouseup="aircraftControl('gimbal_pitch', 1500)"
                  class="gimbal-btn"
                >
                  俯仰下
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button 
                  type="warning" 
                  @click="aircraftControl('gimbal_reset', 2000)"
                  :loading="loading.aircraft.gimbal_reset"
                  class="gimbal-btn"
                >
                  云台复位
                </el-button>
              </el-col>
              <el-col :span="8">
                <el-button 
                  type="info" 
                  @click="aircraftControl('gimbal_pitch', 2000)"
                  @mouseup="aircraftControl('gimbal_pitch', 1500)"
                  class="gimbal-btn"
                >
                  俯仰上
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
              <el-tag :type="wsConnected ? 'success' : 'danger'">
                {{ wsConnected ? '已连接' : '未连接' }}
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
                    @click="vehicleControl('throttle', 2000)"
                    @mouseup="vehicleControl('throttle', 1500)"
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
                    @click="vehicleControl('direction', 1000)"
                    @mouseup="vehicleControl('direction', 1500)"
                    class="direction-btn large"
                  >
                    左转
                  </el-button>
                </el-col>
                <el-col :span="8">
                  <el-button 
                    type="warning" 
                    @click="vehicleControl('throttle', 1000)"
                    @mouseup="vehicleControl('throttle', 1500)"
                    class="direction-btn large"
                  >
                    后退
                  </el-button>
                </el-col>
                <el-col :span="8">
                  <el-button 
                    type="primary" 
                    @click="vehicleControl('direction', 2000)"
                    @mouseup="vehicleControl('direction', 1500)"
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
    </el-row>
    
    <!-- 连接控制 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card class="connection-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>连接控制</span>
            </div>
          </template>
          
          <div class="connection-content">
            <el-button 
              type="success" 
              @click="connectWebSocket"
              :loading="loading.connect"
              size="large"
            >
              连接WebSocket
            </el-button>
            
            <el-button 
              type="danger" 
              @click="disconnectWebSocket"
              :loading="loading.disconnect"
              size="large"
            >
              断开连接
            </el-button>
            
            <el-button 
              type="info" 
              @click="refreshStatus"
              :loading="loading.status"
              size="large"
            >
              刷新状态
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 遥测数据 -->
    <el-row :gutter="20" style="margin-top: 20px;">
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
            <el-descriptions :column="1" border>
              <el-descriptions-item label="电量">
                <el-tag :type="telemetry.aircraft.power > 0.5 ? 'success' : 'warning'">
                  {{ telemetry.aircraft.power !== null ? telemetry.aircraft.power + '%' : '--' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="电压">
                {{ telemetry.aircraft.voltage !== null ? telemetry.aircraft.voltage + 'V' : '--' }}
              </el-descriptions-item>
              <el-descriptions-item label="GPS坐标">
                {{ telemetry.aircraft.gps ? telemetry.aircraft.gps.join(', ') : '--' }}
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
            <el-descriptions :column="1" border>
              <el-descriptions-item label="电量">
                <el-tag :type="telemetry.vehicle.power > 0.5 ? 'success' : 'warning'">
                  {{ telemetry.vehicle.power !== null ? telemetry.vehicle.power + '%' : '--' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="电压">
                {{ telemetry.vehicle.voltage !== null ? telemetry.vehicle.voltage + 'V' : '--' }}
              </el-descriptions-item>
              <el-descriptions-item label="GPS坐标">
                {{ telemetry.vehicle.gps ? telemetry.vehicle.gps.join(', ') : '--' }}
              </el-descriptions-item>
              <el-descriptions-item label="速度">
                {{ telemetry.vehicle.speed !== null ? telemetry.vehicle.speed + ' m/s' : '--' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { controlAPI } from '@/services/api'

// 响应式数据
const wsConnected = ref(false)
const telemetry = ref({
  aircraft: {
    online: false,
    power: null,
    voltage: null,
    gps: null,
    speed: null
  },
  vehicle: {
    online: false,
    power: null,
    voltage: null,
    gps: null,
    speed: null
  }
})
const loading = ref({
  connect: false,
  disconnect: false,
  status: false,
  aircraft: {
    takeoff: false,
    land: false,
    back: false,
    gimbal_reset: false
  }
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

// 连接WebSocket
const connectWebSocket = async () => {
  loading.value.connect = true
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
    loading.value.connect = false
  }
}

// 断开WebSocket
const disconnectWebSocket = async () => {
  loading.value.disconnect = true
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
    loading.value.disconnect = false
  }
}

// 刷新状态
const refreshStatus = async () => {
  loading.value.status = true
  try {
    const response = await controlAPI.getStatus()
    if (response.code === '1') {
      wsConnected.value = response.data.websocket_connected
      ElMessage.success('状态刷新成功')
    } else {
      ElMessage.error(response.msg || '获取状态失败')
    }
  } catch (error) {
    console.error('获取状态失败:', error)
    ElMessage.error('获取状态失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value.status = false
  }
}

// 无人机控制
const aircraftControl = async (controlType, value) => {
  if (!wsConnected.value) {
    ElMessage.warning('WebSocket未连接')
    return
  }
  
  const channel = aircraftChannels[controlType]
  if (!channel) {
    ElMessage.error(`未知的控制类型: ${controlType}`)
    return
  }
  
  try {
    await controlAPI.controlAircraft(channel, value)
  } catch (error) {
    console.error('无人机控制失败:', error)
    ElMessage.error('控制失败: ' + (error.message || '网络错误'))
  }
}

// 无人车控制
const vehicleControl = async (controlType, value) => {
  if (!wsConnected.value) {
    ElMessage.warning('WebSocket未连接')
    return
  }
  
  const channel = vehicleChannels[controlType]
  if (!channel) {
    ElMessage.error(`未知的控制类型: ${controlType}`)
    return
  }
  
  try {
    await controlAPI.controlVehicle(channel, value)
  } catch (error) {
    console.error('无人车控制失败:', error)
    ElMessage.error('控制失败: ' + (error.message || '网络错误'))
  }
}

// 无人机特殊动作
const aircraftTakeoff = async () => {
  loading.value.aircraft.takeoff = true
  try {
    await controlAPI.controlAircraft(aircraftChannels.takeoff, 2000)
    ElMessage.success('起飞指令发送成功')
  } catch (error) {
    console.error('起飞失败:', error)
    ElMessage.error('起飞失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value.aircraft.takeoff = false
  }
}

const aircraftLand = async () => {
  loading.value.aircraft.land = true
  try {
    await controlAPI.controlAircraft(aircraftChannels.land, 2000)
    ElMessage.success('降落指令发送成功')
  } catch (error) {
    console.error('降落失败:', error)
    ElMessage.error('降落失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value.aircraft.land = false
  }
}

const aircraftBack = async () => {
  loading.value.aircraft.back = true
  try {
    await controlAPI.controlAircraft(aircraftChannels.back, 2000)
    ElMessage.success('返航指令发送成功')
  } catch (error) {
    console.error('返航失败:', error)
    ElMessage.error('返航失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value.aircraft.back = false
  }
}

// 组件挂载时获取状态
onMounted(() => {
  refreshStatus()
})
</script>

<style scoped>
.control-container {
  padding: 20px;
}

.control-card {
  height: fit-content;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}

.control-content {
  padding: 10px 0;
}

.control-btn {
  width: 100%;
  margin-bottom: 10px;
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

.connection-card {
  text-align: center;
}

.connection-content {
  padding: 20px 0;
}

.connection-content .el-button {
  margin: 0 10px;
  width: 150px;
  height: 50px;
}

.telemetry-card {
  height: fit-content;
}

.telemetry-content {
  padding: 10px 0;
}

/* 按钮按下效果 */
.el-button:active {
  transform: scale(0.95);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .direction-btn {
    width: 60px;
    height: 35px;
    font-size: 12px;
  }
  
  .direction-btn.large {
    width: 80px;
    height: 40px;
  }
  
  .connection-content .el-button {
    width: 120px;
    height: 40px;
    margin: 5px;
  }
}
</style>
