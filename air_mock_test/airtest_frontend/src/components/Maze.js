import * as THREE from 'three';

// ====================== 真实尺寸配置（50m×25m 1:1）======================
const MAZE_CONFIG = {
  gridCols: 480,
  gridRows: 1200,
  realWidth: 25,
  realLength: 50,
  cellSize: 25 / 480,
  wallHeight: 0.9,
  wallThickness: 0.3,
  archHeight: 2,
  archWidth: 1.5, // 门洞宽度
  archThickness: 0.2, // 拱门厚度（固定）
  offsetX: -12.5,
  offsetZ: -25
};

// 碰撞体数组
let collisionBoxes = [];

// ====================== 迷宫生成函数 ======================
function createLeftMaze(scene) {
  const mazeGroup = new THREE.Group();
  scene.add(mazeGroup);

  const wallMaterial = new THREE.MeshLambertMaterial({ color: 0xff3333 });
  const stripeMaterial = new THREE.MeshLambertMaterial({ color: 0xffff00 });
  const archMaterial = new THREE.MeshLambertMaterial({ color: 0x0066ff, transparent: true, opacity: 0.8 });

  // 清空之前的碰撞体
  collisionBoxes = [];

  createMazeBoundary(mazeGroup, wallMaterial, stripeMaterial);
  createInnerWalls(mazeGroup, wallMaterial, stripeMaterial);
  createArches(mazeGroup, archMaterial);
}

function createMazeBoundary(group, wallMat, stripeMat) {
  const { cellSize, wallHeight, offsetX, offsetZ } = MAZE_CONFIG;

  // 边缘墙壁坐标，使用 { x1, x2, z1, z2 } 格式
  const boundaryWalls = [
    { x1: 0, x2: 420, z1: 80, z2: 100 },           // 上边墙
    { x1: 0, x2: 0, z1: 0, z2: 1110 },         // 左边墙
    { x1: 360, x2: 370, z1: 150, z2: 910 },     // 右边墙
    { x1: 410, x2: 420, z1: 950, z2: 1110 },
    { x1: 0, x2: 420, z1: 1100, z2: 1110 }     // 下边墙
  ];

  boundaryWalls.forEach(wall => {
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

function createInnerWalls(group, wallMat, stripeMat) {
  const { cellSize, wallHeight, wallThickness } = MAZE_CONFIG;
  const walls = [
    { x1: 200, x2: 210, z1: 130, z2: 220 },
    { x1: 120, x2: 130, z1: 170, z2: 210 },
    { x1: 120, x2: 200, z1: 210, z2: 220 },
    { x1: 120, x2: 130, z1: 210, z2: 290 },
    { x1: 120, x2: 280, z1: 290, z2: 300 },
    { x1: 120, x2: 130, z1: 300, z2: 370 },
    { x1: 240, x2: 360, z1: 370, z2: 380 },
    { x1: 50, x2: 130, z1: 370, z2: 380 },
    { x1: 0, x2: 120, z1: 460, z2: 470 },
    { x1: 160, x2: 320, z1: 460, z2: 470 },
    { x1: 80, x2: 360, z1: 550, z2: 560 },
    { x1: 0, x2: 300, z1: 630, z2: 640 },
    { x1: 0, x2: 120, z1: 720, z2: 730 },
    { x1: 160, x2: 360, z1: 720, z2: 730 },
    { x1: 80, x2: 280, z1: 820, z2: 830 },
    { x1: 280, x2: 290, z1: 780, z2: 900 },
    { x1: 180, x2: 190, z1: 780, z2: 900 },
    { x1: 0, x2: 70, z1: 900, z2: 910 },
    { x1: 120, x2: 220, z1: 900, z2: 910 },
    { x1: 280, x2: 360, z1: 900, z2: 910 },
    { x1: 0, x2: 260, z1: 950, z2: 960 },
       { x1: 300, x2: 420, z1: 950, z2: 960 },
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

// ====================== ✅ 最终修复版：横竖拱门（彻底解决山字问题）======================
function createArches(group, archMat) {
  const { cellSize, archHeight, archWidth, archThickness } = MAZE_CONFIG;

  // 🎯 现在定义绝对清晰，再也不会搞反了！
  // dir: 'vertical' = 竖拱门（正常门，柱子前后站，车辆左右开过去）
  // dir: 'horizontal' = 横拱门（侧门，柱子左右站，车辆前后开过去）
  const arches = [
    { x: 360, z: 130, dir: 'vertical' },
    { x: 370, z: 930, dir: 'vertical' },
    { x: 120, z: 980, dir: 'vertical' },
    { x: 280, z: 960, dir: 'horizontal' },
    { x: 20, z: 1020, dir: 'vertical' },
    { x: 200, z: 1020, dir: 'vertical' },
    { x: 380, z: 1050, dir: 'horizontal' },
    { x: 80, z: 1080, dir: 'vertical' },
    { x: 280, z: 1080, dir: 'vertical' },
  ];

  arches.forEach(arch => {
    const realX = (arch.x - 240) * cellSize;
    const realZ = (arch.z - 600) * cellSize;

    if (arch.dir === 'vertical') {
      // --- 竖拱门（正常门，车辆左右走）---
      // 柱子：前后排列
      createArchPillar(group, archMat, realX, realZ - archWidth/2);
      createArchPillar(group, archMat, realX, realZ + archWidth/2);

      // 横梁：水平左右架在柱子上
      const beam = new THREE.Mesh(
        new THREE.BoxGeometry(archThickness, 0.15, archWidth),
        archMat
      );
      beam.position.set(realX, archHeight, realZ);
      beam.castShadow = true;
      group.add(beam);
    } else {
      // --- 横拱门（侧门，车辆前后走）---
      // 柱子：左右排列
      createArchPillar(group, archMat, realX - archWidth/2, realZ);
      createArchPillar(group, archMat, realX + archWidth/2, realZ);

      // 横梁：水平前后架在柱子上
      const beam = new THREE.Mesh(
        new THREE.BoxGeometry(archWidth, 0.15, archThickness),
        archMat
      );
      beam.position.set(realX, archHeight, realZ);
      beam.castShadow = true;
      group.add(beam);
    }
  });
}

function createWall(group, mainMat, stripeMat, x, y, z, width, height, depth) {
  const wall = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), mainMat);
  wall.position.set(x, y, z);
  wall.castShadow = true;
  wall.receiveShadow = true;
  group.add(wall);

  // 添加碰撞体
  collisionBoxes.push({
    minX: x - width/2,
    maxX: x + width/2,
    minY: 0,
    maxY: height,
    minZ: z - depth/2,
    maxZ: z + depth/2
  });

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
  const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.15, MAZE_CONFIG.archHeight, 0.15), mat);
  pillar.position.set(x, MAZE_CONFIG.archHeight/2, z);
  pillar.castShadow = true;
  group.add(pillar);

  // 添加柱子碰撞体
  collisionBoxes.push({
    minX: x - 0.075,
    maxX: x + 0.075,
    minY: 0,
    maxY: MAZE_CONFIG.archHeight,
    minZ: z - 0.075,
    maxZ: z + 0.075
  });
}

// 暴露创建迷宫的函数和碰撞检测
export { createLeftMaze, collisionBoxes };

// 获取碰撞体数量（用于调试）
function getCollisionBoxCount() {
  return collisionBoxes.length;
}

export { getCollisionBoxCount };

// 碰撞检测函数（检测整个边界框）
function checkCollision(x, y, z, radius = 0.2, height = 0.1) {
  for (const box of collisionBoxes) {
    // 检查 X 轴
    if (x + radius > box.minX && x - radius < box.maxX &&
        // 检查 Y 轴（高度范围）
        y + height > box.minY && y < box.maxY &&
        // 检查 Z 轴
        z + radius > box.minZ && z - radius < box.maxZ) {
      return true;
    }
  }
  return false;
}

export { checkCollision };
