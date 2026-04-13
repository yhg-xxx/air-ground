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
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// 导入ARUCO码图片
import arucoCode from './icons/2号车.png';

const container = ref(null);
let scene, camera, aircraftCamera, renderer, controls;
let aircraft, vehicle, gimbal;
let aircraftPosition = ref('(0, 0, 0)');
let vehiclePosition = ref('(0, 0, 0)');
let cameraMode = ref('orbit'); // orbit, follow, or camera

// 模拟数据
const telemetryData = ref({
  aircraft: {
    position: { x: 0, y: 10, z: 0 },
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
  // 创建场景
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x87CEEB); // 天空蓝
  
  // 创建主相机
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(50, 50, 50);
  camera.lookAt(0, 0, 0);
  
  // 创建飞机摄像头
  aircraftCamera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  aircraftCamera.position.set(0, 0.2, -3); // 位于无人机前方，稍微向下看
  aircraftCamera.lookAt(0, 0, -10); // 看向无人机前方远处
  
  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  container.value.appendChild(renderer.domElement);
  
  // 添加轨道控制器
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  
  // 添加光源
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(50, 50, 50);
  scene.add(directionalLight);
  
  // 创建地面
  const groundGeometry = new THREE.PlaneGeometry(100, 100);
  const groundMaterial = new THREE.MeshLambertMaterial({ 
    color: 0x8FBC8F, // 草绿色
    side: THREE.DoubleSide 
  });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.5;
  scene.add(ground);
  
  // 创建网格
  const gridHelper = new THREE.GridHelper(100, 20);
  scene.add(gridHelper);
  
  // 创建无人机
  createAircraft();
  
  // 创建车辆
  createVehicle();
  
  // 开始动画
  animate();
  
  // 监听窗口大小变化
  window.addEventListener('resize', onWindowResize);
}

// 创建无人机
function createAircraft() {
  // 无人机主体
  const bodyGeometry = new THREE.BoxGeometry(2, 0.5, 3);
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0xFF4500 }); // 橙红色
  aircraft = new THREE.Mesh(bodyGeometry, bodyMaterial);
  aircraft.position.y = 10;
  scene.add(aircraft);
  
  // 无人机机翼
  const wingGeometry = new THREE.BoxGeometry(6, 0.1, 0.5);
  const wingMaterial = new THREE.MeshLambertMaterial({ color: 0xFFFFFF });
  
  const wing1 = new THREE.Mesh(wingGeometry, wingMaterial);
  wing1.position.set(0, 0.3, 0);
  aircraft.add(wing1);
  
  const wing2 = new THREE.Mesh(wingGeometry, wingMaterial);
  wing2.position.set(0, -0.3, 0);
  wing2.rotation.x = Math.PI;
  aircraft.add(wing2);
  
  // 无人机螺旋桨
  const propellerGeometry = new THREE.BoxGeometry(0.5, 0.1, 3);
  const propellerMaterial = new THREE.MeshLambertMaterial({ color: 0x000000 });
  
  const propeller1 = new THREE.Mesh(propellerGeometry, propellerMaterial);
  propeller1.position.set(3, 0, 0);
  aircraft.add(propeller1);
  
  const propeller2 = new THREE.Mesh(propellerGeometry, propellerMaterial);
  propeller2.position.set(-3, 0, 0);
  aircraft.add(propeller2);
  
  // 创建云台
  const gimbalGeometry = new THREE.BoxGeometry(0.6, 0.6, 0.6);
  const gimbalMaterial = new THREE.MeshLambertMaterial({ color: 0x808080 });
  gimbal = new THREE.Mesh(gimbalGeometry, gimbalMaterial);
  gimbal.position.set(0, 0, -1.5); // 位于无人机前部
  aircraft.add(gimbal);
  
  // 将摄像头添加到云台上
  aircraftCamera.position.set(0, 0, -1); // 调整摄像头位置，使其在云台前方
  gimbal.add(aircraftCamera);
}

// 创建车辆
function createVehicle() {
  // 车辆主体
  const bodyGeometry = new THREE.BoxGeometry(4, 1, 5); // 扩大小车宽度
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0xFFFFFF }); // 白色
  vehicle = new THREE.Mesh(bodyGeometry, bodyMaterial);
  vehicle.position.y = 0.5;
  scene.add(vehicle);
  
  // 车轮
  const wheelGeometry = new THREE.CylinderGeometry(0.5, 0.5, 0.2, 32);
  const wheelMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
  
  const wheels = [
    { position: new THREE.Vector3(1.5, 0, 1.5) },
    { position: new THREE.Vector3(-1.5, 0, 1.5) },
    { position: new THREE.Vector3(1.5, 0, -1.5) },
    { position: new THREE.Vector3(-1.5, 0, -1.5) }
  ];
  
  wheels.forEach(wheel => {
    const wheelMesh = new THREE.Mesh(wheelGeometry, wheelMaterial);
    wheelMesh.rotation.z = Math.PI / 2;
    wheelMesh.position.copy(wheel.position);
    vehicle.add(wheelMesh);
  });
  
  // 添加ARUCO码到车顶上
  const textureLoader = new THREE.TextureLoader();
  const arucoTexture = textureLoader.load(arucoCode);
  
  // 设置纹理参数，确保图片正确显示为正方形
  arucoTexture.wrapS = THREE.ClampToEdgeWrapping;
  arucoTexture.wrapT = THREE.ClampToEdgeWrapping;
  arucoTexture.minFilter = THREE.LinearFilter;
  arucoTexture.magFilter = THREE.LinearFilter;
  
  // 创建正方形平面，确保ARUCO码是正方形
  const arucoSize = 3.5; // 正方形大小，与扩宽后的车辆宽度匹配
  const arucoGeometry = new THREE.PlaneGeometry(arucoSize, arucoSize);
  const arucoMaterial = new THREE.MeshBasicMaterial({ 
    map: arucoTexture, 
    side: THREE.DoubleSide
  });
  const arucoMesh = new THREE.Mesh(arucoGeometry, arucoMaterial);
  
  // 放置在车顶中央，保持水平
  arucoMesh.position.set(0, 0.6, 0);
  arucoMesh.rotation.x = -Math.PI / 2; // 旋转-90度，使其水平
  
  vehicle.add(arucoMesh);
}

// 动画循环
function animate() {
  requestAnimationFrame(animate);
  
  // 更新螺旋桨旋转
  if (aircraft) {
    aircraft.children[2].rotation.x += 0.1;
    aircraft.children[3].rotation.x += 0.1;
  }
  
  // 更新无人机和车辆位置
  updatePositions();
  
  // 更新相机位置
  if (cameraMode.value === 'follow' && aircraft) {
    camera.position.set(
      aircraft.position.x + 20,
      aircraft.position.y + 10,
      aircraft.position.z + 20
    );
    camera.lookAt(aircraft.position);
  }
  
  // 使用当前模式的相机进行渲染
  let currentCamera = camera;
  if (cameraMode.value === 'camera' && aircraft) {
    currentCamera = aircraftCamera;
  }
  
  controls.update();
  renderer.render(scene, currentCamera);
}

// 更新位置
function updatePositions() {
  if (aircraft) {
    aircraft.position.x = telemetryData.value.aircraft.position.x;
    aircraft.position.y = telemetryData.value.aircraft.position.y;
    aircraft.position.z = telemetryData.value.aircraft.position.z;
    aircraft.rotation.x = telemetryData.value.aircraft.rotation.x;
    aircraft.rotation.y = telemetryData.value.aircraft.rotation.y;
    aircraft.rotation.z = telemetryData.value.aircraft.rotation.z;
    
    aircraftPosition.value = `(${telemetryData.value.aircraft.position.x.toFixed(2)}, ${telemetryData.value.aircraft.position.y.toFixed(2)}, ${telemetryData.value.aircraft.position.z.toFixed(2)})`;
  }
  
  // 更新云台状态
  if (gimbal) {
    gimbal.rotation.x = telemetryData.value.aircraft.gimbal.pitch * Math.PI / 180; // 转换为弧度
    gimbal.rotation.z = telemetryData.value.aircraft.gimbal.roll * Math.PI / 180; // 转换为弧度
  }
  
  if (vehicle) {
    vehicle.position.x = telemetryData.value.vehicle.position.x;
    vehicle.position.y = telemetryData.value.vehicle.position.y;
    vehicle.position.z = telemetryData.value.vehicle.position.z;
    vehicle.rotation.x = telemetryData.value.vehicle.rotation.x;
    vehicle.rotation.y = telemetryData.value.vehicle.rotation.y;
    vehicle.rotation.z = telemetryData.value.vehicle.rotation.z;
    
    vehiclePosition.value = `(${telemetryData.value.vehicle.position.x.toFixed(2)}, ${telemetryData.value.vehicle.position.y.toFixed(2)}, ${telemetryData.value.vehicle.position.z.toFixed(2)})`;
  }
}

// 窗口大小变化处理
function onWindowResize() {
  camera.aspect = container.value.clientWidth / container.value.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
}

// 切换相机模式
function toggleCamera() {
  // 循环切换相机模式：orbit → follow → camera → orbit
  if (cameraMode.value === 'orbit') {
    cameraMode.value = 'follow';
  } else if (cameraMode.value === 'follow') {
    cameraMode.value = 'camera';
  } else {
    cameraMode.value = 'orbit';
    // 重置相机位置
    camera.position.set(50, 50, 50);
    camera.lookAt(0, 0, 0);
  }
}

// 重置场景
function resetScene() {
  telemetryData.value = {
    aircraft: {
      position: { x: 0, y: 10, z: 0 },
      rotation: { x: 0, y: 0, z: 0 }
    },
    vehicle: {
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 }
    }
  };
  
  if (cameraMode.value === 'orbit') {
    camera.position.set(50, 50, 50);
    camera.lookAt(0, 0, 0);
  }
}

// 暴露更新遥测数据的方法
defineExpose({
  updateTelemetry: (data) => {
    if (data.type === 'aircraft_telemetry_gnss') {
      // 调整GPS坐标，将其缩放到合理范围
      telemetryData.value.aircraft.position.x = (data.data.gps[0] - 0.5687) * 1000;
      telemetryData.value.aircraft.position.z = (data.data.gps[1] - 1.3854) * 1000;
      // 更新高度
      if (data.data.altitude) {
        telemetryData.value.aircraft.position.y = parseFloat(data.data.altitude);
      }
    } else if (data.type === 'vehicle_telemetry_gnss') {
      // 调整GPS坐标，将其缩放到合理范围
      telemetryData.value.vehicle.position.x = (data.data.gps[0] - 0.5687) * 1000;
      telemetryData.value.vehicle.position.z = (data.data.gps[1] - 1.3854) * 1000;
    } else if (data.type === 'aircraft_telemetry_gimbal') {
      // 更新云台状态
      if (data.data.pitch !== undefined) {
        telemetryData.value.aircraft.gimbal.pitch = data.data.pitch;
      }
      if (data.data.roll !== undefined) {
        telemetryData.value.aircraft.gimbal.roll = data.data.roll;
      }
    }
  },
  
  // 捕获无人机摄像头视角的图片
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

// 生命周期钩子
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
  height: 600px;
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
