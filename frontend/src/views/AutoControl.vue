<template>
  <div class="auto-control">
    <!-- 顶部标题栏 -->
    <div class="header-bar">
      <div class="title-section">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <div class="title-text">
          <h1>融瓴机器人联盟・空陆协同竞速挑战赛</h1>
          <span class="subtitle">Air-Ground Collaborative Racing System</span>
        </div>
      </div>
      
      <div class="status-section">
        <div class="mode-indicator" :class="{ active: isAutoMode }">
          <span class="mode-dot"></span>
          <span>{{ isAutoMode ? '自主模式' : '待机模式' }}</span>
        </div>
        <div class="time-display">
          <span class="time-label">任务用时</span>
          <span class="time-value">{{ formatTime(elapsedTime) }}</span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 左侧：任务流程 -->
      <div class="left-panel">
        <div class="panel-card mission-flow">
          <div class="panel-header">
            <span class="panel-icon">🎯</span>
            <span>自动化任务流程</span>
            <div class="flow-progress">
              <span>{{ completedSteps }}/{{ totalSteps }}</span>
            </div>
          </div>
          
          <div class="mission-steps">
            <div 
              v-for="(step, index) in missionSteps" 
              :key="step.id"
              class="mission-step"
              :class="{ 
                'completed': step.status === 'completed',
                'active': step.status === 'active',
                'pending': step.status === 'pending',
                'error': step.status === 'error'
              }"
            >
              <div class="step-connector" v-if="index > 0"></div>
              <div class="step-indicator">
                <span v-if="step.status === 'completed'" class="check-icon">✓</span>
                <span v-else-if="step.status === 'active'" class="loading-icon"></span>
                <span v-else-if="step.status === 'error'" class="error-icon">!</span>
                <span v-else class="step-number">{{ index + 1 }}</span>
              </div>
              <div class="step-content">
                <div class="step-title">{{ step.title }}</div>
                <div class="step-desc">{{ step.description }}</div>
                <div v-if="step.status === 'active'" class="step-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: step.progress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ step.progress }}%</span>
                </div>
              </div>
              <div class="step-time" v-if="step.time">{{ step.time }}</div>
            </div>
          </div>
        </div>

        <!-- AI决策日志 -->
        <div class="panel-card ai-log">
          <div class="panel-header">
            <span class="panel-icon">🤖</span>
            <span>AI决策日志</span>
            <span class="log-count">{{ aiLogs.length }}</span>
          </div>
          <div class="log-container">
            <div 
              v-for="log in aiLogs.slice(-8)" 
              :key="log.id" 
              class="log-item"
              :class="log.type"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-tag">{{ log.tag }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：视觉识别与路径规划 -->
      <div class="center-panel">
        <!-- 无人机视角 -->
        <div class="panel-card vision-panel">
          <div class="panel-header">
            <span class="panel-icon">📷</span>
            <span>无人机视觉 - AI图像分析</span>
            <div class="vision-controls">
              <button class="capture-btn" @click="captureImage" :disabled="isCapturing">
                <span v-if="isCapturing">📸</span>
                <span v-else>📷</span>
                {{ isCapturing ? '抓拍中...' : '抓拍' }}
              </button>
              <div class="fps-indicator">
                <span class="fps-value">{{ fps }}</span>
                <span class="fps-label">FPS</span>
              </div>
            </div>
          </div>
          
          <div class="vision-container">
            <div class="video-frame" :class="{ analyzing: isAnalyzing }">
              <img v-if="capturedImage" :src="capturedImage" alt="无人机视角" />
              <div v-else class="video-placeholder">
                <div class="placeholder-icon">�</div>
                <span>未抓拍图像</span>
              </div>
              
              <!-- AI识别覆盖层 -->
              <div class="ai-overlay" v-if="aiDetections.length > 0">
                <div 
                  v-for="det in aiDetections" 
                  :key="det.id"
                  class="detection-box"
                  :class="det.type"
                  :style="getDetectionStyle(det)"
                >
                  <span class="det-label">{{ det.label }}</span>
                  <span class="det-conf">{{ det.confidence }}%</span>
                </div>
              </div>
              
              <!-- 分析状态指示 -->
              <div class="analysis-indicator" v-if="isAnalyzing">
                <div class="scan-line"></div>
                <span>AI图像分析中...</span>
              </div>
            </div>
            
            <div class="vision-info">
              <div class="info-item">
                <span class="info-label">检测目标</span>
                <span class="info-value">{{ aiDetections.length }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">障碍物</span>
                <span class="info-value obstacle">{{ obstacleCount }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">拱门</span>
                <span class="info-value gate">{{ gateCount }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">ArUco</span>
                <span class="info-value aruco">{{ arucoDetected ? '已识别' : '搜索中' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 迷宫地图与路径规划 -->
        <div class="panel-card map-panel">
          <div class="panel-header">
            <span class="panel-icon">🗺️</span>
            <span>迷宫地图 - 路径规划</span>
            <div class="map-actions">
              <button class="action-btn" @click="refreshMap">
                <span>🔄</span>
              </button>
            </div>
          </div>
          
          <div class="map-container">
            <div class="maze-grid">
              <!-- 迷宫可视化 -->
              <svg viewBox="0 0 500 400" class="maze-svg">
                <!-- 背景网格 -->
                <defs>
                  <pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">
                    <path d="M 25 0 L 0 0 0 25" fill="none" stroke="rgba(59,130,246,0.1)" stroke-width="1"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)"/>
                
                <!-- 迷宫区域标识 -->
                <rect x="0" y="0" :width="DISPLAY_W" :height="DISPLAY_H * 0.15" 
                  fill="rgba(16,185,129,0.1)" stroke="none"/>
                <text x="250" y="25" text-anchor="middle" fill="#10b981" font-size="11">终点区域</text>
                
                <rect x="0" :y="DISPLAY_H * 0.7" :width="DISPLAY_W" :height="DISPLAY_H * 0.3" 
                  fill="rgba(59,130,246,0.1)" stroke="none"/>
                <text x="250" :y="DISPLAY_H * 0.75" text-anchor="middle" fill="#3b82f6" font-size="11">起点区域 · 迷宫穿越区 (17m×44m)</text>
                
                <!-- 迷宫墙壁（使用线段渲染） -->
                <g class="maze-walls">
                  <line v-for="(wall, idx) in mazeWalls" :key="'wall-' + idx"
                    :x1="scaleX(wall.x1)" :y1="scaleY(wall.y1)"
                    :x2="scaleX(wall.x2)" :y2="scaleY(wall.y2)"
                    stroke="#475569" stroke-width="3" stroke-linecap="round"/>
                </g>
                
                <!-- 拱门标记 -->
                <g v-for="gate in gates" :key="'gate-' + gate.id">
                  <rect :x="gate.x" :y="gate.y" :width="gate.w" :height="gate.h"
                    fill="rgba(16,185,129,0.2)" stroke="#10b981" stroke-width="2" 
                    :stroke-dasharray="gate.id === 9 ? '0' : '5,3'" rx="3"/>
                  <circle :cx="gate.x + gate.w/2" :cy="gate.y + gate.h/2" r="8"
                    fill="#10b981" opacity="0.8"/>
                  <text :x="gate.x + gate.w/2" :y="gate.y + gate.h/2 + 4" 
                    text-anchor="middle" fill="white" font-size="9" font-weight="bold">{{ gate.id }}</text>
                  <text :x="gate.x + gate.w/2" :y="gate.y - 5" 
                    text-anchor="middle" fill="#10b981" font-size="9">{{ gate.name }}</text>
                </g>
                
                <!-- 无人机飞行路径 -->
                <path v-if="plannedPath" 
                  :d="plannedPath" 
                  fill="none" 
                  stroke="#3b82f6" 
                  stroke-width="3"
                  stroke-dasharray="8,4"
                  class="path-animation"/>
                
                <!-- 小车迷宫路径 -->
                <path v-if="carPlannedPath" 
                  :d="carPlannedPath" 
                  fill="none" 
                  stroke="#f59e0b" 
                  stroke-width="2.5"
                  stroke-dasharray="6,3"
                  class="car-path-animation"/>
                
                <!-- 无人机位置 -->
                <g :transform="`translate(${dronePos.x}, ${dronePos.y})`" class="drone-marker">
                  <circle r="12" fill="#3b82f6" opacity="0.3"/>
                  <circle r="8" fill="#3b82f6"/>
                  <text y="4" text-anchor="middle" fill="white" font-size="10">✈</text>
                </g>
                
                <!-- 无人车位置 -->
                <g :transform="`translate(${carPos.x}, ${carPos.y})`" class="car-marker">
                  <circle r="10" fill="#10b981" opacity="0.3"/>
                  <circle r="6" fill="#10b981"/>
                  <text y="3" text-anchor="middle" fill="white" font-size="8">🚗</text>
                </g>
                
                <!-- 起点标记 -->
                <g :transform="`translate(${scaleX(startPoint.gridX)}, ${scaleY(startPoint.gridY)})`">
                  <circle r="12" fill="rgba(59,130,246,0.3)"/>
                  <circle r="6" fill="#3b82f6"/>
                  <text y="-15" text-anchor="middle" fill="#3b82f6" font-size="10">起点</text>
                </g>
                
                <!-- 终点标记 -->
                <g :transform="`translate(${scaleX(endPoint.gridX)}, ${scaleY(endPoint.gridY)})`">
                  <circle r="12" fill="rgba(245,158,11,0.3)"/>
                  <circle r="6" fill="#f59e0b"/>
                  <text y="-15" text-anchor="middle" fill="#f59e0b" font-size="10">🏁 终点</text>
                </g>
              </svg>
            </div>
            
            <div class="map-legend">
              <div class="legend-item"><span class="legend-color drone"></span>无人机</div>
              <div class="legend-item"><span class="legend-color car"></span>无人车</div>
              <div class="legend-item"><span class="legend-color gate"></span>拱门(9个)</div>
              <div class="legend-item"><span class="legend-color wall"></span>迷宫墙</div>
              <div class="legend-item"><span class="legend-color path"></span>无人机路径</div>
              <div class="legend-item"><span class="legend-color car-path"></span>小车路径</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：设备状态与控制 -->
      <div class="right-panel">
        <!-- 设备状态卡片 -->
        <div class="panel-card device-status">
          <div class="panel-header">
            <span class="panel-icon">📊</span>
            <span>设备状态</span>
          </div>
          
          <div class="device-cards">
            <!-- 无人机状态 -->
            <div class="device-card drone">
              <div class="device-header">
                <span class="device-icon">✈️</span>
                <span class="device-name">无人机</span>
                <span class="device-state" :class="droneState">{{ droneStateText }}</span>
              </div>
              <div class="device-stats">
                <div class="stat-item">
                  <span class="stat-label">电量</span>
                  <div class="stat-bar">
                    <div class="stat-fill battery" :style="{ width: droneBattery + '%' }"></div>
                  </div>
                  <span class="stat-value">{{ droneBattery }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">高度</span>
                  <span class="stat-value">{{ droneAltitude }}m</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">速度</span>
                  <span class="stat-value">{{ droneSpeed }}m/s</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">信号</span>
                  <div class="signal-bars">
                    <span v-for="i in 4" :key="i" class="signal-bar" :class="{ active: i <= signalStrength }"></span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 无人车状态 -->
            <div class="device-card car">
              <div class="device-header">
                <span class="device-icon">🚗</span>
                <span class="device-name">无人车</span>
                <span class="device-state" :class="carState">{{ carStateText }}</span>
              </div>
              <div class="device-stats">
                <div class="stat-item">
                  <span class="stat-label">电量</span>
                  <div class="stat-bar">
                    <div class="stat-fill battery" :style="{ width: carBattery + '%' }"></div>
                  </div>
                  <span class="stat-value">{{ carBattery }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">速度</span>
                  <span class="stat-value">{{ carSpeed }}m/s</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">航向</span>
                  <span class="stat-value">{{ carHeading }}°</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 精准降落模块 -->
        <div class="panel-card landing-module">
          <div class="panel-header">
            <span class="panel-icon">🎯</span>
            <span>精准降落引导</span>
          </div>
          
          <div class="landing-content">
            <div class="landing-visual">
              <div class="target-circle outer">
                <div class="target-circle middle">
                  <div class="target-circle inner">
                    <div class="target-crosshair"></div>
                  </div>
                </div>
              </div>
              <div class="drone-indicator" :style="getLandingIndicatorStyle()">
                <span>✈</span>
              </div>
            </div>
            
            <div class="landing-info">
              <div class="info-row">
                <span class="info-label">ArUco ID</span>
                <span class="info-value">{{ targetArucoId }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">偏移X</span>
                <span class="info-value" :class="getOffsetClass(landingOffsetX)">{{ landingOffsetX }}cm</span>
              </div>
              <div class="info-row">
                <span class="info-label">偏移Y</span>
                <span class="info-value" :class="getOffsetClass(landingOffsetY)">{{ landingOffsetY }}cm</span>
              </div>
              <div class="info-row">
                <span class="info-label">降落状态</span>
                <span class="info-value" :class="landingState">{{ landingStateText }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 控制按钮 -->
        <div class="panel-card control-buttons">
          <div class="panel-header">
            <span class="panel-icon">🎮</span>
            <span>任务控制</span>
          </div>
          
          <div class="button-grid">
            <button class="ctrl-btn primary" @click="startMission" :disabled="isAutoMode">
              <span class="btn-icon">▶</span>
              <span class="btn-text">开始任务</span>
            </button>
            <button class="ctrl-btn warning" @click="pauseMission" :disabled="!isAutoMode">
              <span class="btn-icon">⏸</span>
              <span class="btn-text">暂停</span>
            </button>
            <button class="ctrl-btn danger" @click="emergencyStop">
              <span class="btn-icon">🛑</span>
              <span class="btn-text">紧急停止</span>
            </button>
            <button class="ctrl-btn info" @click="resetMission">
              <span class="btn-icon">🔄</span>
              <span class="btn-text">重置任务</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { officialServerAPI, WebSocketManager } from '../services/officialAPI'

// 状态变量
const isAutoMode = ref(false)
const elapsedTime = ref(0)
const fps = ref(24)
const isAnalyzing = ref(true)
const capturedImage = ref(null)
const isCapturing = ref(false)

// 任务步骤
const missionSteps = ref([
  { id: 1, title: '系统初始化', description: '连接设备，校准传感器', status: 'completed', progress: 100, time: '00:03' },
  { id: 2, title: '无人机起飞', description: '垂直起飞至观测高度', status: 'completed', progress: 100, time: '00:08' },
  { id: 3, title: '迷宫侦查', description: 'AI视觉扫描迷宫结构', status: 'active', progress: 67, time: '' },
  { id: 4, title: '路径规划', description: '计算最优穿越路径', status: 'pending', progress: 0, time: '' },
  { id: 5, title: '拱门穿越', description: '无人机精准穿越障碍', status: 'pending', progress: 0, time: '' },
  { id: 6, title: '协同引导', description: '引导无人车穿越迷宫', status: 'pending', progress: 0, time: '' },
  { id: 7, title: '精准降落', description: '降落至无人车指定区域', status: 'pending', progress: 0, time: '' },
  { id: 8, title: '冲刺终点', description: '无人车携带无人机冲线', status: 'pending', progress: 0, time: '' }
])

const completedSteps = computed(() => missionSteps.value.filter(s => s.status === 'completed').length)
const totalSteps = computed(() => missionSteps.value.length)

// AI识别数据 - 基于真实拱门位置动态生成
const aiDetections = computed(() => {
  const detections = []
  // 当前穿越的拱门
  const currentGate = realGates[currentWaypointIndex.value]
  if (currentGate && currentWaypointIndex.value < 8) {
    detections.push({
      id: 1,
      type: 'gate',
      label: currentGate.name,
      confidence: 96 + Math.floor(Math.random() * 4),
      x: 35, y: 30, w: 30, h: 40
    })
  }
  // ArUco码检测（降落阶段）
  if (currentWaypointIndex.value >= 7) {
    detections.push({
      id: 2,
      type: 'aruco',
      label: `ArUco #${targetArucoId.value}`,
      confidence: 99,
      x: 45, y: 55, w: 15, h: 15
    })
  }
  return detections
})

const obstacleCount = computed(() => aiDetections.value.filter(d => d.type === 'obstacle').length)
const gateCount = computed(() => aiDetections.value.filter(d => d.type === 'gate').length)
const arucoDetected = computed(() => aiDetections.value.some(d => d.type === 'aruco'))

// AI日志
const aiLogs = ref([
  { id: 1, time: '14:23:01', tag: 'INIT', type: 'info', message: '系统初始化完成' },
  { id: 2, time: '14:23:05', tag: 'DRONE', type: 'success', message: '无人机已连接，电量92%' },
  { id: 3, time: '14:23:06', tag: 'CAR', type: 'success', message: '无人车已连接，电量88%' },
  { id: 4, time: '14:23:10', tag: 'CTRL', type: 'info', message: '起飞指令已发送' },
  { id: 5, time: '14:23:15', tag: 'DRONE', type: 'success', message: '已达到观测高度 8m' },
  { id: 6, time: '14:23:18', tag: 'AI', type: 'info', message: '开始迷宫结构扫描' },
  { id: 7, time: '14:23:22', tag: 'AI', type: 'success', message: '检测到障碍物 x3' },
  { id: 8, time: '14:23:25', tag: 'AI', type: 'success', message: '检测到拱门 x2' }
])

// 真实迷宫数据 - 基于480x1200格栅，缩放到500x400显示
const GRID_COLS = 480
const GRID_ROWS = 1200
const DISPLAY_W = 500
const DISPLAY_H = 400
const scaleX = (x) => (x / GRID_COLS) * DISPLAY_W
const scaleY = (y) => (y / GRID_ROWS) * DISPLAY_H

// 真实拱门坐标（从drone_flight_path.json）
const realGates = [
  { id: 1, gridX: 331, gridY: 943, name: '拱门1' },
  { id: 2, gridX: 295, gridY: 1003, name: '拱门2' },
  { id: 3, gridX: 219, gridY: 1087, name: '拱门3' },
  { id: 4, gridX: 131, gridY: 999, name: '拱门4' },
  { id: 5, gridX: 19, gridY: 1087, name: '拱门5' },
  { id: 6, gridX: 75, gridY: 1167, name: '拱门6' },
  { id: 7, gridX: 323, gridY: 1167, name: '拱门7' },
  { id: 8, gridX: 391, gridY: 1107, name: '拱门8' },
  { id: 9, gridX: 339, gridY: 103, name: '终点门' }
]

// 转换拱门坐标到显示坐标
const gates = computed(() => realGates.map(g => ({
  id: g.id,
  x: scaleX(g.gridX) - 15,
  y: scaleY(g.gridY) - 20,
  w: 30,
  h: 40,
  name: g.name
})))

// 真实飞行路径航点 - 无人机穿越拱门路径
const flightWaypoints = [
  [350, 945],  // 起点
  [331, 943],  // 拱门1
  [295, 1003], // 拱门2
  [219, 1087], // 拱门3
  [131, 999],  // 拱门4
  [19, 1087],  // 拱门5
  [75, 1167],  // 拱门6
  [323, 1167], // 拱门7
  [391, 1107], // 拱门8
  [350, 105]   // 终点
]

// 小车迷宫穿越路径 - 从path_data.json简化提取的真实路径
const carWaypoints = [
  [350, 945],  // 起点
  [126, 920],  // 向左上
  [62, 815],   // 向左上
  [236, 641],  // 斜向右上
  [289, 631],  // 继续向右
  [211, 553],  // 向左上
  [54, 552],   // 向左
  [273, 308],  // 斜向右上
  [262, 127],  // 向上
  [350, 105]   // 终点
]

// 迷宫墙壁线段数据（从grid_data.json提取的真实墙壁）
const mazeWalls = [
  // 水平墙壁
  {x1:0,y1:72,x2:343,y2:72},
  {x1:264,y1:128,x2:336,y2:128},
  {x1:128,y1:216,x2:215,y2:216},
  {x1:128,y1:288,x2:271,y2:288},
  {x1:48,y1:368,x2:135,y2:368},
  {x1:240,y1:376,x2:343,y2:376},
  {x1:0,y1:456,x2:79,y2:456},
  {x1:128,y1:456,x2:303,y2:456},
  {x1:56,y1:544,x2:343,y2:544},
  {x1:0,y1:632,x2:287,y2:632},
  {x1:0,y1:712,x2:151,y2:712},
  {x1:192,y1:712,x2:343,y2:712},
  {x1:64,y1:816,x2:287,y2:816},
  {x1:0,y1:912,x2:79,y2:912},
  {x1:128,y1:912,x2:231,y2:912},
  {x1:280,y1:912,x2:343,y2:912},
  {x1:0,y1:968,x2:271,y2:968},
  {x1:335,y1:968,x2:423,y2:968},
  {x1:0,y1:1192,x2:72,y2:1192},
  {x1:79,y1:1192,x2:320,y2:1192},
  {x1:327,y1:1192,x2:423,y2:1192},
  // 垂直墙壁
  {x1:0,y1:72,x2:0,y2:1199},
  {x1:128,y1:128,x2:128,y2:375},
  {x1:176,y1:816,x2:176,y2:919},
  {x1:208,y1:72,x2:208,y2:223},
  {x1:280,y1:768,x2:280,y2:919},
  {x1:336,y1:128,x2:336,y2:919},
  {x1:416,y1:968,x2:416,y2:1104},
  {x1:416,y1:1111,x2:416,y2:1199},
]

// 生成无人机SVG路径
const plannedPath = computed(() => {
  const points = flightWaypoints.map(p => `${scaleX(p[0])},${scaleY(p[1])}`)
  return `M ${points.join(' L ')}`
})

// 生成小车SVG路径
const carPlannedPath = computed(() => {
  const points = carWaypoints.map(p => `${scaleX(p[0])},${scaleY(p[1])}`)
  return `M ${points.join(' L ')}`
})

// 起点和终点
const startPoint = { gridX: 350, gridY: 945 }
const endPoint = { gridX: 350, gridY: 105 }

// 无人机和无人车当前位置
const currentWaypointIndex = ref(0)
const dronePos = ref({ x: scaleX(350), y: scaleY(945) })
const carPos = ref({ x: scaleX(350), y: scaleY(945) })

// 设备状态
const droneBattery = ref(87)
const droneAltitude = ref(8.2)
const droneSpeed = ref(2.5)
const droneState = ref('flying')
const droneStateText = ref('飞行中')
const signalStrength = ref(4)

const carBattery = ref(82)
const carSpeed = ref(0)
const carHeading = ref(45)
const carState = ref('standby')
const carStateText = ref('待命')

// 降落引导
const targetArucoId = ref(2)
const landingOffsetX = ref(12)
const landingOffsetY = ref(-8)
const landingState = ref('searching')
const landingStateText = ref('目标搜索中')

// 定时器
let timer = null
let simulationTimer = null

// WebSocket管理器
const wsManager = new WebSocketManager()

// 方法
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const getDetectionStyle = (det) => ({
  left: det.x + '%',
  top: det.y + '%',
  width: det.w + '%',
  height: det.h + '%'
})

const getLandingIndicatorStyle = () => ({
  transform: `translate(${landingOffsetX.value * 2}px, ${-landingOffsetY.value * 2}px)`
})

const getOffsetClass = (val) => {
  const abs = Math.abs(val)
  if (abs < 5) return 'good'
  if (abs < 15) return 'warning'
  return 'danger'
}

const startMission = () => {
  isAutoMode.value = true
  ElMessage.success('自动任务已启动')
  addLog('CTRL', 'success', '自动任务流程启动')
}

const pauseMission = () => {
  isAutoMode.value = false
  ElMessage.warning('任务已暂停')
  addLog('CTRL', 'warning', '任务暂停')
}

const emergencyStop = () => {
  isAutoMode.value = false
  ElMessage.error('紧急停止！')
  addLog('CTRL', 'error', '紧急停止触发')
}

const resetMission = () => {
  isAutoMode.value = false
  elapsedTime.value = 0
  missionSteps.value.forEach((step, idx) => {
    step.status = idx === 0 ? 'active' : 'pending'
    step.progress = idx === 0 ? 0 : 0
    step.time = ''
  })
  ElMessage.info('任务已重置')
  addLog('CTRL', 'info', '任务重置')
}

const refreshMap = () => {
  addLog('AI', 'info', '刷新地图数据...')
}

const addLog = (tag, type, message) => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  aiLogs.value.push({
    id: Date.now(),
    time,
    tag,
    type,
    message
  })
}

// 真实路径模拟
const startSimulation = () => {
  simulationTimer = setInterval(() => {
    if (isAutoMode.value) {
      // 无人机沿飞行路径移动（穿越拱门）
      const droneProgress = (Date.now() / 120) % 1000 / 1000
      const droneTotalWaypoints = flightWaypoints.length
      const droneCurrentIndex = Math.floor(droneProgress * (droneTotalWaypoints - 1))
      const droneNextIndex = Math.min(droneCurrentIndex + 1, droneTotalWaypoints - 1)
      const droneLocalProgress = (droneProgress * (droneTotalWaypoints - 1)) % 1
      
      // 无人机插值计算当前位置
      const droneCurr = flightWaypoints[droneCurrentIndex]
      const droneNext = flightWaypoints[droneNextIndex]
      const droneX = droneCurr[0] + (droneNext[0] - droneCurr[0]) * droneLocalProgress
      const droneY = droneCurr[1] + (droneNext[1] - droneCurr[1]) * droneLocalProgress
      
      dronePos.value = { x: scaleX(droneX), y: scaleY(droneY) }
      currentWaypointIndex.value = droneCurrentIndex
      
      // 小车沿迷宫路径移动（独立路径）
      const carProgress = (Date.now() / 150) % 1000 / 1000  // 稍慢于无人机
      const carTotalWaypoints = carWaypoints.length
      const carCurrentIndex = Math.floor(carProgress * (carTotalWaypoints - 1))
      const carNextIndex = Math.min(carCurrentIndex + 1, carTotalWaypoints - 1)
      const carLocalProgress = (carProgress * (carTotalWaypoints - 1)) % 1
      
      // 小车插值计算当前位置
      const carCurr = carWaypoints[carCurrentIndex]
      const carNext = carWaypoints[carNextIndex]
      const carX = carCurr[0] + (carNext[0] - carCurr[0]) * carLocalProgress
      const carY = carCurr[1] + (carNext[1] - carCurr[1]) * carLocalProgress
      
      carPos.value = { x: scaleX(carX), y: scaleY(carY) }
      
      // 更新任务进度
      const activeStep = missionSteps.value.find(s => s.status === 'active')
      if (activeStep && activeStep.progress < 100) {
        activeStep.progress = Math.min(100, activeStep.progress + 0.3)
        if (activeStep.progress >= 100) {
          activeStep.status = 'completed'
          activeStep.time = formatTime(elapsedTime.value)
          const nextStep = missionSteps.value.find(s => s.status === 'pending')
          if (nextStep) {
            nextStep.status = 'active'
            addLog('AI', 'info', `开始执行: ${nextStep.title}`)
          }
        }
      }
      
      // 根据当前阶段更新状态
      if (droneCurrentIndex >= 1 && droneCurrentIndex <= 8) {
        droneStateText.value = `穿越拱门${droneCurrentIndex}`
        carStateText.value = `迷宫穿越中 (${Math.floor(carProgress * 100)}%)`
        carState.value = 'moving'
      } else if (droneCurrentIndex >= 9) {
        droneStateText.value = '准备降落'
        landingState.value = 'approaching'
        landingStateText.value = '对准中'
      }
    }
    
    // 模拟降落偏移（逐渐收敛）
    const convergeFactor = isAutoMode.value ? 0.95 : 1
    landingOffsetX.value = Math.round(Math.sin(Date.now() / 1000) * 15 * convergeFactor)
    landingOffsetY.value = Math.round(Math.cos(Date.now() / 1200) * 12 * convergeFactor)
    
    // FPS波动
    fps.value = 22 + Math.floor(Math.random() * 6)
    
    // 更新设备状态（电量由WebSocket实时更新，这里只模拟速度）
    if (isAutoMode.value) {
      // 电量由WebSocket实时更新，不再模拟
      // 速度模拟（当WebSocket无数据时作为备选）
      if (!wsManager.isConnected) {
        droneSpeed.value = 1.5 + Math.random() * 2
        carSpeed.value = 0.8 + Math.random() * 1.2
      }
    }
  }, 100)
}

// 抓取图像
const captureImage = async () => {
  try {
    isCapturing.value = true
    isAnalyzing.value = true
    
    const token = localStorage.getItem('official_token')
    if (!token) {
      ElMessage.error('未获取到认证token，请重新认证')
      return
    }

    capturedImage.value = await officialServerAPI.captureImage(token)
    ElMessage.success('图像抓拍成功')
    addLog('VISION', 'success', '图像抓拍成功，开始AI分析')
    
    // 模拟AI分析
    setTimeout(() => {
      isAnalyzing.value = false
    }, 1500)
    
  } catch (error) {
    ElMessage.error('图像抓拍失败：' + error.message)
    addLog('VISION', 'error', '抓拍失败: ' + error.message)
  } finally {
    isCapturing.value = false
  }
}

onMounted(async () => {
  // 计时器
  timer = setInterval(() => {
    if (isAutoMode.value) {
      elapsedTime.value++
    }
  }, 1000)
  
  startSimulation()
  
  // 连接WebSocket获取实时遥测数据
  try {
    const token = localStorage.getItem('official_token')
    if (token) {
      await wsManager.connect(token)
      
      // 监听无人机遥测数据
      wsManager.on('aircraft_telemetry', (data) => {
        if (data.power !== undefined) droneBattery.value = data.power
        if (data.speed !== undefined) droneSpeed.value = data.speed
      })
      
      // 监听无人车遥测数据
      wsManager.on('vehicle_telemetry', (data) => {
        if (data.power !== undefined) carBattery.value = data.power
        if (data.speed !== undefined) carSpeed.value = data.speed
      })
      
      addLog('WS', 'success', 'WebSocket已连接，开始接收遥测数据')
    }
  } catch (error) {
    console.error('WebSocket连接失败:', error)
    addLog('WS', 'error', 'WebSocket连接失败: ' + error.message)
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (simulationTimer) clearInterval(simulationTimer)
  wsManager.disconnect()
})
</script>

<style scoped>
.auto-control {
  height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  color: #e2e8f0;
  font-family: 'Inter', 'PingFang SC', sans-serif;
  overflow: hidden;
}

/* 顶部栏 */
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid rgba(59, 130, 246, 0.3);
  backdrop-filter: blur(20px);
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6, #10b981);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 30px rgba(59, 130, 246, 0.5);
}

.logo-icon svg {
  width: 28px;
  height: 28px;
  color: white;
}

.title-text h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 1px;
}

.status-section {
  display: flex;
  align-items: center;
  gap: 24px;
}

.mode-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 20px;
  font-size: 13px;
}

.mode-indicator.active {
  background: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.5);
}

.mode-dot {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.mode-indicator.active .mode-dot {
  background: #10b981;
}

.time-display {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.time-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

.time-value {
  font-size: 24px;
  font-weight: 700;
  font-family: 'Monaco', monospace;
  color: #3b82f6;
}

/* 主容器 */
.main-container {
  display: grid;
  grid-template-columns: 320px 1fr 300px;
  gap: 16px;
  padding: 16px;
  height: calc(100vh - 90px);
  overflow: hidden;
}

/* 面板卡片 */
.panel-card {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(59, 130, 246, 0.1);
  border-bottom: 1px solid rgba(59, 130, 246, 0.2);
  font-weight: 600;
  font-size: 14px;
}

.panel-icon {
  font-size: 16px;
}

/* 左侧面板 */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.mission-flow {
  flex: 1;
}

.flow-progress {
  margin-left: auto;
  font-size: 12px;
  color: #3b82f6;
  font-weight: 700;
}

.mission-steps {
  padding: 16px;
  max-height: calc(100% - 50px);
  overflow-y: auto;
}

.mission-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  position: relative;
}

.step-connector {
  position: absolute;
  left: 15px;
  top: -12px;
  width: 2px;
  height: 24px;
  background: rgba(59, 130, 246, 0.3);
}

.mission-step.completed .step-connector {
  background: #10b981;
}

.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.2);
  border: 2px solid rgba(59, 130, 246, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.mission-step.completed .step-indicator {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10b981;
  color: #10b981;
}

.mission-step.active .step-indicator {
  background: rgba(59, 130, 246, 0.3);
  border-color: #3b82f6;
  animation: pulse 2s infinite;
}

.mission-step.error .step-indicator {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

.loading-icon {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 2px;
}

.step-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.step-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 11px;
  color: #3b82f6;
  font-weight: 600;
}

.step-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  font-family: monospace;
}

/* AI日志 */
.ai-log {
  height: 200px;
}

.log-count {
  margin-left: auto;
  background: rgba(59, 130, 246, 0.2);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.log-container {
  padding: 8px;
  height: calc(100% - 50px);
  overflow-y: auto;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  font-size: 11px;
  border-radius: 4px;
  margin-bottom: 4px;
  background: rgba(0, 0, 0, 0.2);
}

.log-time {
  color: rgba(255, 255, 255, 0.4);
  font-family: monospace;
}

.log-tag {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
}

.log-item.info .log-tag { background: rgba(59, 130, 246, 0.3); color: #3b82f6; }
.log-item.success .log-tag { background: rgba(16, 185, 129, 0.3); color: #10b981; }
.log-item.warning .log-tag { background: rgba(245, 158, 11, 0.3); color: #f59e0b; }
.log-item.error .log-tag { background: rgba(239, 68, 68, 0.3); color: #ef4444; }

.log-message {
  color: rgba(255, 255, 255, 0.8);
}

/* 中间面板 */
.center-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.vision-panel {
  flex: 1;
}

.fps-indicator {
  margin-left: auto;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.vision-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.capture-btn {
  padding: 6px 12px;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid #3b82f6;
  border-radius: 6px;
  color: #3b82f6;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.capture-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.3);
}

.capture-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.fps-indicator {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.fps-value {
  font-size: 18px;
  font-weight: 700;
  color: #10b981;
}

.fps-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

.vision-container {
  padding: 12px;
  height: calc(100% - 50px);
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.video-frame {
  flex: 1;
  background: #000;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
  min-height: 180px;
}

.video-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.3);
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.ai-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.detection-box {
  position: absolute;
  border: 2px solid;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 4px;
}

.detection-box.obstacle {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.detection-box.gate {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.detection-box.aruco {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.det-label {
  font-size: 10px;
  font-weight: 600;
  color: white;
  background: rgba(0, 0, 0, 0.6);
  padding: 1px 4px;
  border-radius: 2px;
}

.det-conf {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.8);
}

.analysis-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  color: #3b82f6;
  font-size: 12px;
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

.vision-info {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.info-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

.info-value {
  font-size: 14px;
  font-weight: 600;
}

.info-value.obstacle { color: #ef4444; }
.info-value.gate { color: #10b981; }
.info-value.aruco { color: #f59e0b; }

/* 地图面板 */
.map-panel {
  flex: 1;
}

.map-actions {
  margin-left: auto;
}

.action-btn {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  padding: 4px 8px;
  cursor: pointer;
  color: #e2e8f0;
}

.action-btn:hover {
  background: rgba(59, 130, 246, 0.3);
}

.map-container {
  padding: 12px;
  height: calc(100% - 50px);
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.maze-grid {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  overflow: hidden;
  min-height: 200px;
}

.maze-svg {
  width: 100%;
  height: 100%;
}

.path-animation {
  stroke-dashoffset: 100;
  animation: dash 3s linear infinite;
}

.car-path-animation {
  stroke-dashoffset: 80;
  animation: car-dash 4s linear infinite;
}

@keyframes car-dash {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes dash {
  to { stroke-dashoffset: 0; }
}

.drone-marker, .car-marker {
  transition: transform 0.1s ease;
}

.map-legend {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-color.drone { background: #3b82f6; }
.legend-color.car { background: #10b981; }
.legend-color.obstacle { background: #ef4444; }
.legend-color.gate { border: 2px dashed #10b981; }
.legend-color.wall { background: #475569; }
.legend-color.path { background: #3b82f6; }
.legend-color.car-path { background: #f59e0b; }

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.device-cards {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid;
}

.device-card.drone { border-left-color: #3b82f6; }
.device-card.car { border-left-color: #10b981; }

.device-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.device-icon {
  font-size: 20px;
}

.device-name {
  font-weight: 600;
  font-size: 13px;
}

.device-state {
  margin-left: auto;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
}

.device-state.flying, .device-state.moving {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.device-state.standby {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.device-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  width: 40px;
}

.stat-bar {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.stat-fill.battery {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  border-radius: 3px;
}

.stat-value {
  font-size: 12px;
  font-weight: 600;
  min-width: 45px;
  text-align: right;
}

.signal-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
}

.signal-bar {
  width: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 1px;
}

.signal-bar:nth-child(1) { height: 25%; }
.signal-bar:nth-child(2) { height: 50%; }
.signal-bar:nth-child(3) { height: 75%; }
.signal-bar:nth-child(4) { height: 100%; }

.signal-bar.active {
  background: #10b981;
}

/* 降落模块 */
.landing-content {
  padding: 12px;
  display: flex;
  gap: 16px;
}

.landing-visual {
  width: 120px;
  height: 120px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.target-circle {
  border: 2px solid rgba(16, 185, 129, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.target-circle.outer {
  width: 100px;
  height: 100px;
}

.target-circle.middle {
  width: 60px;
  height: 60px;
}

.target-circle.inner {
  width: 20px;
  height: 20px;
  background: rgba(16, 185, 129, 0.3);
}

.target-crosshair {
  position: absolute;
  width: 100%;
  height: 100%;
}

.target-crosshair::before,
.target-crosshair::after {
  content: '';
  position: absolute;
  background: rgba(16, 185, 129, 0.5);
}

.target-crosshair::before {
  width: 100%;
  height: 1px;
  top: 50%;
}

.target-crosshair::after {
  width: 1px;
  height: 100%;
  left: 50%;
}

.drone-indicator {
  position: absolute;
  font-size: 20px;
  transition: transform 0.1s ease;
  filter: drop-shadow(0 0 8px #3b82f6);
}

.landing-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.info-row .info-label {
  color: rgba(255, 255, 255, 0.5);
}

.info-row .info-value {
  font-weight: 600;
}

.info-value.good { color: #10b981; }
.info-value.warning { color: #f59e0b; }
.info-value.danger { color: #ef4444; }
.info-value.searching { color: #3b82f6; }

/* 控制按钮 */
.control-buttons {
  margin-top: auto;
}

.button-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 12px;
}

.ctrl-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.ctrl-btn .btn-icon {
  font-size: 20px;
}

.ctrl-btn.primary {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.ctrl-btn.warning {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.ctrl-btn.danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.ctrl-btn.info {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.5);
  color: #e2e8f0;
}

.ctrl-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.ctrl-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 动画 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 3px;
}

/* 响应式 */
@media screen and (max-width: 1400px) {
  .main-container {
    grid-template-columns: 280px 1fr 260px;
  }
}

@media screen and (max-width: 1200px) {
  .main-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  
  .left-panel, .center-panel, .right-panel {
    max-height: none;
  }
}
</style>
