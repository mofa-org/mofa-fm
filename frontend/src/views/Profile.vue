<template>
  <div class="profile-page">
    <div class="container">
      <h1 class="page-title">个人资料</h1>

      <div class="profile-content mofa-card">
        <!-- 头像部分 -->
        <div class="avatar-section">
          <el-avatar :size="120" :src="previewUrl || form.avatar_url" :icon="UserFilled" />
          <input
            ref="avatarInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleAvatarChange"
          />
          <el-button
            class="mofa-btn mofa-btn-primary"
            style="margin-top: 16px"
            @click="$refs.avatarInput.click()"
          >
            更换头像
          </el-button>
          <div v-if="avatarFile" class="avatar-hint">
            已选择: {{ avatarFile.name }}
          </div>
        </div>

        <!-- 表单部分 -->
        <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" class="profile-form">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" disabled />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" type="email" />
          </el-form-item>

          <el-form-item label="个人简介" prop="bio">
            <el-input
              v-model="form.bio"
              type="textarea"
              :rows="4"
              maxlength="500"
              show-word-limit
              placeholder="介绍一下你自己..."
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              class="mofa-btn mofa-btn-primary"
              :loading="saving"
              @click="handleSave"
            >
              保存更改
            </el-button>
            <el-button class="mofa-btn" @click="handleCancel">
              取消
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 账户信息 -->
        <div class="account-info">
          <h3>账户信息</h3>
          
          <div class="info-item">
            <span class="label">邮箱验证:</span>
            <div class="value-row">
              <el-tag :type="user?.email_verified ? 'success' : 'warning'">
                {{ user?.email_verified ? '已验证' : '未验证' }}
              </el-tag>
              <button 
                v-if="!user?.email_verified" 
                @click="sendVerificationEmail" 
                class="text-btn"
                :disabled="sendingEmail"
              >
                {{ sendingEmail ? '发送中...' : '发送验证邮件' }}
              </button>
            </div>
          </div>

          <div class="info-item">
            <span class="label">创作者状态:</span>
            <el-tag :type="user?.is_creator ? 'success' : 'info'">
              {{ user?.is_creator ? '已认证' : '普通用户' }}
            </el-tag>
          </div>
          <div class="info-item" v-if="user?.is_creator">
            <span class="label">节目数:</span>
            <span>{{ user?.shows_count }}</span>
          </div>
          <div class="info-item" v-if="user?.is_creator">
            <span class="label">总播放量:</span>
            <span>{{ user?.total_plays }}</span>
          </div>
          <div class="info-item">
            <span class="label">注册时间:</span>
            <span>{{ formatDate(user?.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const avatarInput = ref()
const saving = ref(false)
const sendingEmail = ref(false)
const avatarFile = ref(null)
const previewUrl = ref('')

const form = ref({
  username: '',
  email: '',
  bio: '',
  avatar_url: ''
})

const user = computed(() => authStore.user)

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

onMounted(() => {
  if (user.value) {
    form.value = {
      username: user.value.username,
      email: user.value.email,
      bio: user.value.bio || '',
      avatar_url: user.value.avatar_url
    }
  }
})

async function sendVerificationEmail() {
  if (sendingEmail.value) return
  sendingEmail.value = true
  try {
    const res = await api.auth.sendVerificationEmail()
    ElMessage.success(res.message || '验证邮件已发送，请查收')
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.error || '发送失败，请稍后重试')
  } finally {
    sendingEmail.value = false
  }
}

function handleAvatarChange(event) {
  const file = event.target.files[0]
  if (!file) return

  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return
  }

  avatarFile.value = file
  // 创建预览URL
  previewUrl.value = URL.createObjectURL(file)
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const formData = new FormData()
    formData.append('email', form.value.email)
    formData.append('bio', form.value.bio)

    if (avatarFile.value) {
      formData.append('avatar', avatarFile.value)
    }

    const data = await authStore.updateProfile(formData)
    form.value.avatar_url = data.avatar_url
    avatarFile.value = null
    previewUrl.value = ''

    ElMessage.success('资料更新成功')
  } catch (error) {
    // 错误已在拦截器处理
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.back()
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD')
}
</script>

<style scoped>
.profile-page {
  padding: var(--spacing-2xl) 0;
}

.page-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-lg);
}

.profile-content {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-2xl);
}

.avatar-section {
  text-align: center;
  padding-bottom: var(--spacing-2xl);
  border-bottom: 2px solid var(--color-light-gray);
  margin-bottom: var(--spacing-2xl);
}

.avatar-hint {
  margin-top: var(--spacing-xs);
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
}

.profile-form {
  margin-bottom: var(--spacing-2xl);
}

.account-info {
  padding-top: var(--spacing-xl);
  border-top: 2px solid var(--color-light-gray);
}

.account-info h3 {
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-md);
}

.info-item {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-base);
}

.info-item .label {
  color: var(--color-text-secondary);
  font-weight: var(--font-medium);
  min-width: 100px;
}

  min-width: 100px;
}

.value-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.text-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  padding: 0;
  font-size: var(--font-sm);
  text-decoration: underline;
}

.text-btn:disabled {
  color: var(--color-text-tertiary);
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 768px) {
  .profile-page {
    padding: var(--spacing-lg) 0;
  }

  .page-title {
    font-size: var(--font-2xl);
    padding: 0 var(--spacing-md);
  }

  .profile-content {
    padding: var(--spacing-lg);
  }

  .avatar-section {
    padding-bottom: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);
  }

  .profile-form {
    margin-bottom: var(--spacing-lg);
  }

  .profile-form :deep(.el-form-item__label) {
    width: 70px !important;
  }

  .account-info h3 {
    font-size: var(--font-lg);
  }

  .info-item {
    font-size: var(--font-sm);
  }

  .info-item .label {
    min-width: 80px;
  }
}

@media (max-width: 480px) {
  .profile-page {
    padding: var(--spacing-md) 0;
  }

  .page-title {
    font-size: var(--font-xl);
    margin-bottom: var(--spacing-md);
    padding: 0 var(--spacing-sm);
  }

  .profile-content {
    padding: var(--spacing-md);
  }

  .avatar-section {
    padding-bottom: var(--spacing-md);
    margin-bottom: var(--spacing-md);
  }

  .avatar-section :deep(.el-avatar) {
    width: 80px !important;
    height: 80px !important;
  }

  .avatar-hint {
    font-size: var(--font-xs);
    padding: 0 var(--spacing-sm);
  }

  .profile-form {
    margin-bottom: var(--spacing-md);
  }

  .profile-form :deep(.el-form-item) {
    flex-direction: column;
    margin-bottom: var(--spacing-md);
  }

  .profile-form :deep(.el-form-item__label) {
    width: 100% !important;
    text-align: left;
    margin-bottom: var(--spacing-xs);
    padding: 0;
  }

  .profile-form :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }

  .profile-form :deep(.el-button) {
    width: 100%;
    margin: var(--spacing-xs) 0;
  }

  .account-info {
    padding-top: var(--spacing-md);
  }

  .account-info h3 {
    font-size: var(--font-base);
    margin-bottom: var(--spacing-sm);
  }

  .info-item {
    flex-direction: column;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-md);
    font-size: var(--font-sm);
    padding: var(--spacing-sm);
    background: var(--color-bg);
    border-radius: var(--radius-default);
  }

  .info-item .label {
    min-width: auto;
    font-size: var(--font-xs);
    color: var(--color-text-tertiary);
  }
}
</style>
