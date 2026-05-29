import * as THREE from 'three';

const MAZE_CONFIG = {
  gridCols: 480,
  gridRows: 1200,
  realWidth: 25,
  realLength: 50,
  cellSize: 25 / 480,
  wallHeight: 0.9,
  wallThickness: 0.3,
  archHeight: 2,
  archWidth: 1.5,
  archThickness: 0.2,
  offsetX: -12.5,
  offsetZ: -25,
  waterHorseWidth: 0.3,
  waterHorseLength: 1.45
};

let collisionBoxes = [];

function createWaterHorseGeometry() {
  const group = new THREE.Group();
  
  const mainGeo = new THREE.BoxGeometry(MAZE_CONFIG.waterHorseLength, 0.8, MAZE_CONFIG.waterHorseWidth);
  
  const cutGeo1 = new THREE.CylinderGeometry(0.12, 0.12, 0.5, 16, 1, true, 0, Math.PI * 2);
  cutGeo1.rotateZ(Math.PI / 2);
  const cutMesh1 = new THREE.Mesh(cutGeo1);
  cutMesh1.position.set(-0.35, 0.3, 0);
  
  const cutGeo2 = new THREE.CylinderGeometry(0.12, 0.12, 0.5, 16, 1, true, 0, Math.PI * 2);
  cutGeo2.rotateZ(Math.PI / 2);
  const cutMesh2 = new THREE.Mesh(cutGeo2);
  cutMesh2.position.set(0, 0.3, 0);
  
  const cutGeo3 = new THREE.CylinderGeometry(0.12, 0.12, 0.5, 16, 1, true, 0, Math.PI * 2);
  cutGeo3.rotateZ(Math.PI / 2);
  const cutMesh3 = new THREE.Mesh(cutGeo3);
  cutMesh3.position.set(0.35, 0.3, 0);
  
  const topGeo = new THREE.BoxGeometry(MAZE_CONFIG.waterHorseLength + 0.1, 0.08, MAZE_CONFIG.waterHorseWidth + 0.02);
  const topMesh = new THREE.Mesh(topGeo);
  topMesh.position.set(0, 0.44, 0);
  
  const bottomGeo = new THREE.BoxGeometry(MAZE_CONFIG.waterHorseLength + 0.15, 0.1, MAZE_CONFIG.waterHorseWidth + 0.08);
  const bottomMesh = new THREE.Mesh(bottomGeo);
  bottomMesh.position.set(0, -0.4, 0);
  
  return { mainGeo, topGeo, bottomGeo };
}

function createWaterHorse(group, x, y, z, isHorizontal) {
  const waterHorseMaterial = new THREE.MeshStandardMaterial({
    color: 0xcc2222,
    roughness: 0.78,
    metalness: 0.02,
    envMapIntensity: 0.28
  });
  
  const yellowStripeMaterial = new THREE.MeshStandardMaterial({
    color: 0xffdd00,
    roughness: 0.72,
    metalness: 0.02,
    envMapIntensity: 0.25
  });
  
  const whitePanelMaterial = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.68,
    metalness: 0.01,
    envMapIntensity: 0.22
  });

  const waterHorseGroup = new THREE.Group();
  
  const baseGeo = new THREE.BoxGeometry(MAZE_CONFIG.waterHorseLength, 0.8, MAZE_CONFIG.waterHorseWidth);
  const baseMesh = new THREE.Mesh(baseGeo, waterHorseMaterial);
  baseMesh.position.set(0, 0.4, 0);
  baseMesh.castShadow = true;
  baseMesh.receiveShadow = true;
  waterHorseGroup.add(baseMesh);
  
  const topGeo = new THREE.BoxGeometry(MAZE_CONFIG.waterHorseLength + 0.1, 0.08, MAZE_CONFIG.waterHorseWidth + 0.02);
  const topMesh = new THREE.Mesh(topGeo, waterHorseMaterial);
  topMesh.position.set(0, 0.84, 0);
  topMesh.castShadow = true;
  waterHorseGroup.add(topMesh);
  
  const bottomGeo = new THREE.BoxGeometry(MAZE_CONFIG.waterHorseLength + 0.15, 0.12, MAZE_CONFIG.waterHorseWidth + 0.08);
  const bottomMesh = new THREE.Mesh(bottomGeo, waterHorseMaterial);
  bottomMesh.position.set(0, 0.06, 0);
  bottomMesh.castShadow = true;
  bottomMesh.receiveShadow = true;
  waterHorseGroup.add(bottomMesh);
  
  const holeGeo1 = new THREE.CylinderGeometry(0.12, 0.12, MAZE_CONFIG.waterHorseWidth + 0.1, 24);
  holeGeo1.rotateZ(Math.PI / 2);
  const holeMesh1 = new THREE.Mesh(holeGeo1, new THREE.MeshStandardMaterial({ 
    color: 0x333333, 
    roughness: 0.85,
    metalness: 0.01,
    side: THREE.DoubleSide
  }));
  holeMesh1.position.set(-0.35, 0.45, 0);
  waterHorseGroup.add(holeMesh1);
  
  const holeGeo2 = new THREE.CylinderGeometry(0.12, 0.12, MAZE_CONFIG.waterHorseWidth + 0.1, 24);
  holeGeo2.rotateZ(Math.PI / 2);
  const holeMesh2 = new THREE.Mesh(holeGeo2, new THREE.MeshStandardMaterial({ 
    color: 0x333333, 
    roughness: 0.85,
    metalness: 0.01,
    side: THREE.DoubleSide
  }));
  holeMesh2.position.set(0, 0.45, 0);
  waterHorseGroup.add(holeMesh2);
  
  const holeGeo3 = new THREE.CylinderGeometry(0.12, 0.12, MAZE_CONFIG.waterHorseWidth + 0.1, 24);
  holeGeo3.rotateZ(Math.PI / 2);
  const holeMesh3 = new THREE.Mesh(holeGeo3, new THREE.MeshStandardMaterial({ 
    color: 0x333333, 
    roughness: 0.85,
    metalness: 0.01,
    side: THREE.DoubleSide
  }));
  holeMesh3.position.set(0.35, 0.45, 0);
  waterHorseGroup.add(holeMesh3);
  
  for (let i = -2; i <= 2; i++) {
    const arrowGeo = new THREE.BoxGeometry(0.12, 0.03, 0.02);
    const arrowMesh = new THREE.Mesh(arrowGeo, yellowStripeMaterial);
    arrowMesh.position.set(i * 0.22, 0.2, MAZE_CONFIG.waterHorseWidth/2 + 0.015);
    arrowMesh.castShadow = true;
    waterHorseGroup.add(arrowMesh);
    
    const arrowMesh2 = new THREE.Mesh(arrowGeo, yellowStripeMaterial);
    arrowMesh2.position.set(i * 0.22, 0.2, -MAZE_CONFIG.waterHorseWidth/2 - 0.015);
    arrowMesh2.castShadow = true;
    waterHorseGroup.add(arrowMesh2);
  }
  
  const panelGeo = new THREE.BoxGeometry(0.6, 0.22, 0.02);
  const panelMesh = new THREE.Mesh(panelGeo, whitePanelMaterial);
  panelMesh.position.set(0, 0.6, MAZE_CONFIG.waterHorseWidth/2 + 0.012);
  panelMesh.castShadow = true;
  waterHorseGroup.add(panelMesh);
  
  const panelMesh2 = new THREE.Mesh(panelGeo, whitePanelMaterial);
  panelMesh2.position.set(0, 0.6, -MAZE_CONFIG.waterHorseWidth/2 - 0.012);
  panelMesh2.castShadow = true;
  waterHorseGroup.add(panelMesh2);
  
  if (isHorizontal) {
    waterHorseGroup.position.set(x, y, z);
  } else {
    waterHorseGroup.rotation.y = Math.PI / 2;
    waterHorseGroup.position.set(x, y, z);
  }
  
  group.add(waterHorseGroup);
  
  const width = isHorizontal ? MAZE_CONFIG.waterHorseLength : MAZE_CONFIG.waterHorseWidth;
  const depth = isHorizontal ? MAZE_CONFIG.waterHorseWidth : MAZE_CONFIG.waterHorseLength;
  collisionBoxes.push({
    minX: x - width/2,
    maxX: x + width/2,
    minY: 0,
    maxY: MAZE_CONFIG.wallHeight,
    minZ: z - depth/2,
    maxZ: z + depth/2
  });
}

function createLeftMaze(scene) {
  const mazeGroup = new THREE.Group();
  scene.add(mazeGroup);

  const archMaterial = new THREE.MeshStandardMaterial({ 
    color: 0x33aaff, 
    roughness: 0.4, 
    metalness: 0.12 
  });

  collisionBoxes = [];

  createMazeBoundary(mazeGroup);
  createInnerWalls(mazeGroup);
  createArches(mazeGroup, archMaterial);
}

function createMazeBoundary(group) {
  const { cellSize, wallHeight, offsetX, offsetZ } = MAZE_CONFIG;

  const boundaryWalls = [
    { x1: 0, x2: 420, z1: 80, z2: 100 },
    { x1: 0, x2: 0, z1: 0, z2: 1110 },
    { x1: 360, x2: 370, z1: 150, z2: 910 },
    { x1: 410, x2: 420, z1: 950, z2: 1110 },
    { x1: 0, x2: 420, z1: 1100, z2: 1110 }
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
    
    const isHorizontal = width > depth;
    const length = isHorizontal ? width : depth;
    const numWaterHorses = Math.floor(length / MAZE_CONFIG.waterHorseLength);
    const spacing = MAZE_CONFIG.waterHorseLength;
    
    for (let i = 0; i < numWaterHorses; i++) {
      const pos = -length/2 + spacing/2 + i * spacing;
      if (isHorizontal) {
        createWaterHorse(group, centerX - width/2 + spacing/2 + i * spacing, 0, centerZ, true);
      } else {
        createWaterHorse(group, centerX, 0, centerZ - depth/2 + spacing/2 + i * spacing, false);
      }
    }
  });
}

function createInnerWalls(group) {
  const { cellSize, wallHeight, wallThickness } = MAZE_CONFIG;
  const walls = [

      //x为左右长，z为上下长

    { x1: 200, x2: 210, z1: 130, z2: 220 },
    { x1: 120, x2: 130, z1: 150, z2: 210 },
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
    
    const isHorizontal = width > depth;
    const length = isHorizontal ? width : depth;
    const numWaterHorses = Math.floor(length / MAZE_CONFIG.waterHorseLength);
    
    for (let i = 0; i < numWaterHorses; i++) {
      const pos = -length/2 + MAZE_CONFIG.waterHorseLength/2 + i * MAZE_CONFIG.waterHorseLength;
      if (isHorizontal) {
        createWaterHorse(group, centerX - width/2 + MAZE_CONFIG.waterHorseLength/2 + i * MAZE_CONFIG.waterHorseLength, 0, centerZ, true);
      } else {
        createWaterHorse(group, centerX, 0, centerZ - depth/2 + MAZE_CONFIG.waterHorseLength/2 + i * MAZE_CONFIG.waterHorseLength, false);
      }
    }
  });
}

function createArches(group, archMat) {
  const { cellSize, archHeight, archWidth, archThickness } = MAZE_CONFIG;

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
      createArchPillar(group, archMat, realX, realZ - archWidth/2);
      createArchPillar(group, archMat, realX, realZ + archWidth/2);

      const beam = new THREE.Mesh(
        new THREE.BoxGeometry(archThickness, 0.15, archWidth),
        archMat
      );
      beam.position.set(realX, archHeight, realZ);
      beam.castShadow = true;
      group.add(beam);
    } else {
      createArchPillar(group, archMat, realX - archWidth/2, realZ);
      createArchPillar(group, archMat, realX + archWidth/2, realZ);

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

function createArchPillar(group, mat, x, z) {
  const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.15, MAZE_CONFIG.archHeight, 0.15), mat);
  pillar.position.set(x, MAZE_CONFIG.archHeight/2, z);
  pillar.castShadow = true;
  group.add(pillar);

  collisionBoxes.push({
    minX: x - 0.075,
    maxX: x + 0.075,
    minY: 0,
    maxY: MAZE_CONFIG.archHeight,
    minZ: z - 0.075,
    maxZ: z + 0.075
  });
}

export { createLeftMaze, collisionBoxes };

function getCollisionBoxCount() {
  return collisionBoxes.length;
}

export { getCollisionBoxCount };

function checkCollision(x, y, z, radius = 0.2, height = 0.1) {
  for (const box of collisionBoxes) {
    if (x + radius > box.minX && x - radius < box.maxX &&
        y + height > box.minY && y < box.maxY &&
        z + radius > box.minZ && z - radius < box.maxZ) {
      return true;
    }
  }
  return false;
}

export { checkCollision };
