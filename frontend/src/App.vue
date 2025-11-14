<template>
  <el-container class="app-container">
    <el-header v-if="showHeader" class="app-header">
      <div class="header-left">
        <img src="/logo.png" alt="MoFA Voice" class="logo" />
        <span class="app-title">MoFA Voice</span>
      </div>
      <el-menu
        mode="horizontal"
        :default-active="$route.path"
        router
        class="header-menu"
      >
        <el-menu-item index="/conversations">AI 对话</el-menu-item>
        <el-menu-item index="/scripts">我的脚本</el-menu-item>
        <el-menu-item index="/tasks">任务列表</el-menu-item>
      </el-menu>
      <div class="header-right">
        <el-tag type="success">Credit: {{ userStore.creditBalance }}</el-tag>
        <el-dropdown @command="handleUserAction">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            {{ userStore.username }}
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="credit">Credit 管理</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const showHeader = computed(() => {
  return !['login', 'register'].includes(route.name)
})

const handleUserAction = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (command === 'credit') {
    router.push('/credit')
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  height: 40px;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-menu {
  flex: 1;
  border: none;
  margin: 0 40px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #606266;
}

.app-main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
