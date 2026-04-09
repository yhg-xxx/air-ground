import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response.data
  },
  error => {
    // 对响应错误做点什么
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// 认证相关API
export const authAPI = {
  // 获取Token
  getToken: () => {
    return api.post('/api/auth/token')
  },
  
  // 设置前端Token
  setFrontendToken: (token, expiresIn = 7200) => {
    return api.post('/api/auth/token/frontend', {
      token,
      expires_in: expiresIn
    })
  }
}

// 云台相关API
export const gimbalAPI = {
  // 抓拍图像
  captureImage: () => {
    return api.post('/api/gimbal/capture', {}, {
      responseType: 'blob'
    })
  }
}

// 系统相关API
export const systemAPI = {
  // 健康检查
  healthCheck: () => {
    return api.get('/api/health')
  }
}

// 控制相关API
export const controlAPI = {
  // 连接WebSocket
  connect: () => {
    return api.post('/api/control/connect')
  },
  
  // 断开WebSocket
  disconnect: () => {
    return api.post('/api/control/disconnect')
  },
  
  // 获取控制状态
  getStatus: () => {
    return api.get('/api/control/status')
  },
  
  // 无人机控制
  controlAircraft: (channel, value) => {
    return api.post('/api/control/aircraft', {}, {
      params: { channel, value }
    })
  },
  
  // 无人车控制
  controlVehicle: (channel, value) => {
    return api.post('/api/control/vehicle', {}, {
      params: { channel, value }
    })
  },
  
  // 通用控制
  controlUniversal: (target, channel, value) => {
    return api.post('/api/control/universal', {
      target,
      channel,
      value
    })
  }
}

// 降落相关API
export const landingAPI = {
  // 开始降落过程
  startLanding: (targetArucoId = 0) => {
    return api.post('/api/landing/start', {}, {
      params: { target_aruco_id: targetArucoId }
    })
  },
  
  // 获取降落状态
  getLandingStatus: () => {
    return api.get('/api/landing/status')
  },
  
  // 取消降落过程
  cancelLanding: () => {
    return api.post('/api/landing/cancel')
  }
}

export default api
