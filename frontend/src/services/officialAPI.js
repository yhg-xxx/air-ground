import axios from 'axios'

// ===================== 官方配置 =====================
const HOST = "fcs.botzooo.com"
const PORT = 30080
const WS_HOST = "fcs.botzooo.com"
const WS_PORT = 30081
const USERNAME = "fcs002"
const PASSWORD = "wa729461"

const MAX = 2000
const MIN = 1000
const MID = 1500
const MIN_INTERVAL = 0.1

// axios 代理配置
const officialAPI = axios.create({
  baseURL: '/api',  // 使用相对路径，通过vite代理
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 官方服务器API
export const officialServerAPI = {
  // 获取Token
  getToken: async () => {
    try {
      const response = await officialAPI.post('/auth/token', {
        username: USERNAME,
        password: PASSWORD
      })
      if (response.data.code === "1") {
        return response.data.data.token
      } else {
        throw new Error("获取Token失败：" + response.data.msg)
      }
    } catch (error) {
      throw new Error("获取Token失败：" + error.message)
    }
  },

  // 抓拍图像
  captureImage: async (token) => {
    try {
      const response = await officialAPI.post('/gimbal/capture', {}, {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob',
        timeout: 60000
      })

      if (response.headers["content-type"]?.includes("image")) {
        const blob = new Blob([response.data], { type: 'image/jpeg' })
        return URL.createObjectURL(blob)
      } else {
        throw new Error("抓拍失败：返回的不是图像数据")
      }
    } catch (error) {
      throw new Error("抓拍失败：" + error.message)
    }
  },

  // 开始降落
  startLanding: async (targetArucoId = 0) => {
    try {
      const response = await officialAPI.post('/landing/start', {
        target_aruco_id: targetArucoId
      })
      return response.data
    } catch (error) {
      throw new Error("开始降落失败：" + error.message)
    }
  },

  // 获取降落状态
  getLandingStatus: async () => {
    try {
      const response = await officialAPI.get('/landing/status')
      return response.data
    } catch (error) {
      throw new Error("获取降落状态失败：" + error.message)
    }
  },

  // 取消降落
  cancelLanding: async () => {
    try {
      const response = await officialAPI.post('/landing/cancel')
      return response.data
    } catch (error) {
      throw new Error("取消降落失败：" + error.message)
    }
  }
}

// WebSocket连接管理（完全按照官方文档实现）
export class WebSocketManager {
  constructor() {
    this.ws = null
    this.isConnected = false
    this.token = null
    this.reconnectTimer = null
    this.messageHandlers = new Map()

    this.telemetryData = {
      aircraft: { power: 0, voltage: 0, gps: '', speed: 0 },
      vehicle: { power: 0, voltage: 0, gps: '', speed: 0 }
    }
  }

  async connect(token) {
    try {
      // 避免重复连接
      if (this.isConnected && this.ws) {
        console.log('WebSocket已经连接，无需重复连接')
        return
      }
      
      this.token = token
      // 使用相对路径的WebSocket连接，通过vite代理
      const wsUrl = `ws://localhost:5174/ws?token=${token}`
      console.log('正在连接WebSocket:', wsUrl)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket连接成功')
        this.isConnected = true
        this.emit('connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket连接关闭:', event.code, event.reason)
        this.isConnected = false
        this.emit('disconnected')
        // 只有在正常关闭时才重连
        if (event.code !== 1000) {
          this.autoReconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        this.emit('error', error)
      }

    } catch (error) {
      console.error('WebSocket连接失败:', error)
      throw new Error('WebSocket连接失败: ' + error.message)
    }
  }

  handleMessage(data) {
    const type = data.type

    switch (type) {
      case "auth_success":
        console.log('✅ WebSocket认证成功')
        this.emit('auth_success')
        break
      case "ping":
        // 官方文档：服务端心跳，客户端无需回复！
        console.log('❤️ 收到服务端心跳')
        break
      case "aircraft_telemetry_power":
        this.telemetryData.aircraft.power = data.data.power
        this.telemetryData.aircraft.voltage = data.data.voltage
        this.emit('aircraft_telemetry', this.telemetryData.aircraft)
        break
      case "aircraft_telemetry_gnss":
        this.telemetryData.aircraft.gps = data.data.gps
        this.telemetryData.aircraft.speed = data.data.speed
        this.emit('aircraft_telemetry', this.telemetryData.aircraft)
        break
      case "vehicle_telemetry_power":
        this.telemetryData.vehicle.power = data.data.power
        this.telemetryData.vehicle.voltage = data.data.voltage
        this.emit('vehicle_telemetry', this.telemetryData.vehicle)
        break
      case "vehicle_telemetry_gnss":
        this.telemetryData.vehicle.gps = data.data.gps
        this.telemetryData.vehicle.speed = data.data.speed
        this.emit('vehicle_telemetry', this.telemetryData.vehicle)
        break
      case "vehicle_safety_fence_over":
        console.warn("⚠️ 车辆超出围栏")
        break
      case "aircraft_safety_fence_over":
        console.warn("⚠️ 无人机超出围栏")
        break
      default:
        this.emit('message', data)
    }
  }

  // 发送控制指令（官方标准格式）
  sendControl(target, channel, value) {
    if (!this.isConnected || !this.ws) return

    const message = {
      type: "control",
      target: target,
      channel: channel,
      value: value
    }

    this.ws.send(JSON.stringify(message))
    console.log(`[${target}] 通道${channel} → ${value}`)
  }

  // 事件系统
  on(event, callback) {
    if (!this.messageHandlers.has(event)) this.messageHandlers.set(event, [])
    this.messageHandlers.get(event).push(callback)
  }

  off(event, callback) {
    if (this.messageHandlers.has(event)) {
      const handlers = this.messageHandlers.get(event)
      const index = handlers.indexOf(callback)
      if (index > -1) handlers.splice(index, 1)
    }
  }

  emit(event, data) {
    if (this.messageHandlers.has(event)) {
      this.messageHandlers.get(event).forEach(callback => {
        try { callback(data) } catch (e) {}
      })
    }
  }

  // 自动重连
  autoReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.reconnectTimer = setTimeout(() => {
      if (this.token) this.connect(this.token)
    }, 2000)
  }

  // 断开连接
  disconnect() {
    if (this.ws) this.ws.close()
    this.isConnected = false
  }

  getTelemetryData() {
    return this.telemetryData
  }
}

// 官方通道定义（100% 匹配文档）
// 车辆：通道1=转向（左转2000,右转1000） 通道2=油门（前进2000,后退1000）
export const CONTROL_CHANNELS = {
  // 车辆通道
  VEHICLE_STEERING: 1,     // 转向：左转=2000, 中=1500, 右转=1000
  VEHICLE_THROTTLE: 2,     // 油门：前进=2000, 中=1500, 后退=1000

  // 无人机通道
  AIRCRAFT_DIRECTION: 1,     // 左转右转
  AIRCRAFT_ALTITUDE: 2,      // 上升下降
  AIRCRAFT_MOVEMENT: 3,      // 左移右移
  AIRCRAFT_THROTTLE: 4,      // 前进后退
  AIRCRAFT_GIMBAL_PITCH: 5,  // 云台俯仰
  AIRCRAFT_GIMBAL_ROLL: 6,   // 云台横滚
  AIRCRAFT_TAKEOFF: 7,       // 起飞
  AIRCRAFT_LAND: 8,          // 降落
  AIRCRAFT_BACK: 9,          // 返航
  AIRCRAFT_GIMBAL_RESET: 10  // 云台复位
}

export const CONTROL_VALUES = {
  MAX: 2000,
  MIN: 1000,
  MID: 1500
}

export default officialServerAPI