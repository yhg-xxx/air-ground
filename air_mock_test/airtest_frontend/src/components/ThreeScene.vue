<template>
  <div class="three-scene">
    <div class="scene-top">
      <div class="camera-sidebar">
        <div ref="vehicleCameraContainer" class="vehicle-camera-container"></div>
        <div ref="aircraftCameraContainer" class="aircraft-camera-container"></div>
      </div>
      <div ref="container" class="scene-container"></div>
    </div>
    <div class="scene-controls">
      <h3>3D 场景控制</h3>
      <div class="control-buttons">
        <button @click="toggleCamera">切换视角</button>
        <button @click="resetScene">重置场景</button>
      </div>
      <div class="control-instructions">
        <h4>遥感操作：</h4>
        <p><strong>无人机：</strong>WS前进后退 | AD左转右转 | IK升降 | QE云台俯仰</p>
        <p><strong>车辆：</strong>↑↓前后 | ←→转向</p>
      </div>
      <div class="status">
        <p>无人机位置: {{ aircraftPosition }}</p>
        <p>车辆位置: {{ vehiclePosition }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
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
    rotation: { x: 0, y: 0, z: 0 },
    gimbal: { pitch: 0, roll: 0 }
  },
  vehicle: {
    position: { x: 8.546, y: 0.05, z: 16.756 },
    rotation: { x: 0, y: 0, z: 0 }
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
  vehicleRenderer.setSize(200, 200);
  vehicleRenderer.shadowMap.enabled = true;
  vehicleRenderer.shadowMap.type = THREE.PCFSoftShadowMap;
  vehicleCameraContainer.value.appendChild(vehicleRenderer.domElement);

  // 无人机视角渲染器
  aircraftRenderer = new THREE.WebGLRenderer({ antialias: true });
  aircraftRenderer.setSize(200, 200);
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

  // 光源
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(10, 20, 10);
  directionalLight.castShadow = true;
  directionalLight.shadow.mapSize.set(2048, 2048);
  scene.add(directionalLight);

  // 地面
  const groundGeometry = new THREE.PlaneGeometry(60, 80);
  const groundMaterial = new THREE.MeshLambertMaterial({
    color: 0x7CFC00,
    side: THREE.DoubleSide
  });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.01;
  ground.receiveShadow = true;
  scene.add(ground);

  // 网格辅助
  const gridHelper = new THREE.GridHelper(60, 60, 0x000000, 0xcccccc);
  scene.add(gridHelper);

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

function onWindowResize() {
  camera.aspect = container.value.clientWidth / container.value.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  if (vehicleRenderer) {
    vehicleRenderer.setSize(200, 200);
  }
  if (aircraftRenderer) {
    aircraftRenderer.setSize(200, 200);
  }
}

function resetScene() {
  telemetryData.value = {
    aircraft: { position: { x: 8.546, y: 1.050, z: 16.756 }, rotation: { x: 0, y: 0, z: 0 }, gimbal: { pitch: 0, roll: 0 } },
    vehicle: { position: { x: 8.546, y: 0.05, z: 16.756 }, rotation: { x: 0, y: 0, z: 0 } }
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
    if (aircraftCamera) {
      const originalCamera = cameraMode.value;
      cameraMode.value = 'camera';
      renderer.render(scene, aircraftCamera);
      const imageUrl = renderer.domElement.toDataURL('image/jpeg');
      cameraMode.value = originalCamera;
      return imageUrl;
    }
    return null;
  }
});

// 生命周期
onMounted(() => {
  initScene();
});

onUnmounted(() => {
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
  height: 700px;
  margin: 20px 0;
}

.scene-top {
  display: flex;
  flex-direction: row;
  flex: 1;
  gap: 10px;
  min-height: 0;
}

.camera-sidebar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.vehicle-camera-container {
  width: 200px;
  height: 200px;
  border: 2px solid #4CAF50;
  border-radius: 8px;
  overflow: hidden;
}

.aircraft-camera-container {
  width: 200px;
  height: 200px;
  border: 2px solid #FF4500;
  border-radius: 8px;
  overflow: hidden;
}

.scene-container {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  min-width: 0;
}

.scene-controls {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 10px;
}

.control-buttons {
  display: flex;
  gap: 8px;
}

.control-instructions {
  font-size: 12px;
  color: #555;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.control-instructions h4 {
  margin: 0 0 5px 0;
  font-size: 13px;
  color: #333;
}

.control-instructions p {
  margin: 3px 0;
}

button {
  margin: 0;
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background-color: #45a049;
}

.status {
  font-size: 14px;
  color: #333;
  font-family: monospace;
}
</style>