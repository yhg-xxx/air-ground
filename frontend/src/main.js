import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from "axios"
import router from './router'  // ✅ 添加这行：导入路由配置

// 修复 Edge 浏览器无法最小化问题
(function fixEdgeMinimizeIssue() {
    const isEdge = navigator.userAgent.indexOf('Edg') > -1;
    if (!isEdge) return;

    const originalReplaceState = window.history.replaceState;
    const originalPushState = window.history.pushState;

    window.history.replaceState = function(state, title, url) {
        if (document.visibilityState === 'hidden') {
            return;
        }
        return originalReplaceState.call(this, state, title, url);
    };

    window.history.pushState = function(state, title, url) {
        if (document.visibilityState === 'hidden') {
            return;
        }
        return originalPushState.call(this, state, title, url);
    };
})();

// 全局配置 axios
axios.defaults.withCredentials = true;
axios.defaults.baseURL = 'http://localhost:8000'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

// 挂载插件
app.use(ElementPlus, {
    locale: zhCn
})
app.use(router)  // ✅ 添加这行：挂载路由插件

app.mount('#app')