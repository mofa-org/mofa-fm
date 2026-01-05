<template>
  <el-dialog
    v-model="visible"
    title="GitHub FM - 从开源项目生成播客"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="github-fm-dialog">
      <div class="dialog-intro">
        <el-icon :size="20" color="#ff513b"><Link /></el-icon>
        <span>输入GitHub仓库地址，自动读取README作为参考文件</span>
      </div>

      <el-form :model="form" label-width="120px" @submit.prevent="handleSubmit">
        <el-form-item label="GitHub URL" required>
          <el-input
            v-model="form.url"
            placeholder="https://github.com/owner/repo"
            clearable
            :disabled="loading"
            @input="handleUrlInput"
          />
          <div v-if="parsedRepo" class="url-hint">
            <el-icon><Check /></el-icon>
            将导入仓库: {{ parsedRepo }}
          </div>
        </el-form-item>

        <el-form-item label="会话标题">
          <el-input
            v-model="form.session_title"
            placeholder="留空则自动使用仓库名"
            clearable
            :disabled="loading"
          />
        </el-form-item>

        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        />
      </el-form>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose" :disabled="loading">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="loading"
          :disabled="!form.url.trim()"
        >
          <el-icon v-if="!loading"><Promotion /></el-icon>
          {{ loading ? '导入中...' : '开始创作' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Link, Check, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = ref({
  url: '',
  session_title: ''
})

const loading = ref(false)
const error = ref('')
const parsedRepo = ref('')

function handleUrlInput(value) {
  error.value = ''

  // 简单解析显示仓库信息
  if (value && value.includes('github.com')) {
    try {
      const match = value.match(/github\.com\/([^/]+)\/([^/\s?#]+)/)
      if (match) {
        parsedRepo.value = `${match[1]}/${match[2]}`
      } else {
        parsedRepo.value = ''
      }
    } catch (e) {
      parsedRepo.value = ''
    }
  } else {
    parsedRepo.value = ''
  }
}

async function handleSubmit() {
  if (!form.value.url.trim()) {
    error.value = '请输入GitHub仓库地址'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await api.podcasts.importGithubReadme({
      url: form.value.url.trim(),
      session_title: form.value.session_title.trim()
    })

    ElMessage.success({
      message: `成功导入 ${response.github_owner}/${response.github_repo}（${response.readme_size} 字符）`,
      duration: 3000
    })

    // 通知父组件成功
    emit('success', {
      sessionId: response.session_id,
      showId: response.show_id,
      owner: response.github_owner,
      repo: response.github_repo
    })

    // 关闭对话框
    handleClose()

  } catch (err) {
    console.error('导入GitHub README失败:', err)
    error.value = err.response?.data?.error || err.message || '导入失败，请检查URL或稍后重试'
  } finally {
    loading.value = false
  }
}

function handleClose() {
  if (!loading.value) {
    // 重置表单
    form.value = {
      url: '',
      session_title: ''
    }
    error.value = ''
    parsedRepo.value = ''

    visible.value = false
  }
}

// 监听对话框打开
watch(visible, (newVal) => {
  if (!newVal) {
    // 关闭时重置
    form.value = {
      url: '',
      session_title: ''
    }
    error.value = ''
    parsedRepo.value = ''
  }
})
</script>

<style scoped>
.github-fm-dialog {
  padding: 8px 0;
}

.dialog-intro {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, rgba(255, 81, 59, 0.05), rgba(109, 202, 208, 0.05));
  border-left: 3px solid var(--color-primary);
  border-radius: 4px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.url-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-success);
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
