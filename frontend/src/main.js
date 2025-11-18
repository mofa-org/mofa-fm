/**
 * MoFA FM 主入口文件
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import api from './api'

// 导入样式
import '@/assets/styles/theme.css'
import '@/assets/styles/main.css'
import '@/assets/styles/animations.css'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局注入 API
app.config.globalProperties.$api = api

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
