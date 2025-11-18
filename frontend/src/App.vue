<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-gradient"></div>
      <div class="container header-content">
        <div class="header-left">
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
            placeholder="搜索播客..."
            :prefix-icon="Search"
            class="search-input"
            @keyup.enter="handleSearch"
          />

          <!-- 用户菜单 -->
          <template v-if="isAuthenticated">
            <router-link v-if="isCreator" to="/creator" class="mofa-btn mofa-btn-primary">
              创作中心
            </router-link>
            <router-link v-else to="/become-creator" class="mofa-btn mofa-btn-warning">
              成为创作者
            </router-link>

            <el-dropdown @command="handleCommand">
              <div class="user-avatar">
                <el-avatar v-if="user?.avatar_url" :src="user.avatar_url" />
                <el-avatar v-else :icon="UserFilled" />
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>{{ user?.username }}</el-dropdown-item>
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

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isCreator = computed(() => authStore.isCreator)
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
  }
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

@media (max-width: 768px) {
  .nav-menu {
    display: none;
  }

  .search-input {
    width: 150px;
  }
}
</style>
