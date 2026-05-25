<template>
  <div class="three-scene">
    <div class="scene-top">
      <div class="camera-sidebar">
        <div class="camera-wrapper">
          <div class="camera-label">无人机摄像头</div>
          <div class="camera-position">位置: {{ aircraftPosition }}</div>
          <div ref="aircraftCameraContainer" class="aircraft-camera-container"></div>
        </div>
        <div class="camera-wrapper">
          <div class="camera-label">无人车摄像头</div>
          <div class="camera-position">位置: {{ vehiclePosition }}</div>
          <div ref="vehicleCameraContainer" class="vehicle-camera-container"></div>
        </div>
      </div>
      <div class="scene-wrapper">
        <div class="scene-label">全局视角</div>
        <div ref="container" class="scene-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// 导入ARUCO码图片
import arucoCode from './icons/2号车.png';

// 导入迷宫模块
import { createLeftMaze, checkCollision, getCollisionBoxCount } from './Maze.js';

const container = ref(null);
const vehicleCameraContainer = ref(null);
const aircraftCameraContainer = ref(null);
let scene, camera, aircraftCamera, vehicleCamera, renderer, vehicleRenderer, aircraftRenderer, controls;
let aircraft, vehicle, gimbal;
let aircraftPosition = ref('(0, 0, 0)');
let vehiclePosition = ref('(0, 0, 0)');
let cameraMode = ref('orbit'); // orbit, follow, camera

// 键盘状态监听
const keys = ref({});

// 自动化算法状态
const isAutoMissionRunning = ref(false);
const autoMissionStatus = ref('');
let ws = null; // WebSocket连接
let telemetryInterval = null; // 遥测数据发送定时器

// 自动化路径规划 - 根据用户提供的路线图片生成
const AUTO_PATHS = {
  // 无人车迷宫路径（黄色路线）- 从起点穿过迷宫到达终点
  vehicle: [
    { x: 8.546, z: 16.756 },   // 起点
    { x: 7.0, z: 16.756 },     // 向左进入通道
    { x: 7.0, z: 12.0 },       // 向前到第一个转弯
    { x: 4.0, z: 12.0 },       // 向左转
    { x: 4.0, z: 5.0 },        // 向前穿过通道
    { x: 6.5, z: 5.0 },        // 向右转
    { x: 6.5, z: -2.0 },       // 向前
    { x: 3.5, z: -2.0 },       // 向左转
    { x: 3.5, z: -8.0 },       // 向前
    { x: 6.0, z: -8.0 },       // 向右转
    { x: 6.0, z: -15.0 },      // 向前
    { x: 3.0, z: -15.0 },      // 向左转
    { x: 3.0, z: -20.0 },      // 向前到底部
    { x: 10.0, z: -20.0 },     // 向右到达终点区域
  ],
  // 无人机拱门路径（红蓝路线）- 起飞后穿过所有拱门
  aircraft: [
    { x: 8.546, z: 16.756, y: 0.05 },  // 起点（地面）
    { x: 8.546, z: 16.756, y: 3.0 },   // 起飞到3m
    { x: 8.546, z: 16.756, y: 5.0 },   // 上升到5m
    // 拱门区域路径
    { x: 7.5, z: 14.0, y: 5.0 },       // 飞向拱门区域入口
    { x: 6.5, z: 12.0, y: 5.0 },       // 拱门1附近
    { x: 5.0, z: 10.0, y: 5.0 },       // 中间点
    { x: 3.0, z: 8.0, y: 5.0 },        // 拱门2附近
    { x: 1.0, z: 6.0, y: 5.0 },        // 中间点
    { x: -1.0, z: 4.0, y: 5.0 },       // 拱门3附近
    { x: -3.0, z: 2.0, y: 5.0 },       // 中间点
    { x: -5.0, z: 0.0, y: 5.0 },       // 拱门4附近
    { x: -3.0, z: -2.0, y: 5.0 },      // 中间点
    { x: -1.0, z: -4.0, y: 5.0 },       // 拱门5附近
    { x: 1.0, z: -6.0, y: 5.0 },       // 中间点
    { x: 3.0, z: -8.0, y: 5.0 },       // 拱门6附近
    { x: 5.0, z: -10.0, y: 5.0 },      // 中间点
    { x: 7.0, z: -12.0, y: 5.0 },      // 拱门7附近
    { x: 8.0, z: -14.0, y: 5.0 },      // 中间点
    { x: 9.0, z: -16.0, y: 5.0 },      // 拱门8附近
    { x: 10.0, z: -18.0, y: 5.0 },     // 中间点
    { x: 11.0, z: -20.0, y: 5.0 },     // 拱门9附近（终点）
    // 返回起点
    { x: 10.0, z: -15.0, y: 5.0 },     // 返回路径点
    { x: 9.0, z: -10.0, y: 5.0 },      // 返回路径点
    { x: 8.546, z: 16.756, y: 5.0 },   // 返回起点上方
    { x: 8.546, z: 16.756, y: 2.0 },   // 下降到2m
    { x: 8.546, z: 16.756, y: 0.05 },  // 降落
  ]
};

// 自动化控制状态
let autoMissionInterval = null;
let currentVehiclePathIndex = 0;
let currentAircraftPathIndex = 0;
const cellSize = 25 / 480; // 迷宫单元格大小

// ====================== 自动化算法控制 ======================
function startAutoMission() {
  if (isAutoMissionRunning.value) return;

  console.log('准备启动本地自动化算法');
  isAutoMissionRunning.value = true;
  autoMissionStatus.value = '启动自动化任务...';

  // 重置路径索引
  currentVehiclePathIndex = 0;
  currentAircraftPathIndex = 0;

  // 重置位置到起点
  telemetryData.value.vehicle.position.x = AUTO_PATHS.vehicle[0].x;
  telemetryData.value.vehicle.position.z = AUTO_PATHS.vehicle[0].z;
  telemetryData.value.aircraft.position.x = AUTO_PATHS.aircraft[0].x;
  telemetryData.value.aircraft.position.z = AUTO_PATHS.aircraft[0].z;
  telemetryData.value.aircraft.position.y = AUTO_PATHS.aircraft[0].y;

  // 启动自动化控制循环
  autoMissionInterval = setInterval(executeAutoMissionStep, 100);
}

function stopAutoMission() {
  if (autoMissionInterval) {
    clearInterval(autoMissionInterval);
    autoMissionInterval = null;
  }
  isAutoMissionRunning.value = false;
  autoMissionStatus.value = '自动化任务已停止';
}

function executeAutoMissionStep() {
  const vc = telemetryData.value.vehicle;
  const ac = telemetryData.value.aircraft;

  // 无人车路径控制
  if (currentVehiclePathIndex < AUTO_PATHS.vehicle.length) {
    const target = AUTO_PATHS.vehicle[currentVehiclePathIndex];
    const dx = target.x - vc.position.x;
    const dz = target.z - vc.position.z;
    const distance = Math.sqrt(dx * dx + dz * dz);

    if (distance < 0.1) {
      // 到达当前目标点，移动到下一个
      currentVehiclePathIndex++;
      autoMissionStatus.value = `无人车到达路径点 ${currentVehiclePathIndex}/${AUTO_PATHS.vehicle.length}`;
    } else {
      // 移动向目标点
      const speed = 0.05;
      const angle = Math.atan2(dx, dz);
      vc.rotation.y = angle * 180 / Math.PI;
      vc.position.x += Math.sin(angle) * speed;
      vc.position.z += Math.cos(angle) * speed;
    }
  }

  // 无人机路径控制
  if (currentAircraftPathIndex < AUTO_PATHS.aircraft.length) {
    const target = AUTO_PATHS.aircraft[currentAircraftPathIndex];
    const dx = target.x - ac.position.x;
    const dy = target.y - ac.position.y;
    const dz = target.z - ac.position.z;
    const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

    if (distance < 0.2) {
      // 到达当前目标点，移动到下一个
      currentAircraftPathIndex++;
      autoMissionStatus.value = `无人机到达路径点 ${currentAircraftPathIndex}/${AUTO_PATHS.aircraft.length}`;
    } else {
      // 移动向目标点（包括高度）
      const speed = 0.08;
      ac.position.x += (dx / distance) * speed;
      ac.position.y += (dy / distance) * speed;
      ac.position.z += (dz / distance) * speed;
    }
  }

  // 检查是否完成所有路径
  if (currentVehiclePathIndex >= AUTO_PATHS.vehicle.length &&
      currentAircraftPathIndex >= AUTO_PATHS.aircraft.length) {
    stopAutoMission();
    autoMissionStatus.value = '自动化任务完成！';
  }
}

function connectWebSocket() {
  // 如果已经连接，先关闭
  if (ws) {
    ws.close();
  }
  
  // 连接到mock_server的WebSocket
  console.log('正在连接WebSocket...');
  ws = new WebSocket('ws://localhost:30081?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...');
  
  ws.onopen = () => {
    console.log('WebSocket连接已建立，readyState:', ws.readyState);
    // 开始定期发送遥测数据
    startTelemetrySending();
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('收到遥测数据:', data.type);
      
      if (data.type === 'control') {
        // 处理控制指令
        handleControlCommand(data);
      } else if (data.type === 'aircraft_telemetry_gnss') {
        // 忽略mock_server发送的无人机位置更新，只依赖控制指令
        console.log('忽略mock_server的无人机位置更新');
      } else if (data.type === 'vehicle_telemetry_gnss') {
        // 忽略mock_server发送的车辆位置更新，只依赖控制指令
        console.log('忽略mock_server的车辆位置更新');
      } else if (data.type === 'capture_image_request') {
        // 收到图片抓拍请求
        console.log('收到图片抓拍请求');
        const imageUrl = captureImageInternal();
        if (imageUrl) {
          // 将图片数据通过WebSocket发送回后端
          ws.send(JSON.stringify({
            type: 'capture_image_response',
            data: imageUrl
          }));
          console.log('已发送图片数据');
        }
      }
    } catch (e) {
      console.error('解析遥测数据失败:', e, event.data);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket错误:', error);
  };
  
  ws.onclose = () => {
    console.log('WebSocket连接已关闭');
    isAutoMissionRunning.value = false;
  };
}

function disconnectWebSocket() {
  if (telemetryInterval) {
    clearInterval(telemetryInterval);
    telemetryInterval = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
}

// 内部图片抓拍函数
function captureImageInternal() {
  if (aircraftCamera && aircraftRenderer) {
    // 使用无人机视角的渲染器渲染场景
    aircraftRenderer.render(scene, aircraftCamera);
    const imageUrl = aircraftRenderer.domElement.toDataURL('image/jpeg');
    return imageUrl;
  }
  return null;
}

// ====================== 处理来自后端的控制指令 ======================
function handleControlCommand(command) {
  const target = command.target;
  const channel = command.channel;
  const value = command.value;
  
  console.log('收到控制指令:', target, '通道', channel, '值', value);
  
  const ac = telemetryData.value.aircraft;
  const vc = telemetryData.value.vehicle;
  
  // 移动速度因子（大幅增加速度）
  const speed = 0.5;
  const altitudeSpeed = 2.0;
  
  let updated = false;
  
  if (target === 'aircraft') {
    if (channel === 1) {  // 左转/右转
      if (value > 1500) {  // 右转
        ac.rotation.y -= speed * (value - 1500) / 500 * (180/Math.PI);
        console.log('右转:', ac.rotation.y);
        updated = true;
      } else if (value < 1500) {  // 左转
        ac.rotation.y += speed * (1500 - value) / 500 * (180/Math.PI);
      }
    } else if (channel === 2) {  // 上升/下降
      if (value > 1500) {  // 上升
        ac.position.y += altitudeSpeed * (value - 1500) / 500;
      } else if (value < 1500) {  // 下降
        ac.position.y -= altitudeSpeed * (1500 - value) / 500;
        if (ac.position.y < 0.2) ac.position.y = 0.2;
      }
    } else if (channel === 3) {  // 左移/右移
      const yawRad = ac.rotation.y * Math.PI / 180;
      if (value > 1500) {  // 右移
        ac.position.x += Math.cos(yawRad) * speed * (value - 1500) / 500;
        ac.position.z -= Math.sin(yawRad) * speed * (value - 1500) / 500;
      } else if (value < 1500) {  // 左移
        ac.position.x -= Math.cos(yawRad) * speed * (1500 - value) / 500;
        ac.position.z += Math.sin(yawRad) * speed * (1500 - value) / 500;
      }
    } else if (channel === 4) {  // 前进/后退
      const yawRad = ac.rotation.y * Math.PI / 180;
      if (value > 1500) {  // 前进
        ac.position.x -= Math.sin(yawRad) * speed * (value - 1500) / 500;
        ac.position.z -= Math.cos(yawRad) * speed * (value - 1500) / 500;
      } else if (value < 1500) {  // 后退
        ac.position.x += Math.sin(yawRad) * speed * (1500 - value) / 500;
        ac.position.z += Math.cos(yawRad) * speed * (1500 - value) / 500;
      }
    } else if (channel === 5) {  // 云台俯仰
      if (value > 1500) {  // 仰
        ac.gimbal.pitch += 1.0 * (value - 1500) / 500;
        if (ac.gimbal.pitch > 90) ac.gimbal.pitch = 90;
      } else if (value < 1500) {  // 俯
        ac.gimbal.pitch -= 1.0 * (1500 - value) / 500;
        if (ac.gimbal.pitch < -90) ac.gimbal.pitch = -90;
      }
    } else if (channel === 6) {  // 云台横滚
      if (value > 1500) {  // 左
        ac.gimbal.roll += 1.0 * (value - 1500) / 500;
        if (ac.gimbal.roll > 45) ac.gimbal.roll = 45;
      } else if (value < 1500) {  // 右
        ac.gimbal.roll -= 1.0 * (1500 - value) / 500;
        if (ac.gimbal.roll < -45) ac.gimbal.roll = -45;
      }
    } else if (channel === 7) {  // 起飞
      if (value >= 1500) {
        ac.position.y = 10.0;
      }
    } else if (channel === 8) {  // 降落
      if (value >= 1500) {
        ac.position.y = 0.05;
      }
    }
  } else if (target === 'vehicle') {
    if (channel === 1) {  // 前进/后退
      const vYawRad = vc.rotation.y * Math.PI / 180;
      if (value > 1500) {  // 前进
        vc.position.x += Math.sin(vYawRad) * speed * (value - 1500) / 500;
        vc.position.z += Math.cos(vYawRad) * speed * (value - 1500) / 500;
      } else if (value < 1500) {  // 后退
        vc.position.x -= Math.sin(vYawRad) * speed * (1500 - value) / 500;
        vc.position.z -= Math.cos(vYawRad) * speed * (1500 - value) / 500;
      }
    } else if (channel === 2) {  // 左转/右转
      if (value > 1500) {  // 右转
        vc.rotation.y -= speed * (value - 1500) / 500 * (180/Math.PI);
      } else if (value < 1500) {  // 左转
        vc.rotation.y += speed * (1500 - value) / 500 * (180/Math.PI);
      }
    }
  }
}

// ====================== 遥感控制参数 ======================
const CONTROL_CONFIG = {
  aircraftMoveSpeed: 0.05,      // 无人机移动速度
  aircraftRotateSpeed: 0.03,    // 无人机旋转速度 (弧度)
  aircraftGimbalSpeed: 0.05,    // 云台旋转速度 (弧度)
  vehicleMoveSpeed: 0.03,       // 车辆移动速度
  vehicleRotateSpeed: 0.04      // 车辆旋转速度 (弧度)
};

// 遥测数据
const telemetryData = ref({
  aircraft: {
    position: { x: 8.546, y: 1.050, z: 16.756 },
    rotation: { x: 0, y: 90, z: 0 },
    gimbal: { pitch: 0, roll: 0 }
  },
  vehicle: {
    position: { x: 8.546, y: 0.05, z: 16.756 },
    rotation: { x: 0, y: 90, z: 0 }
  }
});

// 初始化场景
function initScene() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x87CEEB);

  // 主相机
  camera = new THREE.PerspectiveCamera(75, container.value.clientWidth / container.value.clientHeight, 0.1, 100);
  camera.position.set(0, 15, 10);
  camera.lookAt(0, 0, 0);

  // 无人机第一视角相机
  aircraftCamera = new THREE.PerspectiveCamera(75, 1, 0.1, 50);
  aircraftCamera.position.set(0, 0.1, -0.5);
  aircraftCamera.lookAt(0, 0, -5);

  // 小车第一视角相机
  vehicleCamera = new THREE.PerspectiveCamera(75, 1, 0.1, 50);
  vehicleCamera.position.set(0, 0.2, 0.3);
  vehicleCamera.lookAt(0, 0.2, 5);

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.value.appendChild(renderer.domElement);

  // 小车视角渲染器
  vehicleRenderer = new THREE.WebGLRenderer({ antialias: true });
  vehicleRenderer.setSize(vehicleCameraContainer.value.clientWidth, vehicleCameraContainer.value.clientHeight);
  vehicleRenderer.shadowMap.enabled = true;
  vehicleRenderer.shadowMap.type = THREE.PCFSoftShadowMap;
  vehicleCameraContainer.value.appendChild(vehicleRenderer.domElement);

  // 无人机视角渲染器
  aircraftRenderer = new THREE.WebGLRenderer({ antialias: true });
  aircraftRenderer.setSize(aircraftCameraContainer.value.clientWidth, aircraftCameraContainer.value.clientHeight);
  aircraftRenderer.shadowMap.enabled = true;
  aircraftRenderer.shadowMap.type = THREE.PCFSoftShadowMap;
  aircraftCameraContainer.value.appendChild(aircraftRenderer.domElement);

  // 轨道控制器
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.maxPolarAngle = Math.PI / 2;
  controls.minDistance = 1;
  controls.maxDistance = 50;

  // 光源 - 晴天户外明亮自然光效果
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 1.3);
  directionalLight.position.set(20, 30, 20);
  directionalLight.castShadow = true;
  directionalLight.shadow.mapSize.set(2048, 2048);
  directionalLight.shadow.camera.near = 0.5;
  directionalLight.shadow.camera.far = 120;
  directionalLight.shadow.camera.left = -50;
  directionalLight.shadow.camera.right = 50;
  directionalLight.shadow.camera.top = 60;
  directionalLight.shadow.camera.bottom = -60;
  directionalLight.shadow.bias = -0.0001;
  directionalLight.shadow.radius = 2;
  scene.add(directionalLight);

  const fillLight = new THREE.DirectionalLight(0xa8d8ea, 0.4);
  fillLight.position.set(-15, 20, -15);
  scene.add(fillLight);

  const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x88cc88, 0.3);
  scene.add(hemisphereLight);

  // 地面 - 操场高密度仿真人造草坪（带横向条纹）
  const textureLoader = new THREE.TextureLoader();
  
  const stripeWidth = 4;
  const numStripes = Math.ceil(80 / stripeWidth);
  
  for (let i = 0; i < numStripes; i++) {
    const groundGeometry = new THREE.PlaneGeometry(60, stripeWidth);
    const grassTexture = textureLoader.load('/Grass005_1K-JPG/Grass005_1K-JPG_Color.jpg');
    grassTexture.wrapS = THREE.RepeatWrapping;
    grassTexture.wrapT = THREE.RepeatWrapping;
    grassTexture.repeat.set(12, 2);
    
    const grassNormalMap = textureLoader.load('/Grass005_1K-JPG/Grass005_1K-JPG_NormalGL.jpg');
    grassNormalMap.wrapS = THREE.RepeatWrapping;
    grassNormalMap.wrapT = THREE.RepeatWrapping;
    grassNormalMap.repeat.set(12, 2);
    
    const isDarkStripe = i % 2 === 0;
    const stripeColor = isDarkStripe ? 0x4a8c2a : 0x8dd25a;
    
    const groundMaterial = new THREE.MeshStandardMaterial({
      map: grassTexture,
      normalMap: grassNormalMap,
      normalScale: new THREE.Vector2(0.12, 0.12),
      roughness: 0.7,
      metalness: 0.02,
      side: THREE.DoubleSide,
      color: stripeColor,
      envMapIntensity: 0.25
    });
    
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.01;
    ground.position.z = -40 + i * stripeWidth + stripeWidth / 2;
    ground.receiveShadow = true;
    scene.add(ground);
  }

  // 移除网格辅助线以保持草坪真实感

  // 创建迷宫
  createLeftMaze(scene);
  console.log('碰撞体数量:', getCollisionBoxCount());

  // 创建模型
  createAircraft();
  createVehicle();

  // 开始动画
  animate();

  // 窗口监听
  window.addEventListener('resize', onWindowResize);
  window.addEventListener('keydown', onKeyDown);
  window.addEventListener('keyup', onKeyUp);
}

// ====================== 键盘事件处理 ======================
function onKeyDown(e) {
  keys.value[e.key.toLowerCase()] = true;
  // 阻止方向键的默认滚动行为
  if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
    e.preventDefault();
  }
}

function onKeyUp(e) {
  keys.value[e.key.toLowerCase()] = false;
}

// ====================== 遥感控制逻辑 ======================
function handleRemoteControl() {
  const ac = telemetryData.value.aircraft;
  const vc = telemetryData.value.vehicle;
  const cfg = CONTROL_CONFIG;

  // --- 无人机控制 ---
  const yawRad = ac.rotation.y * Math.PI / 180;

  // 前进后退 (WS) - 相对于机头方向
  if (keys.value['w']) {
    const newX = ac.position.x - Math.sin(yawRad) * cfg.aircraftMoveSpeed;
    const newZ = ac.position.z - Math.cos(yawRad) * cfg.aircraftMoveSpeed;
    if (!checkCollision(newX, ac.position.y, newZ, 0.15)) {
      ac.position.x = newX;
      ac.position.z = newZ;
    }
  }
  if (keys.value['s']) {
    const newX = ac.position.x + Math.sin(yawRad) * cfg.aircraftMoveSpeed;
    const newZ = ac.position.z + Math.cos(yawRad) * cfg.aircraftMoveSpeed;
    if (!checkCollision(newX, ac.position.y, newZ, 0.15)) {
      ac.position.x = newX;
      ac.position.z = newZ;
    }
  }

  // 左转右转 (AD)
  if (keys.value['a']) ac.rotation.y += cfg.aircraftRotateSpeed * (180/Math.PI);
  if (keys.value['d']) ac.rotation.y -= cfg.aircraftRotateSpeed * (180/Math.PI);

  // 升降 (IK)
  if (keys.value['i']) ac.position.y += cfg.aircraftMoveSpeed;
  if (keys.value['k']) {
    ac.position.y -= cfg.aircraftMoveSpeed;
    if (ac.position.y < 0.2) ac.position.y = 0.2; // 防撞地
  }

  // 云台俯仰 (QE)
  if (keys.value['q']) {
    ac.gimbal.pitch -= cfg.aircraftGimbalSpeed * (180/Math.PI);
    if (ac.gimbal.pitch < -90) ac.gimbal.pitch = -90;
  }
  if (keys.value['e']) {
    ac.gimbal.pitch += cfg.aircraftGimbalSpeed * (180/Math.PI);
    if (ac.gimbal.pitch > 90) ac.gimbal.pitch = 90;
  }

  // --- 车辆控制 ---
  const vYawRad = vc.rotation.y * Math.PI / 180;

  // 前后 (方向键上下) - 相对于车头方向
  if (keys.value['arrowup']) {
    const newX = vc.position.x + Math.sin(vYawRad) * cfg.vehicleMoveSpeed;
    const newZ = vc.position.z + Math.cos(vYawRad) * cfg.vehicleMoveSpeed;
    if (!checkCollision(newX, vc.position.y, newZ, 0.25, 0.15)) {
      vc.position.x = newX;
      vc.position.z = newZ;
    }
  }
  if (keys.value['arrowdown']) {
    const newX = vc.position.x - Math.sin(vYawRad) * cfg.vehicleMoveSpeed;
    const newZ = vc.position.z - Math.cos(vYawRad) * cfg.vehicleMoveSpeed;
    if (!checkCollision(newX, vc.position.y, newZ, 0.25, 0.15)) {
      vc.position.x = newX;
      vc.position.z = newZ;
    }
  }

  // 转向 (方向键左右)
  if (keys.value['arrowleft']) vc.rotation.y += cfg.vehicleRotateSpeed * (180/Math.PI);
  if (keys.value['arrowright']) vc.rotation.y -= cfg.vehicleRotateSpeed * (180/Math.PI);
}

// ====================== 模型创建函数 ======================
function createAircraft() {
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.05, 0.3), new THREE.MeshLambertMaterial({ color: 0xFF4500 }));
  aircraft = body;
  aircraft.position.set(0, 2, 0);
  scene.add(aircraft);

  const wingGeo = new THREE.BoxGeometry(0.6, 0.01, 0.02);
  const wingMat = new THREE.MeshLambertMaterial({ color: 0xFFFFFF });
  const wing1 = new THREE.Mesh(wingGeo, wingMat);
  wing1.position.set(0, 0.02, 0);
  aircraft.add(wing1);
  const wing2 = new THREE.Mesh(wingGeo, wingMat);
  wing2.position.set(0, -0.02, 0);
  wing2.rotation.x = Math.PI;
  aircraft.add(wing2);

  const propGeo = new THREE.BoxGeometry(0.2, 0.01, 0.02);
  const propMat = new THREE.MeshLambertMaterial({ color: 0x000000 });
  const prop1 = new THREE.Mesh(propGeo, propMat);
  prop1.position.set(0.15, 0.02, 0.15);
  aircraft.add(prop1);
  const prop2 = new THREE.Mesh(propGeo, propMat);
  prop2.position.set(-0.15, 0.02, 0.15);
  aircraft.add(prop2);

  gimbal = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.06, 0.06), new THREE.MeshLambertMaterial({ color: 0x808080 }));
  gimbal.position.set(0, -0.05, 0);
  aircraft.add(gimbal);
  gimbal.add(aircraftCamera);
}

function createVehicle() {
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 0.5), new THREE.MeshLambertMaterial({ color: 0xFFFFFF }));
  vehicle = body;
  vehicle.position.set(0, 0.05, 0);
  scene.add(vehicle);

  const wheelGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.02, 16);
  const wheelMat = new THREE.MeshLambertMaterial({ color: 0x333333 });
  const wheels = [[0.12, 0, 0.18], [-0.12, 0, 0.18], [0.12, 0, -0.18], [-0.12, 0, -0.18]];
  wheels.forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    wheel.rotation.z = Math.PI / 2;
    wheel.position.set(...pos);
    vehicle.add(wheel);
  });

  const textureLoader = new THREE.TextureLoader();
  const arucoTexture = textureLoader.load(arucoCode);
  arucoTexture.wrapS = THREE.ClampToEdgeWrapping;
  arucoTexture.wrapT = THREE.ClampToEdgeWrapping;
  const aruco = new THREE.Mesh(new THREE.PlaneGeometry(0.1, 0.1), new THREE.MeshBasicMaterial({ map: arucoTexture, side: THREE.DoubleSide }));
  aruco.position.set(0, 0.06, 0);
  aruco.rotation.x = -Math.PI / 2;
  vehicle.add(aruco);

  // 添加小车相机
  vehicle.add(vehicleCamera);
}

// ====================== 动画与控制 ======================
function animate() {
  requestAnimationFrame(animate);

  // 处理遥感输入
  handleRemoteControl();

  // 螺旋桨旋转
  if (aircraft && aircraft.children.length >= 4) {
    aircraft.children[2].rotation.y += 0.3;
    aircraft.children[3].rotation.y += 0.3;
  }

  updatePositions();

  // 跟随视角
  if (cameraMode.value === 'follow' && aircraft) {
    camera.position.set(aircraft.position.x + 3, aircraft.position.y + 2, aircraft.position.z + 3);
    camera.lookAt(aircraft.position);
  }

  let currentCamera = camera;
  if (cameraMode.value === 'camera' && aircraft) {
    currentCamera = aircraftCamera;
  }

  controls.update();
  renderer.render(scene, currentCamera);

  // 渲染小车视角
  if (vehicleRenderer && vehicleCamera) {
    vehicleRenderer.render(scene, vehicleCamera);
  }

  // 渲染无人机视角
  if (aircraftRenderer && aircraftCamera) {
    aircraftRenderer.render(scene, aircraftCamera);
  }
}

function updatePositions() {
  if (aircraft) {
    aircraft.position.copy(telemetryData.value.aircraft.position);
    aircraft.rotation.set(
      telemetryData.value.aircraft.rotation.x * Math.PI / 180,
      telemetryData.value.aircraft.rotation.y * Math.PI / 180,
      telemetryData.value.aircraft.rotation.z * Math.PI / 180
    );
    aircraftPosition.value = `(${telemetryData.value.aircraft.position.x.toFixed(3)}, ${telemetryData.value.aircraft.position.y.toFixed(3)}, ${telemetryData.value.aircraft.position.z.toFixed(3)})`;
  }

  if (gimbal) {
    gimbal.rotation.x = telemetryData.value.aircraft.gimbal.pitch * Math.PI / 180;
    gimbal.rotation.z = telemetryData.value.aircraft.gimbal.roll * Math.PI / 180;
  }

  if (vehicle) {
    vehicle.position.copy(telemetryData.value.vehicle.position);
    vehicle.rotation.y = telemetryData.value.vehicle.rotation.y * Math.PI / 180;
    vehiclePosition.value = `(${telemetryData.value.vehicle.position.x.toFixed(3)}, ${telemetryData.value.vehicle.position.y.toFixed(3)}, ${telemetryData.value.vehicle.position.z.toFixed(3)})`;
  }
}

// 监听遥测数据变化
watch(telemetryData, (newVal) => {
  console.log('遥测数据变化:', newVal.aircraft.position, newVal.vehicle.position);
}, { deep: true });

function onWindowResize() {
  camera.aspect = container.value.clientWidth / container.value.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  if (vehicleRenderer && vehicleCameraContainer.value) {
    vehicleRenderer.setSize(vehicleCameraContainer.value.clientWidth, vehicleCameraContainer.value.clientHeight);
  }
  if (aircraftRenderer && aircraftCameraContainer.value) {
    aircraftRenderer.setSize(aircraftCameraContainer.value.clientWidth, aircraftCameraContainer.value.clientHeight);
  }
}

function resetScene() {
  telemetryData.value = {
    aircraft: { position: { x: 8.546, y: 1.050, z: 16.756 }, rotation: { x: 0, y: 90, z: 0 }, gimbal: { pitch: 0, roll: 0 } },
    vehicle: { position: { x: 8.546, y: 0.05, z: 16.756 }, rotation: { x: 0, y: 90, z: 0 } }
  };
  if (cameraMode.value === 'orbit') {
    camera.position.set(8.546, 15, 18.756);
    camera.lookAt(8.546, 0, 16.756);
  }
}

// 暴露API (保留原有接口，可与键盘控制共存)
defineExpose({
  updateTelemetry: (data) => {
    if (data.type === 'aircraft_telemetry_gnss') {
      telemetryData.value.aircraft.position.x = data.data.gps[0];
      telemetryData.value.aircraft.position.z = data.data.gps[1];
      if (data.data.altitude) {
        telemetryData.value.aircraft.position.y = parseFloat(data.data.altitude);
      }
    } else if (data.type === 'vehicle_telemetry_gnss') {
      telemetryData.value.vehicle.position.x = data.data.gps[0];
      telemetryData.value.vehicle.position.z = data.data.gps[1];
    } else if (data.type === 'aircraft_telemetry_gimbal') {
      telemetryData.value.aircraft.gimbal.pitch = data.data.pitch;
      telemetryData.value.aircraft.gimbal.roll = data.data.roll;
    }
  },
  captureImage: () => {
    if (aircraftCamera && aircraftRenderer) {
      // 使用无人机视角的渲染器渲染场景
      aircraftRenderer.render(scene, aircraftCamera);
      const imageUrl = aircraftRenderer.domElement.toDataURL('image/jpeg');
      return imageUrl;
    }
    return null;
  }
});

// 生命周期
onMounted(() => {
  initScene();
  connectWebSocket();
});

onUnmounted(() => {
  disconnectWebSocket();
  window.removeEventListener('resize', onWindowResize);
  window.removeEventListener('keydown', onKeyDown);
  window.removeEventListener('keyup', onKeyUp);
  if (renderer) {
    renderer.dispose();
  }
  if (vehicleRenderer) {
    vehicleRenderer.dispose();
  }
  if (aircraftRenderer) {
    aircraftRenderer.dispose();
  }
});

</script>

<style scoped>
.three-scene {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  margin: 0;
  position: relative;
}

.auto-controls-fixed {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 12px;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 6px;
  border: 1px solid #ddd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.scene-top {
  display: flex;
  flex-direction: row;
  flex: 1;
  gap: 5px;
  min-height: 0;
}

.camera-sidebar {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex-shrink: 0;
  width: 25%;
}

.camera-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 3px;
}

.camera-label {
  font-size: 14px;
  font-weight: bold;
  color: #333;
  padding: 3px 6px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
}

.camera-position {
  font-size: 12px;
  color: #555;
  padding: 2px 6px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  font-family: monospace;
}

.vehicle-camera-container {
  width: 100%;
  flex: 1;
  border: 2px solid #4CAF50;
  border-radius: 8px;
  overflow: hidden;
  min-height: 0;
}

.aircraft-camera-container {
  width: 100%;
  flex: 1;
  border: 2px solid #FF4500;
  border-radius: 8px;
  overflow: hidden;
  min-height: 0;
}

.scene-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 3px;
}

.scene-label {
  font-size: 14px;
  font-weight: bold;
  color: #333;
  padding: 3px 6px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
}

.start-btn {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
}

.start-btn:hover {
  background-color: #45a049;
}

.start-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.stop-btn {
  padding: 8px 16px;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
}

.stop-btn:hover {
  background-color: #da190b;
}

.stop-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.status-text {
  font-size: 14px;
  color: #333;
  padding: 4px 8px;
  background-color: rgba(240, 240, 240, 0.95);
  border-radius: 4px;
  font-weight: 500;
}

.scene-container {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  min-height: 0;
}
</style>