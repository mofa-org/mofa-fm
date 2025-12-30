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
      path: '/auth/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/auth/ForgotPassword.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/auth/reset-password/:uid/:token',
      name: 'reset-password',
      component: () => import('../views/auth/ResetPassword.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/auth/verify-email/:uid/:token',
      name: 'verify-email',
      component: () => import('../views/auth/VerifyEmail.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/app/login', // Deprecated path redirect
      redirect: '/login'
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
      path: '/creator/shows/:slug',
      name: 'manage-show',
      component: () => import('@/views/creator/ManageShow.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/creator/shows/:slug/edit',
      name: 'edit-show',
      component: () => import('@/views/creator/EditShow.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/creator/shows/:slug/episodes/create',
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
      path: '/creator/ai-studio',
      name: 'ai-studio',
      component: () => import('@/views/creator/AIScriptStudio.vue'),
      meta: { requiresAuth: true, requiresCreator: true }
    },
    {
      path: '/debates',
      name: 'debate-list',
      component: () => import('@/views/DebateList.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/debate/create',
      name: 'create-debate',
      component: () => import('@/views/creator/CreateDebate.vue'),
      meta: { requiresAuth: true }  // 只需登录，不需要creator权限
    },
    {
      path: '/debate/:episodeId',
      name: 'debate-viewer',
      component: () => import('@/views/creator/DebateViewer.vue'),
      meta: { requiresAuth: true }  // 只需登录，不需要creator权限
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
    },
    {
      path: '/status',
      name: 'status',
      component: () => import('@/views/Status.vue')
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
