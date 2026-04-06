<template>
  <div class="dashboard">
    <!-- 欢迎信息 -->
    <el-card class="welcome-card" shadow="hover">
      <div class="welcome-content">
        <h2>欢迎使用空地协同系统</h2>
        <p>这是一个集成了云台控制和图像抓拍功能的综合性系统</p>
      </div>
    </el-card>
    
    <!-- 系统状态卡片 -->
    <el-row :gutter="20" class="status-row">
      <el-col :span="6">
        <el-card class="status-card" shadow="hover">
          <div class="status-item">
            <div class="status-icon system">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="status-info">
              <h4>系统状态</h4>
              <el-tag :type="systemStatus === 'healthy' ? 'success' : 'danger'">
                {{ systemStatus === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="status-card" shadow="hover">
          <div class="status-item">
            <div class="status-icon auth">
              <el-icon><Key /></el-icon>
            </div>
            <div class="status-info">
              <h4>认证状态</h4>
              <el-tag :type="hasToken ? 'success' : 'warning'">
                {{ hasToken ? '已认证' : '未认证' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="status-card" shadow="hover">
          <div class="status-item">
            <div class="status-icon capture">
              <el-icon><Camera /></el-icon>
            </div>
            <div class="status-info">
              <h4>抓拍次数</h4>
              <span class="status-number">{{ totalCaptures }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="status-card" shadow="hover">
          <div class="status-item">
            <div class="status-icon success">
              <el-icon><Check /></el-icon>
            </div>
            <div class="status-info">
              <h4>成功率</h4>
              <span class="status-number">{{ successRate }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 功能模块 -->
    <el-row :gutter="20" class="feature-row">
      <el-col :span="12">
        <el-card class="feature-card" shadow="hover">
          <template #header>
            <div class="feature-header">
              <span>快速操作</span>
            </div>
          </template>
          
          <div class="feature-content">
            <el-button 
              type="primary" 
              size="large" 
              @click="goToAuth"
              icon="Key"
              class="feature-btn"
            >
              获取Token
            </el-button>
            
            <el-button 
              type="success" 
              size="large" 
              @click="goToGimbal"
              icon="Camera"
              class="feature-btn"
            >
              云台控制
            </el-button>
            
            <el-button 
              type="info" 
              size="large" 
              @click="checkHealth"
              icon="Refresh"
              class="feature-btn"
              :loading="checking"
            >
              健康检查
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="feature-card" shadow="hover">
          <template #header>
            <div class="feature-header">
              <span>系统信息</span>
            </div>
          </template>
          
          <div class="system-info">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="后端地址">
                http://localhost:8000
              </el-descriptions-item>
              <el-descriptions-item label="API版本">
                v1.0.0
              </el-descriptions-item>
              <el-descriptions-item label="最后检查">
                {{ lastCheckTime || '从未检查' }}
              </el-descriptions-item>
              <el-descriptions-item label="Token状态">
                <el-tag :type="hasToken ? 'success' : 'danger'" size="small">
                  {{ hasToken ? '有效' : '无效' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近活动 -->
    <el-card class="activity-card" shadow="hover">
      <template #header>
        <div class="activity-header">
          <span>最近活动</span>
          <el-button type="text" @click="clearActivity">清除</el-button>
        </div>
      </template>
      
      <div class="activity-content">
        <el-timeline>
          <el-timeline-item
            v-for="(activity, index) in recentActivities"
            :key="index"
            :timestamp="activity.time"
            :type="activity.type"
            :icon="activity.icon"
          >
            {{ activity.message }}
          </el-timeline-item>
          
          <el-timeline-item v-if="recentActivities.length === 0" type="info">
            暂无活动记录
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Monitor, Key, Camera, Check, Refresh } from '@element-plus/icons-vue'
import { systemAPI } from '@/services/api'

const router = useRouter()

// 响应式数据
const systemStatus = ref('unknown')
const checking = ref(false)
const lastCheckTime = ref('')
const totalCaptures = ref(0)
const successCaptures = ref(0)
const recentActivities = ref([])

// 计算属性
const hasToken = computed(() => !!localStorage.getItem('token'))
const successRate = computed(() => {
  if (totalCaptures.value === 0) return 0
  return Math.round((successCaptures.value / totalCaptures.value) * 100)
})

// 方法
const goToAuth = () => {
  router.push('/auth')
}

const goToGimbal = () => {
  if (!hasToken.value) {
    ElMessage.warning('请先获取Token')
    router.push('/auth')
    return
  }
  router.push('/gimbal')
}

const checkHealth = async () => {
  checking.value = true
  try {
    const response = await systemAPI.healthCheck()
    systemStatus.value = response.status || 'unknown'
    lastCheckTime.value = new Date().toLocaleString()
    
    addActivity('系统健康检查完成', 'success', 'Check')
    ElMessage.success('健康检查完成')
  } catch (error) {
    systemStatus.value = 'unhealthy'
    addActivity('健康检查失败: ' + error.message, 'danger', 'Close')
    ElMessage.error('健康检查失败')
  } finally {
    checking.value = false
  }
}

const addActivity = (message, type, icon) => {
  recentActivities.value.unshift({
    time: new Date().toLocaleString(),
    message,
    type,
    icon
  })
  
  // 限制活动记录数量
  if (recentActivities.value.length > 10) {
    recentActivities.value = recentActivities.value.slice(0, 10)
  }
}

const clearActivity = () => {
  recentActivities.value = []
  ElMessage.success('活动记录已清除')
}

// 初始化统计数据
const initStats = () => {
  // 从localStorage读取统计数据
  const stats = localStorage.getItem('captureStats')
  if (stats) {
    const data = JSON.parse(stats)
    totalCaptures.value = data.total || 0
    successCaptures.value = data.success || 0
  }
}

// 保存统计数据
const saveStats = () => {
  localStorage.setItem('captureStats', JSON.stringify({
    total: totalCaptures.value,
    success: successCaptures.value
  }))
}

// 监听统计数据变化
watch([totalCaptures, successCaptures], saveStats)

// 组件挂载时初始化
onMounted(() => {
  initStats()
  checkHealth()
  addActivity('用户访问控制台', 'primary', 'House')
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-content {
  text-align: center;
  padding: 20px 0;
}

.welcome-content h2 {
  color: #409EFF;
  margin-bottom: 10px;
}

.welcome-content p {
  color: #606266;
  font-size: 14px;
}

.status-row {
  margin-bottom: 20px;
}

.status-card {
  height: 120px;
}

.status-item {
  display: flex;
  align-items: center;
  height: 100%;
}

.status-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.status-icon.system {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.status-icon.auth {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.status-icon.capture {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.status-icon.success {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.status-info h4 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 14px;
}

.status-number {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.feature-row {
  margin-bottom: 20px;
}

.feature-card {
  height: 200px;
}

.feature-header {
  font-weight: bold;
  color: #303133;
}

.feature-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 10px 0;
}

.feature-btn {
  width: 100%;
  height: 50px;
}

.system-info {
  padding: 10px 0;
}

.activity-card {
  margin-bottom: 20px;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #303133;
}

.activity-content {
  max-height: 300px;
  overflow-y: auto;
}
</style>
