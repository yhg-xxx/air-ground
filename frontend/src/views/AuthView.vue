<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <template #header>
        <div class="card-header">
          <el-icon><Key /></el-icon>
          <span>用户认证</span>
        </div>
      </template>
      
      <div class="auth-form">
        <div class="auth-info">
          <p>系统将使用预设的认证信息获取Token</p>
          <p class="text-secondary">用户名: fcs002</p>
          <p class="text-secondary">密码: wa729461</p>
        </div>
        <el-button type="primary" @click="handleLogin" :loading="isLoading" style="width: 100%">
          {{ isLoading ? '认证中...' : '获取Token' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { officialServerAPI } from '../services/officialAPI'
import { authAPI } from '../services/api'
import {Key} from "@element-plus/icons-vue";

const router = useRouter()

// 加载状态
const isLoading = ref(false)

// 处理登录
const handleLogin = async () => {
  try {
    isLoading.value = true
    
    // 调用官方API获取token
    const token = await officialServerAPI.getToken()
    
    // 保存token到localStorage
    localStorage.setItem('official_token', token)
    
    // 将token传递给后端
    await authAPI.setFrontendToken(token)
    
    ElMessage.success('认证成功')
    await router.push('/control')
  } catch (error) {
    ElMessage.error('认证失败：' + error.message)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
}

.auth-card {
  width: 400px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.auth-form {
  padding: 20px 0;
}

.auth-info {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.auth-info p {
  margin: 5px 0;
  text-align: center;
}

.text-secondary {
  color: #909399;
  font-size: 14px;
}
</style>