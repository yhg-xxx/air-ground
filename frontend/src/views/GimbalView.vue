<template>
  <div class="gimbal-container">
    <el-row :gutter="20">
      <!-- 控制面板 -->
      <el-col :span="8">
        <el-card class="control-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>云台控制</span>
            </div>
          </template>
          
          <div class="control-content">
            <!-- 抓拍控制 -->
            <el-form :model="form" label-width="80px">
              <el-form-item label="操作">
                <el-button 
                  type="primary" 
                  @click="captureImage" 
                  :loading="capturing"
                  icon="Camera"
                  size="large"
                >
                  抓拍图像
                </el-button>
              </el-form-item>
              
              <el-form-item label="自动抓拍">
                <el-switch 
                  v-model="autoCapture" 
                  active-text="开启" 
                  inactive-text="关闭"
                  @change="toggleAutoCapture"
                />
              </el-form-item>
              
              <el-form-item v-if="autoCapture" label="抓拍间隔">
                <el-input-number 
                  v-model="captureInterval" 
                  :min="1" 
                  :max="60" 
                  :step="1"
                  @change="updateAutoCapture"
                />
                <span style="margin-left: 10px;">秒</span>
              </el-form-item>
            </el-form>
            
            <el-divider />
            
            <!-- 统计信息 -->
            <div class="statistics">
              <h4>统计信息</h4>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="总抓拍次数">
                  {{ totalCaptures }}
                </el-descriptions-item>
                <el-descriptions-item label="成功次数">
                  <el-tag type="success">{{ successCaptures }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="失败次数">
                  <el-tag type="danger">{{ failedCaptures }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="最后抓拍">
                  {{ lastCaptureTime || '从未抓拍' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <el-divider />
            
            <!-- 操作历史 -->
            <div class="history">
              <h4>操作历史</h4>
              <el-timeline>
                <el-timeline-item
                  v-for="(item, index) in history"
                  :key="index"
                  :timestamp="item.time"
                  :type="item.success ? 'success' : 'danger'"
                  :icon="item.success ? 'Check' : 'Close'"
                >
                  {{ item.message }}
                </el-timeline-item>
              </el-timeline>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 图像显示区域 -->
      <el-col :span="16">
        <el-card class="image-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>图像预览</span>
              <div class="header-actions">
                <el-button 
                  v-if="currentImage" 
                  type="success" 
                  size="small"
                  @click="downloadImage"
                  icon="Download"
                >
                  下载图像
                </el-button>
                <el-button 
                  v-if="currentImage" 
                  type="warning" 
                  size="small"
                  @click="clearImage"
                  icon="Delete"
                >
                  清除图像
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="image-content">
            <div v-if="currentImage" class="image-wrapper">
              <img 
                :src="currentImage" 
                alt="抓拍图像" 
                class="captured-image"
                @load="onImageLoad"
                @error="onImageError"
              />
              <div class="image-info">
                <p><strong>抓拍时间:</strong> {{ lastCaptureTime }}</p>
                <p><strong>图像大小:</strong> {{ imageSize }}</p>
              </div>
            </div>
            <div v-else class="no-image">
              <el-empty 
                description="暂无图像" 
                :image-size="200"
              >
                <el-button 
                  type="primary" 
                  @click="captureImage"
                  :loading="capturing"
                >
                  开始抓拍
                </el-button>
              </el-empty>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { gimbalAPI } from '@/services/api'

const form = ref({})
const capturing = ref(false)
const currentImage = ref('')
const autoCapture = ref(false)
const captureInterval = ref(5)
const autoCaptureTimer = ref(null)

// 统计信息
const totalCaptures = ref(0)
const successCaptures = ref(0)
const failedCaptures = ref(0)
const lastCaptureTime = ref('')
const imageSize = ref('')

// 操作历史
const history = ref([])

// 抓拍图像
const captureImage = async () => {
  capturing.value = true
  totalCaptures.value++
  
  try {
    const response = await gimbalAPI.captureImage()
    
    // 创建blob URL
    const blob = new Blob([response], { type: 'image/jpeg' })
    const imageUrl = URL.createObjectURL(blob)
    currentImage.value = imageUrl
    
    // 更新图像信息
    lastCaptureTime.value = new Date().toLocaleString()
    imageSize.value = `${(blob.size / 1024).toFixed(2)} KB`
    
    successCaptures.value++
    
    // 添加到历史记录
    addToHistory('图像抓拍成功', true)
    
    ElMessage.success('图像抓拍成功')
  } catch (error) {
    console.error('抓拍失败:', error)
    failedCaptures.value++
    addToHistory('抓拍失败: ' + (error.message || '网络错误'), false)
    ElMessage.error('抓拍失败: ' + (error.message || '网络错误'))
  } finally {
    capturing.value = false
  }
}

// 切换自动抓拍
const toggleAutoCapture = (enabled) => {
  if (enabled) {
    startAutoCapture()
  } else {
    stopAutoCapture()
  }
}

// 开始自动抓拍
const startAutoCapture = () => {
  if (autoCaptureTimer.value) {
    clearInterval(autoCaptureTimer.value)
  }
  
  autoCaptureTimer.value = setInterval(() => {
    if (!capturing.value) {
      captureImage()
    }
  }, captureInterval.value * 1000)
  
  addToHistory(`开始自动抓拍，间隔 ${captureInterval.value} 秒`, true)
}

// 停止自动抓拍
const stopAutoCapture = () => {
  if (autoCaptureTimer.value) {
    clearInterval(autoCaptureTimer.value)
    autoCaptureTimer.value = null
  }
  
  addToHistory('停止自动抓拍', true)
}

// 更新自动抓拍间隔
const updateAutoCapture = () => {
  if (autoCapture.value) {
    stopAutoCapture()
    startAutoCapture()
  }
}

// 下载图像
const downloadImage = () => {
  if (!currentImage.value) return
  
  const link = document.createElement('a')
  link.href = currentImage.value
  link.download = `capture_${Date.now()}.jpg`
  link.click()
  
  ElMessage.success('图像下载已开始')
}

// 清除图像
const clearImage = () => {
  if (currentImage.value) {
    URL.revokeObjectURL(currentImage.value)
    currentImage.value = ''
    imageSize.value = ''
    ElMessage.success('图像已清除')
  }
}

// 添加到历史记录
const addToHistory = (message, success) => {
  history.value.unshift({
    time: new Date().toLocaleString(),
    message,
    success
  })
  
  // 限制历史记录数量
  if (history.value.length > 20) {
    history.value = history.value.slice(0, 20)
  }
}

// 图像加载完成
const onImageLoad = () => {
  // 可以在这里添加图像加载完成后的处理
}

// 图像加载错误
const onImageError = () => {
  ElMessage.error('图像加载失败')
  currentImage.value = ''
}

// 组件卸载时清理
onUnmounted(() => {
  stopAutoCapture()
  clearImage()
})

// 组件挂载时检查Token
onMounted(() => {
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.warning('请先获取Token')
  }
})
</script>

<style scoped>
.gimbal-container {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.control-panel, .image-panel {
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}

.control-content {
  padding: 10px 0;
}

.statistics, .history {
  margin-top: 20px;
}

.statistics h4, .history h4 {
  margin-bottom: 15px;
  color: #303133;
}

.image-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-wrapper {
  text-align: center;
  width: 100%;
}

.captured-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.image-info {
  margin-top: 15px;
  text-align: left;
  background-color: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
}

.image-info p {
  margin: 5px 0;
  font-size: 14px;
}

.no-image {
  width: 100%;
  text-align: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}
</style>
