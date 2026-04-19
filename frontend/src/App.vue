<template>
  <div id="app">
    <!-- 全屏显示主内容 -->
    <RouterView />
  </div>
</template>

<script setup>
// 简化后的App组件
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
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
