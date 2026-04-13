<template>
  <div class="api-test">
    <h2>融瓴 API 测试</h2>
    
    <div class="main-content">
      <!-- 左侧：3D 场景 -->
      <div class="left-panel">
        <div class="test-section">
          <h3>3D 场景模拟</h3>
          <ThreeScene ref="threeSceneRef" />
        </div>
      </div>
      
      <!-- 右侧：控制界面 -->
      <div class="right-panel">
        <!-- 认证测试 -->
        <div class="test-section">
          <h3>1. 身份认证</h3>
          <button @click="testAuth" :disabled="loading">获取 Token</button>
          <div v-if="token" class="result">
            <p>Token: {{ token }}</p>
          </div>
          <div v-if="error" class="error">{{ error }}</div>
        </div>
        
        <!-- 云台抓拍测试 -->
        <div class="test-section">
          <h3>2. 云台抓拍</h3>
          <button @click="testCapture" :disabled="!token || loading">获取图片</button>
          <div v-if="imageData" class="result">
            <img :src="imageData" alt="Captured Image" style="max-width: 300px;" />
          </div>
        </div>
        
        <!-- 自动降落测试 -->
        <div class="test-section">
          <h3>3. 自动降落</h3>
          <button @click="startAutoLanding" :disabled="!wsConnected || autoLandingActive" class="auto-landing-btn">
            {{ autoLandingActive ? '自动降落中...' : '开始自动降落' }}
          </button>
          <button @click="stopAutoLanding" :disabled="!autoLandingActive" class="stop-btn">停止降落</button>
          
          <div v-if="landingStatus" class="landing-status">
            <p><strong>状态:</strong> {{ landingStatus }}</p>
            <p v-if="landingDetection"><strong>检测信息:</strong></p>
            <ul v-if="landingDetection">
              <li>标记ID: {{ landingDetection.marker_id }}</li>
              <li>X偏移: {{ landingDetection.x?.toFixed(2) }}m</li>
              <li>Y偏移: {{ landingDetection.y?.toFixed(2) }}m</li>
              <li>高度: {{ landingDetection.height?.toFixed(2) }}m</li>
              <li>距离: {{ landingDetection.distance?.toFixed(2) }}m</li>
            </ul>
            <p v-if="landingCommand"><strong>控制命令:</strong> {{ landingCommand.message }}</p>
          </div>
        </div>
        
        <!-- WebSocket 测试 -->
        <div class="test-section">
          <h3>4. WebSocket 控制</h3>
          <button @click="connectWebSocket" :disabled="!token || loading">连接 WebSocket</button>
          <button @click="disconnectWebSocket" :disabled="!wsConnected">断开连接</button>
          
          <div class="ws-controls">
        <h4>无人机控制</h4>
        <button @click="sendControl('aircraft', 7, 2000)">起飞</button>
        <button @click="sendControl('aircraft', 8, 2000)">降落</button>
        <button @click="sendControl('aircraft', 9, 2000)">返航</button>
        <button @click="sendControl('aircraft', 10, 2000)">云台复位</button>
        <br>
        <button @click="sendControl('aircraft', 4, 2000)">前进</button>
        <button @click="sendControl('aircraft', 4, 1000)">后退</button>
        <button @click="sendControl('aircraft', 1, 2000)">右转</button>
        <button @click="sendControl('aircraft', 1, 1000)">左转</button>
        <br>
        <button @click="sendControl('aircraft', 2, 2000)">上升</button>
        <button @click="sendControl('aircraft', 2, 1000)">下降</button>
        <button @click="sendControl('aircraft', 3, 2000)">右移</button>
        <button @click="sendControl('aircraft', 3, 1000)">左移</button>
        <br>
        <button @click="sendControl('aircraft', 5, 2000)">云台仰</button>
        <button @click="sendControl('aircraft', 5, 1000)">云台俯</button>
        <button @click="sendControl('aircraft', 6, 2000)">云台左滚</button>
        <button @click="sendControl('aircraft', 6, 1000)">云台右滚</button>
      </div>
          
          <div class="ws-controls">
            <h4>车辆控制</h4>
            <button @click="sendControl('vehicle', 1, 2000)">前进</button>
            <button @click="sendControl('vehicle', 1, 1000)">后退</button>
            <button @click="sendControl('vehicle', 2, 1000)">左转</button>
            <button @click="sendControl('vehicle', 2, 2000)">右转</button>
          </div>
          
          <div class="ws-messages">
            <h4>消息</h4>
            <div class="message-list">
              <div v-for="(msg, index) in wsMessages" :key="index" class="message">
                {{ msg }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, ref as refElement } from 'vue';
import ThreeScene from './ThreeScene.vue';

const token = ref('');
const error = ref('');
const loading = ref(false);
const imageData = ref('');
const wsConnected = ref(false);
const ws = ref(null);
const wsMessages = ref([]);
const threeSceneRef = refElement(null);

// 自动降落相关状态
const autoLandingActive = ref(false);
const landingStatus = ref('');
const landingDetection = ref(null);
const landingCommand = ref(null);
const autoLandingInterval = ref(null);

// API 配置
const API_BASE = 'http://localhost:30080';
const WS_BASE = 'ws://localhost:30081';

// 测试认证
async function testAuth() {
  loading.value = true;
  error.value = '';
  try {
    const response = await fetch(`${API_BASE}/api/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: 'fcs002',
        password: 'fcs002fcs002'
      })
    });
    
    const data = await response.json();
    if (data.code === '1') {
      token.value = data.data.token;
    } else {
      error.value = data.msg;
    }
  } catch (err) {
    error.value = '认证失败: ' + err.message;
  } finally {
    loading.value = false;
  }
}

// 测试云台抓拍
async function testCapture() {
  if (!token.value) {
    error.value = '请先获取 Token';
    return;
  }
  
  loading.value = true;
  error.value = '';
  try {
    // 只使用前端捕获的无人机视角图片
    if (threeSceneRef.value) {
      // 捕获当前视角的图片
      const capturedImage = threeSceneRef.value.captureImage();
      if (capturedImage) {
        imageData.value = capturedImage;
      } else {
        error.value = '获取图片失败，请确保无人机摄像头已初始化';
      }
    } else {
      error.value = '获取图片失败，3D场景未加载';
    }
  } catch (err) {
    error.value = '获取图片失败: ' + err.message;
  } finally {
    loading.value = false;
  }
}

// 连接 WebSocket
function connectWebSocket() {
  if (!token.value) {
    error.value = '请先获取 Token';
    return;
  }
  
  ws.value = new WebSocket(`${WS_BASE}?token=${token.value}`);
  
  ws.value.onopen = () => {
    wsConnected.value = true;
    wsMessages.value.push('WebSocket 连接成功');
  };
  
  ws.value.onmessage = (event) => {
    wsMessages.value.push('收到: ' + event.data);
    // 限制消息数量
    if (wsMessages.value.length > 50) {
      wsMessages.value.shift();
    }
    
    // 更新 3D 场景
    try {
      const data = JSON.parse(event.data);
      if (threeSceneRef.value && (data.type.includes('aircraft_telemetry') || data.type.includes('vehicle_telemetry'))) {
        threeSceneRef.value.updateTelemetry(data);
      }
    } catch (e) {
      console.error('解析消息失败:', e);
    }
  };
  
  ws.value.onclose = () => {
    wsConnected.value = false;
    wsMessages.value.push('WebSocket 连接关闭');
  };
  
  ws.value.onerror = (error) => {
    wsMessages.value.push('WebSocket 错误: ' + error.message);
  };
}

// 断开 WebSocket
function disconnectWebSocket() {
  if (ws.value) {
    ws.value.close();
  }
}

// 发送控制指令
function sendControl(target, channel, value) {
  if (!wsConnected.value) {
    error.value = '请先连接 WebSocket';
    return;
  }
  
  const command = {
    type: 'control',
    target: target,
    channel: channel,
    value: value
  };
  
  ws.value.send(JSON.stringify(command));
  wsMessages.value.push('发送: ' + JSON.stringify(command));
}

// 开始自动降落
async function startAutoLanding() {
  if (!wsConnected.value) {
    error.value = '请先连接 WebSocket';
    return;
  }
  
  if (!token.value) {
    error.value = '请先获取 Token';
    return;
  }
  
  autoLandingActive.value = true;
  landingStatus.value = '启动自动降落...';
  landingDetection.value = null;
  landingCommand.value = null;
  
  // 立即执行一次降落逻辑
  await executeLandingStep();
  
  // 设置定时器，每2秒执行一次降落逻辑
  autoLandingInterval.value = setInterval(executeLandingStep, 2000);
}

// 执行降落步骤
async function executeLandingStep() {
  if (!autoLandingActive.value) {
    return;
  }
  
  try {
    // 1. 从3D场景捕获图像
    if (threeSceneRef.value) {
      const capturedImage = threeSceneRef.value.captureImage();
      if (!capturedImage) {
        landingStatus.value = '图像捕获失败';
        return;
      }
      
      // 2. 发送图像到后端处理
      landingStatus.value = '处理图像中...';
      
      const response = await fetch(`${API_BASE}/api/landing/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token.value}`
        },
        body: JSON.stringify({
          image: capturedImage
        })
      });
      
      const data = await response.json();
      
      if (data.code === '1' && data.data.success) {
        // 更新检测信息
        landingDetection.value = data.data.detection;
        landingCommand.value = data.data.command;
        
        // 3. 根据返回的命令控制无人机
        const command = data.data.command;
        
        if (command.action === 'land') {
          // 执行降落
          sendControl(command.target, command.channel, command.value);
          landingStatus.value = '执行降落';
          stopAutoLanding();
        } else if (command.action === 'descend') {
          // 降低高度
          sendControl(command.target, command.channel, command.value);
          landingStatus.value = command.message;
        } else if (command.action === 'adjust') {
          // 调整水平位置
          if (command.commands && command.commands.length > 0) {
            command.commands.forEach(cmd => {
              sendControl(cmd.target, cmd.channel, cmd.value);
            });
            landingStatus.value = command.message;
          }
        } else {
          landingStatus.value = command.message;
        }
      } else {
        landingStatus.value = data.data.message || '图像处理失败';
      }
    } else {
      landingStatus.value = '3D场景未加载';
    }
  } catch (err) {
    error.value = '自动降落错误: ' + err.message;
    landingStatus.value = '错误: ' + err.message;
  }
}

// 停止自动降落
function stopAutoLanding() {
  if (autoLandingInterval.value) {
    clearInterval(autoLandingInterval.value);
    autoLandingInterval.value = null;
  }
  autoLandingActive.value = false;
  landingStatus.value = '自动降落已停止';
}
</script>

<style scoped>
.api-test {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.main-content {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.left-panel {
  flex: 1;
  min-width: 600px;
}

.right-panel {
  flex: 1;
  min-width: 400px;
}

.test-section {
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

button {
  margin: 5px;
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.auto-landing-btn {
  background-color: #ff9800;
}

.auto-landing-btn:disabled {
  background-color: #cccccc;
}

.stop-btn {
  background-color: #f44336;
}

.landing-status {
  margin-top: 10px;
  padding: 10px;
  background-color: #e3f2fd;
  border-radius: 4px;
  border-left: 4px solid #2196f3;
}

.landing-status p {
  margin: 5px 0;
}

.landing-status ul {
  margin: 5px 0;
  padding-left: 20px;
}

.result {
  margin-top: 10px;
  padding: 10px;
  background-color: #f0f0f0;
  border-radius: 4px;
}

.error {
  margin-top: 10px;
  padding: 10px;
  background-color: #ffebee;
  color: #c62828;
  border-radius: 4px;
}

.ws-controls {
  margin: 15px 0;
}

.ws-messages {
  margin-top: 20px;
}

.message-list {
  height: 200px;
  overflow-y: auto;
  border: 1px solid #ddd;
  padding: 10px;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.message {
  margin-bottom: 5px;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel,
  .right-panel {
    min-width: auto;
  }
}
</style>
