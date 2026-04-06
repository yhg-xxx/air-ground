import {createRouter, createWebHashHistory} from "vue-router";
import AuthView from "./views/AuthView.vue";
import DashboardView from "./views/DashboardView.vue";
import GimbalView from "./views/GimbalView.vue";
import ControlView from "./views/ControlView.vue";
import OfficialControlView from "./views/OfficialControlView.vue";

const router = createRouter({
        history: createWebHashHistory(import.meta.env.BASE_URL),
        routes: [
            {
                path: '/',
                redirect: '/auth'
            },
            {
                path: '/auth',
                name: 'Auth',
                component: AuthView,
                meta: {
                    title: '用户认证'
                }
            },
            {
                path: '/dashboard',
                name: 'Dashboard',
                component: DashboardView,
                meta: {
                    requiresAuth: true,
                    title: '控制台'
                }
            },
            {
                path: '/gimbal',
                name: 'Gimbal',
                component: GimbalView,
                meta: {
                    requiresAuth: true,
                    title: '云台控制'
                }
            },
            {
                path: '/control',
                name: 'Control',
                component: ControlView,
                meta: {
                    requiresAuth: true,
                    title: '设备控制'
                }
            },
            {
                path: '/official-control',
                name: 'OfficialControl',
                component: OfficialControlView,
                meta: {
                    requiresAuth: true,
                    title: '官方控制'
                }
            }
        ]

    }
)

// 路由守卫
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token');
    if (to.meta.requiresAuth && !token) {
        next('/auth');
    } else {
        next();
    }
});

export default router;