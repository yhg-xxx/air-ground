<template>
  <div class="api-test">
    <ThreeScene ref="threeSceneRef" />
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
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
}
</style>
