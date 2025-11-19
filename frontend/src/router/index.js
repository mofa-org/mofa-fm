/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/Register.vue'),
      meta: { guest: true }
    },
    {
      path: '/discover',
      name: 'discover',
      component: () => import('@/views/Discover.vue')
    },
    {
      path: '/shows/:slug',
      name: 'show-detail',
      component: () => import('@/views/ShowDetail.vue')
    },
    {
      path: '/shows/:showSlug/episodes/:episodeSlug',
      name: 'episode-detail',
      component: () => import('@/views/EpisodeDetail.vue')
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/Search.vue')
    },
    {
      path: '/library',
      name: 'library',
      component: () => import('@/views/Library.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/creator',
      name: 'creator-dashboard',
      component: () => import('@/views/creator/Dashboard.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/creator/shows/create',
      name: 'create-show',
      component: () => import('@/views/creator/CreateShow.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/creator/shows/:slug/edit',
      name: 'edit-show',
      component: () => import('@/views/creator/EditShow.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/creator/shows/:id/episodes/create',
      name: 'upload-episode',
      component: () => import('@/views/creator/UploadEpisode.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/creator/shows/:showSlug/episodes/:episodeSlug/edit',
      name: 'edit-episode',
      component: () => import('@/views/creator/EditEpisode.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/become-creator',
      name: 'become-creator',
      component: () => import('@/views/BecomeCreator.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/Profile.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 需要认证的路由
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // 需要创作者权限的路由
  if (to.meta.requiresCreator && !authStore.isCreator) {
    next({ name: 'become-creator' })
    return
  }

  // 访客路由（已登录不能访问）
  if (to.meta.guest && authStore.isAuthenticated) {
    next({ name: 'home' })
    return
  }

  next()
})

export default router
