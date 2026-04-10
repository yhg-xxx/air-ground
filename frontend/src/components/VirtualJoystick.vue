<template>
  <div class="joystick-container">
    <div class="joystick-label" v-if="label">{{ label }}</div>
    <div 
      class="joystick-base" 
      ref="joystickBase"
      :style="{ width: size + 'px', height: size + 'px' }"
      @mousedown="startDrag"
      @touchstart.prevent="startDrag"
    >
      <!-- 方向标签 -->
      <span class="direction-label top">{{ topLabel }}</span>
      <span class="direction-label bottom">{{ bottomLabel }}</span>
      <span class="direction-label left">{{ leftLabel }}</span>
      <span class="direction-label right">{{ rightLabel }}</span>
      
      <!-- 十字参考线 -->
      <div class="crosshair horizontal"></div>
      <div class="crosshair vertical"></div>
      
      <!-- 摇杆柄 -->
      <div 
        class="joystick-handle"
        :style="handleStyle"
      >
        <div class="handle-inner">
          <span class="speed-display">{{ currentValue }}</span>
        </div>
      </div>
    </div>
    
    <!-- 速度限制滑块 -->
    <div class="speed-limit" v-if="showSpeedLimit">
      <span class="limit-label">最大速度: {{ Math.round(1500 + 500 * (maxSpeedPercent / 100)) }}</span>
      <input 
        type="range" 
        v-model="maxSpeedPercent" 
        min="20" 
        max="100" 
        step="10"
        class="speed-slider"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  size: { type: Number, default: 150 },
  label: { type: String, default: '' },
  topLabel: { type: String, default: '前' },
  bottomLabel: { type: String, default: '后' },
  leftLabel: { type: String, default: '左' },
  rightLabel: { type: String, default: '右' },
  // 是否只返回单轴（用于单轴控制如油门）
  singleAxisX: { type: Boolean, default: false },
  singleAxisY: { type: Boolean, default: false },
  // 松手后是否自动归中
  autoCenter: { type: Boolean, default: true },
  // 是否显示速度限制滑块
  showSpeedLimit: { type: Boolean, default: false }
})

const emit = defineEmits(['change', 'start', 'end'])

const joystickBase = ref(null)
const isDragging = ref(false)
const position = ref({ x: 0, y: 0 })
const maxSpeedPercent = ref(100) // 最大速度百分比

// 计算摇杆柄的位置样式
const handleStyle = computed(() => {
  const maxOffset = (props.size - 40) / 2 // 40是摇杆柄的大小
  const x = position.value.x * maxOffset
  const y = position.value.y * maxOffset
  return {
    transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`
  }
})

// 计算速度百分比（距离中心的距离）
const speedPercent = computed(() => {
  const distance = Math.sqrt(position.value.x ** 2 + position.value.y ** 2)
  return Math.round(distance * 100)
})

// 当前控制值显示（显示Y轴值，即主要控制方向）
const currentValue = computed(() => {
  const limitedY = -position.value.y * (maxSpeedPercent.value / 100)
  return Math.round(1500 + limitedY * 500)
})

// 将相对位置(-1到1)转换为控制值(1000到2000)
const toControlValue = (value) => {
  // 应用速度限制
  const limitedValue = value * (maxSpeedPercent.value / 100)
  return Math.round(1500 + limitedValue * 500)
}

// 开始拖拽
const startDrag = (event) => {
  isDragging.value = true
  emit('start')
  updatePosition(event)
  
  // 添加全局事件监听
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', endDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', endDrag)
}

// 拖拽中
const onDrag = (event) => {
  if (!isDragging.value) return
  event.preventDefault()
  updatePosition(event)
}

// 结束拖拽
const endDrag = () => {
  isDragging.value = false
  
  // 移除全局事件监听
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', endDrag)
  
  // 自动归中
  if (props.autoCenter) {
    position.value = { x: 0, y: 0 }
    emitChange()
  }
  
  emit('end')
}

// 更新位置
const updatePosition = (event) => {
  if (!joystickBase.value) return
  
  const rect = joystickBase.value.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  
  // 获取触摸或鼠标位置
  const clientX = event.touches ? event.touches[0].clientX : event.clientX
  const clientY = event.touches ? event.touches[0].clientY : event.clientY
  
  // 计算相对于中心的偏移
  let deltaX = (clientX - centerX) / (rect.width / 2)
  let deltaY = (clientY - centerY) / (rect.height / 2)
  
  // 限制在圆形范围内
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  if (distance > 1) {
    deltaX /= distance
    deltaY /= distance
  }
  
  // 单轴模式
  if (props.singleAxisX) deltaY = 0
  if (props.singleAxisY) deltaX = 0
  
  position.value = { x: deltaX, y: deltaY }
  emitChange()
}

// 发送变化事件
const emitChange = () => {
  emit('change', {
    x: position.value.x,
    y: position.value.y,
    xValue: toControlValue(position.value.x),
    yValue: toControlValue(-position.value.y) // Y轴反转，向上为正
  })
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', endDrag)
})
</script>

<style scoped>
.joystick-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  user-select: none;
}

.joystick-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.joystick-base {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(145deg, #f0f2f5, #e4e7ed);
  box-shadow: 
    inset 2px 2px 5px rgba(0,0,0,0.1),
    inset -2px -2px 5px rgba(255,255,255,0.8),
    0 4px 15px rgba(0,0,0,0.1);
  cursor: pointer;
  touch-action: none;
}

.direction-label {
  position: absolute;
  font-size: 11px;
  color: #909399;
  font-weight: 500;
}

.direction-label.top {
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
}

.direction-label.bottom {
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
}

.direction-label.left {
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
}

.direction-label.right {
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}

.crosshair {
  position: absolute;
  background: rgba(64, 158, 255, 0.2);
}

.crosshair.horizontal {
  width: 60%;
  height: 1px;
  left: 20%;
  top: 50%;
}

.crosshair.vertical {
  width: 1px;
  height: 60%;
  left: 50%;
  top: 20%;
}

.joystick-handle {
  position: absolute;
  width: 50px;
  height: 50px;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: linear-gradient(145deg, #409eff, #337ecc);
  box-shadow: 
    0 4px 12px rgba(64, 158, 255, 0.4),
    inset 1px 1px 2px rgba(255,255,255,0.3);
  transition: transform 0.05s ease-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.handle-inner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.4);
  box-shadow: inset 1px 1px 3px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.speed-display {
  font-size: 9px;
  font-weight: bold;
  color: #337ecc;
  text-shadow: 0 0 2px rgba(255,255,255,0.8);
  white-space: nowrap;
}

.joystick-handle:active {
  box-shadow: 
    0 2px 8px rgba(64, 158, 255, 0.5),
    inset 1px 1px 2px rgba(255,255,255,0.3);
}

/* 速度限制滑块 */
.speed-limit {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.limit-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.speed-slider {
  width: 100%;
  max-width: 150px;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(to right, #67c23a, #e6a23c, #f56c6c);
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.speed-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #409eff;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

.speed-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #409eff;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
</style>
