import {createRouter, createWebHashHistory} from "vue-router";


const router = createRouter({
        history: createWebHashHistory(import.meta.env.BASE_URL),
        routes: [
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