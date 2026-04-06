<template>
  <div class="auth-container">
    <el-card class="auth-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>系统认证</span>
        </div>
      </template>
      
      <div class="auth-content">
        <el-form :model="form" label-width="80px">
          <el-form-item label="状态">
            <el-tag :type="hasToken ? 'success' : 'info'">
              {{ hasToken ? '已认证' : '未认证' }}
            </el-tag>
          </el-form-item>
          
          <el-form-item v-if="token" label="Token">
            <el-input 
              v-model="token" 
              type="textarea" 
              :rows="3" 
              readonly 
              placeholder="暂无Token"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="getToken" 
              :loading="loading"
              icon="Key"
            >
              获取Token
            </el-button>
            <el-button 
              v-if="token" 
              type="danger" 
              @click="clearToken"
              icon="Delete"
            >
              清除Token
            </el-button>
          </el-form-item>
        </el-form>
        
        <el-divider />
        
        <div class="system-info">
          <h4>系统信息</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="服务地址">
              http://localhost:8000
            </el-descriptions-item>
            <el-descriptions-item label="系统状态">
              <el-tag :type="systemStatus === 'healthy' ? 'success' : 'danger'">
                {{ systemStatus || '检查中...' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
// 引入路由
import { useRouter } from 'vue-router'
import { authAPI, systemAPI } from '@/services/api'

// 初始化路由
const router = useRouter()

const form = ref({})
const token = ref('')
const loading = ref(false)
const systemStatus = ref('')

const hasToken = computed(() => !!token.value)

// 获取Token
const getToken = async () => {
  loading.value = true
  try {
    const response = await authAPI.getToken()
    if (response.code === '1') {
      token.value = response.data.token
      localStorage.setItem('token', token.value)
      ElMessage.success('Token获取成功，正在跳转...')

      // ====================== 核心：获取成功后跳转 ======================
      setTimeout(() => {
        // 跳转到首页（根据你的路由名称/路径修改）
        router.push({ path: '/dashboard' })
        // 如果是命名路由：router.push({ name: 'Dashboard' })
      }, 800) // 延迟800毫秒跳转，让用户看到提示

    } else {
      ElMessage.error(response.msg || 'Token获取失败')
    }
  } catch (error) {
    console.error('获取Token失败:', error)
    ElMessage.error('获取Token失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

// 清除Token
const clearToken = () => {
  token.value = ''
  localStorage.removeItem('token')
  ElMessage.success('Token已清除')
}

// 检查系统健康状态
const checkSystemHealth = async () => {
  try {
    const response = await systemAPI.healthCheck()
    systemStatus.value = response.status || 'unknown'
  } catch (error) {
    console.error('健康检查失败:', error)
    systemStatus.value = 'unhealthy'
  }
}

// 初始化
onMounted(() => {
  // 如果已经有token，直接跳转到主页，不用停留在登录页
  const savedToken = localStorage.getItem('token')
  if (savedToken) {
    token.value = savedToken
    // 已认证直接跳转
    router.push({ path: '/dashboard' })
  }

  // 检查系统健康状态
  checkSystemHealth()
})
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 500px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
  text-align: center;
}

.auth-content {
  padding: 20px 0;
}

.system-info {
  margin-top: 20px;
}

.system-info h4 {
  margin-bottom: 15px;
  color: #303133;
}
</style>