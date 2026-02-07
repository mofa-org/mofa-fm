<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-gradient"></div>
      <div class="container header-content">
        <div class="header-left">
          <!-- 移动端汉堡菜单 -->
          <button class="mobile-menu-btn" @click="showMobileMenu = !showMobileMenu">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width: 24px; height: 24px">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
            </svg>
          </button>

          <router-link to="/" class="logo">
            <img src="/logo.png" alt="MoFA FM" class="logo-image" />
            <h1 class="logo-text">MoFA FM</h1>
          </router-link>

          <nav class="nav-menu">
            <router-link to="/" class="nav-item">首页</router-link>
            <router-link to="/discover" class="nav-item">发现</router-link>
            <router-link v-if="isAuthenticated" to="/library" class="nav-item">我的收听</router-link>
          </nav>
        </div>

        <div class="header-right">
          <!-- 搜索框 -->
          <el-input
            v-model="searchQuery"
            placeholder="搜索音频..."
            :prefix-icon="Search"
            class="search-input"
            @keyup.enter="handleSearch"
          />

          <!-- 用户菜单 -->
          <template v-if="isAuthenticated">
            <router-link to="/creator/ai-studio" class="mofa-btn mofa-btn-primary">
              创作
            </router-link>
            <router-link to="/creator/shows/create" class="mofa-btn">
              新建节目
            </router-link>

            <el-dropdown @command="handleCommand">
              <div class="user-avatar">
                <el-avatar :src="user?.avatar_url" :icon="UserFilled" />
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">{{ user?.username }}</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>

          <template v-else>
            <router-link to="/login" class="mofa-btn">登录</router-link>
            <router-link to="/register" class="mofa-btn mofa-btn-primary">注册</router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 全局播放器 -->
    <GlobalPlayer v-if="currentEpisode" />

    <!-- 移动端菜单 -->
    <div v-if="showMobileMenu" class="mobile-menu-overlay" @click="showMobileMenu = false">
      <div class="mobile-menu" @click.stop>
        <div class="mobile-menu-header">
          <img src="/logo.png" alt="MoFA FM" class="mobile-menu-logo" />
          <h2>MoFA FM</h2>
          <button class="mobile-menu-close" @click="showMobileMenu = false">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width: 24px; height: 24px">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <nav class="mobile-nav">
          <router-link to="/" class="mobile-nav-item" @click="showMobileMenu = false">
            首页
          </router-link>
          <router-link to="/discover" class="mobile-nav-item" @click="showMobileMenu = false">
            发现
          </router-link>
          <router-link v-if="isAuthenticated" to="/library" class="mobile-nav-item" @click="showMobileMenu = false">
            我的收听
          </router-link>
          <template v-if="isAuthenticated">
            <router-link to="/creator/ai-studio" class="mobile-nav-item" @click="showMobileMenu = false">
              创作
            </router-link>
            <router-link to="/creator/shows/create" class="mobile-nav-item" @click="showMobileMenu = false">
              新建节目
            </router-link>
            <router-link to="/profile" class="mobile-nav-item" @click="showMobileMenu = false">
              个人资料
            </router-link>
            <button class="mobile-nav-item mobile-logout" @click="handleLogout">
              退出登录
            </button>
          </template>
          <template v-else>
            <router-link to="/login" class="mobile-nav-item" @click="showMobileMenu = false">
              登录
            </router-link>
            <router-link to="/register" class="mobile-nav-item mobile-nav-item-primary" @click="showMobileMenu = false">
              注册
            </router-link>
          </template>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlayerStore } from '@/stores/player'
import { Search, UserFilled } from '@element-plus/icons-vue'
import GlobalPlayer from '@/components/player/GlobalPlayer.vue'

const router = useRouter()
const authStore = useAuthStore()
const playerStore = usePlayerStore()

const searchQuery = ref('')
const showMobileMenu = ref(false)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const user = computed(() => authStore.user)
const currentEpisode = computed(() => playerStore.currentEpisode)

onMounted(async () => {
  if (isAuthenticated.value) {
    try {
      await authStore.fetchCurrentUser()
    } catch (error) {
      console.error('获取用户信息失败', error)
    }
  }
})

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push({ name: 'search', query: { q: searchQuery.value } })
  }
}

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

function handleLogout() {
  showMobileMenu.value = false
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--color-white);
  border-bottom: var(--border-width) solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.header-gradient {
  height: 4px;
  background: var(--gradient-bar);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  transition: var(--transition);
}

.logo:hover {
  transform: scale(1.05);
}

.logo-image {
  width: 40px;
  height: 40px;
  object-fit: contain;
  transition: var(--transition);
}

.logo:hover .logo-image {
  transform: rotate(-10deg);
}

.logo-text {
  font-size: var(--font-2xl);
  font-weight: var(--font-extrabold);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-menu {
  display: flex;
  gap: var(--spacing-lg);
}

.nav-item {
  font-size: var(--font-base);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  transition: var(--transition);
}

.nav-item:hover {
  color: var(--color-primary);
  transform: translateY(-2px);
}

.nav-item.router-link-active {
  color: var(--color-primary);
  font-weight: var(--font-bold);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.search-input {
  width: 200px;
}

.user-avatar {
  cursor: pointer;
  transition: var(--transition);
}

.user-avatar:hover {
  transform: scale(1.1);
}

.app-main {
  min-height: calc(100vh - var(--header-height));
  padding-bottom: var(--player-height);
}

/* 响应式布局改进 */
@media (max-width: 1024px) {
  .header-content {
    gap: var(--spacing-sm);
  }

  .header-left {
    gap: var(--spacing-md);
  }

  .search-input {
    width: 180px;
  }

  .logo-text {
    font-size: var(--font-xl);
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 var(--spacing-md);
  }

  .nav-menu {
    display: none;
  }

  .search-input {
    width: 120px;
  }

  .logo-text {
    display: none;
  }

  .header-right {
    gap: var(--spacing-xs);
  }

  .mofa-btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-sm);
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 0 var(--spacing-sm);
  }

  .search-input {
    display: none;
  }

  .logo-image {
    width: 32px;
    height: 32px;
  }

  .mofa-btn {
    padding: var(--spacing-xs) var(--spacing-xs);
    font-size: var(--font-xs);
    white-space: nowrap;
  }
}

/* 移动端汉堡菜单按钮 */
.mobile-menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-default);
  background: var(--color-white);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: var(--transition-fast);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.08);
}

.mobile-menu-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.12);
}

.mobile-menu-btn:active {
  transform: translate(0, 0);
  box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.08);
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }
}

/* 移动端菜单遮罩 */
.mobile-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 移动端菜单 */
.mobile-menu {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  max-width: 80vw;
  background: var(--color-white);
  box-shadow: var(--shadow-soft-lg);
  overflow-y: auto;
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(0);
  }
}

.mobile-menu-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-bottom: var(--border-width-thin) solid var(--border-color-light);
  background: var(--gradient-bar);
  color: var(--color-white);
}

.mobile-menu-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.mobile-menu-header h2 {
  flex: 1;
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
  margin: 0;
}

.mobile-menu-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-default);
  color: var(--color-white);
  cursor: pointer;
  transition: var(--transition-fast);
}

.mobile-menu-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-md) 0;
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: var(--font-base);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  text-decoration: none;
  border: none;
  background: none;
  cursor: pointer;
  transition: var(--transition-fast);
  text-align: left;
  width: 100%;
}

.mobile-nav-item:hover {
  background: var(--color-bg);
  color: var(--color-primary);
}

.mobile-nav-item.router-link-active {
  background: var(--color-bg-secondary);
  color: var(--color-primary);
  font-weight: var(--font-bold);
  border-left: 4px solid var(--color-primary);
}

.mobile-nav-item-primary {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

.mobile-logout {
  margin-top: var(--spacing-md);
  border-top: var(--border-width-thin) solid var(--border-color-light);
  padding-top: var(--spacing-lg);
  color: var(--color-primary);
}
</style>
