import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/',
    redirect: '/conversations'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/conversations',
    name: 'conversations',
    component: () => import('@/views/Conversations.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/conversations/:id',
    name: 'conversation-detail',
    component: () => import('@/views/ConversationDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/scripts',
    name: 'scripts',
    component: () => import('@/views/Scripts.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('@/views/Tasks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/credit',
    name: 'credit',
    component: () => import('@/views/Credit.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
