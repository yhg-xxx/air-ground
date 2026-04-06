import {createRouter, createWebHashHistory} from "vue-router";
import AuthView from "./views/AuthView.vue";
import DashboardView from "./views/DashboardView.vue";
import ControlCenter from "./views/ControlCenter.vue";

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
                path: '/control-center',
                name: 'ControlCenter',
                component: ControlCenter,
                meta: {
                    requiresAuth: true,
                    title: '控制中心'
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