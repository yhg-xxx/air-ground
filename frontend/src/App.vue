<template>
  <div id="app">
    <el-container v-if="!isAuthPage">
      <!-- 侧边栏 -->
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <h3>空地协同系统</h3>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/control">
            <el-icon><Monitor /></el-icon>
            <span>空地协同控制</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主要内容区 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-left">
            <span>{{ pageTitle }}</span>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                用户
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="auth">重新认证</el-dropdown-item>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 主要内容 -->
        <el-main class="main-content">
          <RouterView />
        </el-main>
      </el-container>
    </el-container>
    
    <!-- 认证页面直接显示 -->
    <RouterView v-else />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { House, User, ArrowDown,Monitor } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 判断是否为认证页面
const isAuthPage = computed(() => route.path === '/auth')

// 页面标题
const pageTitle = computed(() => {
  return route.meta?.title || '空地协同系统'
})

// 处理下拉菜单命令
const handleCommand = (command) => {
  switch (command) {
    case 'auth':
      router.push('/auth')
      break
    case 'logout':
      localStorage.removeItem('official_token')
      ElMessage.success('已退出登录')
      router.push('/auth')
      break
  }
}
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
}

.sidebar {
  background-color: #304156;
  color: #bfcbd9;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #434a50;
}

.logo h3 {
  margin: 0;
  color: #409EFF;
  font-size: 16px;
}

.menu {
  border: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.header-left span {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #606266;
  font-size: 14px;
}

.user-info:hover {
  color: #409EFF;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
</style>
