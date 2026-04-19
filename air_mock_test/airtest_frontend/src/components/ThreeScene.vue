<template>
  <div class="three-scene">
    <div ref="container" class="scene-container"></div>
    <div class="scene-controls">
      <h3>3D 场景控制</h3>
      <button @click="toggleCamera">切换视角</button>
      <button @click="resetScene">重置场景</button>
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

const container = ref(null);
let scene, camera, aircraftCamera, renderer, controls;
let aircraft, vehicle, gimbal;
let aircraftPosition = ref('(0, 0, 0)');
let vehiclePosition = ref('(0, 0, 0)');
let cameraMode = ref('orbit'); // orbit, follow, camera

// ====================== 真实尺寸配置（50m×25m 1:1）======================
const MAZE_CONFIG = {
  gridCols: 480,
  gridRows: 1200,
  realWidth: 25,
  realLength: 50,
  cellSize: 25 / 480,
  wallHeight: 0.8,
  wallThickness: 0.3,
  archHeight: 2,
  archWidth: 2,
  offsetX: -12.5,
  offsetZ: -25
};

// 遥测数据
const telemetryData = ref({
  aircraft: {
    position: { x: 0, y: 2, z: 0 },
    rotation: { x: 0, y: 0, z: 0 },
    gimbal: { pitch: 0, roll: 0 }
  },
  vehicle: {
    position: { x: 0, y: 0, z: 0 },
    rotation: { x: 0, y: 0, z: 0 }
  }
});

// 初始化场景
function initScene() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x87CEEB);

  // 主相机
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 15, 10);
  camera.lookAt(0, 0, 0);

  // 无人机第一视角相机
  aircraftCamera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 50);
  aircraftCamera.position.set(0, 0.1, -0.5);
  aircraftCamera.lookAt(0, 0, -5);

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.value.appendChild(renderer.domElement);

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
  createLeftMaze();

  // 创建模型
  createAircraft();
  createVehicle();

  // 开始动画
  animate();

  // 窗口监听
  window.addEventListener('resize', onWindowResize);
}

// ====================== 迷宫生成函数 ======================
function createLeftMaze() {
  const mazeGroup = new THREE.Group();
  scene.add(mazeGroup);

  const wallMaterial = new THREE.MeshLambertMaterial({ color: 0xff3333 });
  const stripeMaterial = new THREE.MeshLambertMaterial({ color: 0xffff00 });
  const archMaterial = new THREE.MeshLambertMaterial({ color: 0x0066ff, transparent: true, opacity: 0.8 });

  createMazeBoundary(mazeGroup, wallMaterial, stripeMaterial);
  createInnerWalls(mazeGroup, wallMaterial, stripeMaterial);
  createArches(mazeGroup, archMaterial);
}

function createMazeBoundary(group, wallMat, stripeMat) {
  const { wallHeight, wallThickness, offsetX, offsetZ } = MAZE_CONFIG;

  // 左边界
  createWall(group, wallMat, stripeMat, offsetX, wallHeight/2, 0, wallThickness, wallHeight, 50);
  // 中间分隔墙（已右移6.25米，匹配航拍图）
  createWall(group, wallMat, stripeMat, 6.25, wallHeight/2, 0, wallThickness, wallHeight, 50);
  // 上边界（已延长至新的中间墙位置）
  createWall(group, wallMat, stripeMat, -3.125, wallHeight/2, offsetZ, 18.75, wallHeight, wallThickness);
  // 下边界（已延长至新的中间墙位置）
  createWall(group, wallMat, stripeMat, -3.125, wallHeight/2, offsetZ + 50, 18.75, wallHeight, wallThickness);
}

function createInnerWalls(group, wallMat, stripeMat) {
  const { cellSize, wallHeight, wallThickness } = MAZE_CONFIG;

  const walls = [
    { x1: 0, x2: 200, z1: 90, z2: 100 },
    { x1: 220, x2: 320, z1: 90, z2: 100 },
    { x1: 120, x2: 130, z1: 130, z2: 210 },
    { x1: 120, x2: 200, z1: 210, z2: 220 },
    { x1: 200, x2: 210, z1: 210, z2: 290 },
    { x1: 120, x2: 280, z1: 290, z2: 300 },
    { x1: 120, x2: 130, z1: 300, z2: 370 },
    { x1: 200, x2: 320, z1: 370, z2: 380 },
    { x1: 0, x2: 120, z1: 460, z2: 470 },
    { x1: 160, x2: 320, z1: 460, z2: 470 },
    { x1: 80, x2: 320, z1: 550, z2: 560 },
    { x1: 0, x2: 200, z1: 630, z2: 640 },
    { x1: 0, x2: 120, z1: 720, z2: 730 },
    { x1: 160, x2: 320, z1: 720, z2: 730 },
    { x1: 80, x2: 280, z1: 820, z2: 830 },
    { x1: 280, x2: 290, z1: 820, z2: 900 },
    { x1: 120, x2: 200, z1: 900, z2: 910 },
    { x1: 120, x2: 130, z1: 900, z2: 980 },
    { x1: 0, x2: 240, z1: 970, z2: 980 },
    { x1: 200, x2: 210, z1: 970, z2: 1050 },
    { x1: 80, x2: 200, z1: 1050, z2: 1060 }
  ];

  walls.forEach(wall => {
    const realX1 = (wall.x1 - 240) * cellSize;
    const realX2 = (wall.x2 - 240) * cellSize;
    const realZ1 = (wall.z1 - 600) * cellSize;
    const realZ2 = (wall.z2 - 600) * cellSize;

    const width = Math.abs(realX2 - realX1);
    const depth = Math.abs(realZ2 - realZ1);
    const centerX = (realX1 + realX2) / 2;
    const centerZ = (realZ1 + realZ2) / 2;

    createWall(group, wallMat, stripeMat, centerX, wallHeight/2, centerZ, width, wallHeight, depth);
  });
}

function createArches(group, archMat) {
  const { cellSize, archHeight, archWidth } = MAZE_CONFIG;

  const arches = [
    { x: 320, z: 100 }, { x: 320, z: 930 }, { x: 120, z: 990 },
    { x: 280, z: 990 }, { x: 20, z: 1080 }, { x: 200, z: 1080 },
    { x: 360, z: 1110 }, { x: 80, z: 1160 }, { x: 320, z: 1160 }
  ];

  arches.forEach(arch => {
    const realX = (arch.x - 240) * cellSize;
    const realZ = (arch.z - 600) * cellSize;

    createArchPillar(group, archMat, realX - archWidth/2, realZ);
    createArchPillar(group, archMat, realX + archWidth/2, realZ);

    const beam = new THREE.Mesh(
      new THREE.BoxGeometry(archWidth, 0.15, 0.2),
      archMat
    );
    beam.position.set(realX, archHeight, realZ);
    beam.castShadow = true;
    group.add(beam);
  });
}

function createWall(group, mainMat, stripeMat, x, y, z, width, height, depth) {
  const wall = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), mainMat);
  wall.position.set(x, y, z);
  wall.castShadow = true;
  wall.receiveShadow = true;
  group.add(wall);

  const stripe1 = new THREE.Mesh(new THREE.BoxGeometry(width, 0.1, depth + 0.01), stripeMat);
  stripe1.position.set(x, y + height*0.3, z);
  stripe1.castShadow = true;
  group.add(stripe1);

  const stripe2 = new THREE.Mesh(new THREE.BoxGeometry(width, 0.1, depth + 0.01), stripeMat);
  stripe2.position.set(x, y + height*0.7, z);
  stripe2.castShadow = true;
  group.add(stripe2);
}

function createArchPillar(group, mat, x, z) {
  const pillar = new THREE.Mesh(
    new THREE.BoxGeometry(0.15, MAZE_CONFIG.archHeight, 0.15),
    mat
  );
  pillar.position.set(x, MAZE_CONFIG.archHeight/2, z);
  pillar.castShadow = true;
  group.add(pillar);
}

// ====================== 模型创建函数 (改回简单的索引结构) ======================
function createAircraft() {
  // 真实无人机尺寸：约30cm×30cm
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.3, 0.05, 0.3),
    new THREE.MeshLambertMaterial({ color: 0xFF4500 })
  );
  aircraft = body;
  aircraft.position.set(0, 2, 0);
  scene.add(aircraft);

  // 机翼 (children[0], [1])
  const wingGeo = new THREE.BoxGeometry(0.6, 0.01, 0.02);
  const wingMat = new THREE.MeshLambertMaterial({ color: 0xFFFFFF });
  const wing1 = new THREE.Mesh(wingGeo, wingMat);
  wing1.position.set(0, 0.02, 0);
  aircraft.add(wing1);

  const wing2 = new THREE.Mesh(wingGeo, wingMat);
  wing2.position.set(0, -0.02, 0);
  wing2.rotation.x = Math.PI;
  aircraft.add(wing2);

  // 螺旋桨 (children[2], [3]) - 注意这里的索引要和 animate 里对应
  const propGeo = new THREE.BoxGeometry(0.2, 0.01, 0.02);
  const propMat = new THREE.MeshLambertMaterial({ color: 0x000000 });

  const prop1 = new THREE.Mesh(propGeo, propMat);
  prop1.position.set(0.15, 0.02, 0.15);
  aircraft.add(prop1); // children[2]

  const prop2 = new THREE.Mesh(propGeo, propMat);
  prop2.position.set(-0.15, 0.02, 0.15);
  aircraft.add(prop2); // children[3]

  // 云台 (children[4])
  gimbal = new THREE.Mesh(
    new THREE.BoxGeometry(0.06, 0.06, 0.06),
    new THREE.MeshLambertMaterial({ color: 0x808080 })
  );
  gimbal.position.set(0, -0.05, 0);
  aircraft.add(gimbal);

  // 摄像头挂载在云台上
  gimbal.add(aircraftCamera);
}

function createVehicle() {
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.3, 0.1, 0.5),
    new THREE.MeshLambertMaterial({ color: 0xFFFFFF })
  );
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

  const aruco = new THREE.Mesh(
    new THREE.PlaneGeometry(0.1, 0.1),
    new THREE.MeshBasicMaterial({ map: arucoTexture, side: THREE.DoubleSide })
  );
  aruco.position.set(0, 0.06, 0);
  aruco.rotation.x = -Math.PI / 2;
  vehicle.add(aruco);
}

// ====================== 动画与控制 (改回简单逻辑) ======================
function animate() {
  requestAnimationFrame(animate);

  // 螺旋桨旋转 (使用简单的索引，和旧代码保持一致)
  if (aircraft && aircraft.children.length >= 4) {
    aircraft.children[2].rotation.y += 0.3;
    aircraft.children[3].rotation.y += 0.3;
  }

  updatePositions();

  // 跟随视角
  if (cameraMode.value === 'follow' && aircraft) {
    camera.position.set(
      aircraft.position.x + 3,
      aircraft.position.y + 2,
      aircraft.position.z + 3
    );
    camera.lookAt(aircraft.position);
  }

  // 选择当前相机
  let currentCamera = camera;
  if (cameraMode.value === 'camera' && aircraft) {
    currentCamera = aircraftCamera;
  }

  controls.update();
  renderer.render(scene, currentCamera);
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

  // 同时也要更新无人机相机的宽高比，防止抓拍时变形
  aircraftCamera.aspect = container.value.clientWidth / container.value.clientHeight;
  aircraftCamera.updateProjectionMatrix();

  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
}

function toggleCamera() {
  const modes = ['orbit', 'follow', 'camera'];
  const currentIndex = modes.indexOf(cameraMode.value);
  cameraMode.value = modes[(currentIndex + 1) % modes.length];

  if (cameraMode.value === 'orbit') {
    camera.position.set(0, 15, 10);
    camera.lookAt(0, 0, 0);
  }
}

function resetScene() {
  telemetryData.value = {
    aircraft: { position: { x: 0, y: 2, z: 0 }, rotation: { x: 0, y: 0, z: 0 }, gimbal: { pitch: 0, roll: 0 } },
    vehicle: { position: { x: 0, y: 0, z: 0 }, rotation: { x: 0, y: 0, z: 0 } }
  };

  if (cameraMode.value === 'orbit') {
    camera.position.set(0, 15, 10);
    camera.lookAt(0, 0, 0);
  }
}

// 暴露API (完全恢复你提供的旧代码中最稳定的版本)
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

  // 捕获无人机摄像头视角的图片 (完全照搬你提供的旧代码逻辑)
  captureImage: () => {
    if (aircraftCamera) {
      // 直接渲染到默认的渲染目标（DOM元素）
      const originalCamera = cameraMode.value;
      cameraMode.value = 'camera';

      // 强制渲染一帧
      renderer.render(scene, aircraftCamera);

      // 将渲染结果转换为图片URL
      const imageUrl = renderer.domElement.toDataURL('image/jpeg');

      // 恢复原来的相机模式
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
  if (renderer) {
    renderer.dispose();
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

.scene-container {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.scene-controls {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

button {
  margin: 0 5px;
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #45a049;
}

.status {
  font-size: 14px;
  color: #333;
}
</style>