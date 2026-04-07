import {createRouter, createWebHashHistory} from "vue-router";
import AuthView from "./views/AuthView.vue";
import MainControl from "./views/MainControl.vue";

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
                path: '/control',
                name: 'MainControl',
                component: MainControl,
                meta: {
                    requiresAuth: true,
                    title: '空地协同控制中心'
                }
            }
        ]

    }
)

// 路由守卫
router.beforeEach((to, from) => {
    const token = localStorage.getItem('official_token');
    if (to.meta.requiresAuth && !token) {
        return '/auth';
    } else {
        return true;
    }
});

export default router;