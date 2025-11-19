<template>
  <div class="upload-episode-page">
    <div class="container">
      <h1 class="page-title">创建播客单集</h1>

      <div class="form-card mofa-card">
        <!-- 模式切换 -->
        <div class="mode-selector">
          <el-radio-group v-model="mode" size="large">
            <el-radio-button value="upload">
              <el-icon><Upload /></el-icon>
              上传音频文件
            </el-radio-button>
            <el-radio-button value="generate">
              <el-icon><MagicStick /></el-icon>
              AI 生成播客
            </el-radio-button>
          </el-radio-group>
        </div>

        <!-- 上传模式 -->
        <el-form v-if="mode === 'upload'" :model="form" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
          <el-form-item label="单集标题" prop="title">
            <el-input v-model="form.title" placeholder="输入单集标题" />
          </el-form-item>

          <el-form-item label="单集描述" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="5"
              placeholder="介绍一下这一集的内容..."
            />
          </el-form-item>

          <el-form-item label="音频文件" prop="audio_file">
            <el-upload
              class="audio-uploader"
              :on-change="handleAudioChange"
              :auto-upload="false"
              accept="audio/*"
              :show-file-list="false"
            >
              <el-button v-if="!audioFile" type="primary">
                <el-icon><Upload /></el-icon>
                选择音频文件
              </el-button>
              <div v-else class="audio-info">
                <el-icon class="audio-icon"><Headset /></el-icon>
                <span>{{ audioFile.name }}</span>
                <el-button type="danger" text @click.stop="removeAudio">
                  删除
                </el-button>
              </div>
            </el-upload>
            <p class="form-hint">支持 MP3、WAV、M4A 等格式，最大 500MB</p>
          </el-form-item>

          <!-- 播客专用字段 -->
          <template v-if="showContentType === 'podcast'">
            <el-form-item label="季数">
              <el-input-number v-model="form.season_number" :min="1" />
            </el-form-item>

            <el-form-item label="集数">
              <el-input-number v-model="form.episode_number" :min="1" />
            </el-form-item>
          </template>

          <!-- 音乐专用字段 -->
          <template v-if="showContentType === 'music'">
            <el-form-item label="艺术家" prop="artist">
              <el-input v-model="form.artist" placeholder="输入艺术家名称" />
            </el-form-item>

            <el-form-item label="流派">
              <el-input v-model="form.genre" placeholder="如：流行、摇滚、古典等" />
            </el-form-item>

            <el-form-item label="专辑名">
              <el-input v-model="form.album_name" placeholder="输入专辑名称（可选）" />
            </el-form-item>

            <el-form-item label="发行日期">
              <el-date-picker
                v-model="form.release_date"
                type="date"
                placeholder="选择发行日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </template>

          <el-form-item>
            <el-button
              type="primary"
              @click="handleUploadSubmit"
              :loading="uploading"
              :disabled="uploadProgress > 0 && uploadProgress < 100"
            >
              {{ uploading ? `上传中 ${uploadProgress}%` : '上传单集' }}
            </el-button>
            <el-button @click="$router.back()">取消</el-button>
          </el-form-item>

          <el-progress v-if="uploadProgress > 0" :percentage="uploadProgress" />
        </el-form>

        <!-- AI 生成模式 -->
        <el-form v-if="mode === 'generate'" :model="generateForm" :rules="generateRules" ref="generateFormRef" label-width="100px">
          <el-form-item label="单集标题" prop="title">
            <el-input v-model="generateForm.title" placeholder="输入单集标题" />
          </el-form-item>

          <el-form-item label="对话脚本" prop="script">
            <div class="script-helper">
              <p><strong>支持格式：</strong></p>
              <code>【大牛】你好，我是大牛。</code>
              <code>【一帆】你好，我是一帆。</code>
            </div>
            <el-input
              v-model="generateForm.script"
              type="textarea"
              :rows="15"
              placeholder="请输入对话脚本..."
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              @click="handleGenerateSubmit"
              :loading="generating"
            >
              {{ generating ? '生成中...' : '开始生成' }}
            </el-button>
            <el-button @click="$router.back()">取消</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Upload, Headset, MagicStick } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 节目信息
const showContentType = ref('podcast')

// 模式切换
const mode = ref('upload')

// 上传模式
const uploadFormRef = ref()
const uploading = ref(false)
const uploadProgress = ref(0)
const audioFile = ref(null)

const form = ref({
  show_id: null,
  title: '',
  description: '',
  audio_file: null,
  season_number: 1,
  episode_number: 1,
  // 音乐字段
  artist: '',
  genre: '',
  album_name: '',
  release_date: null
})

const uploadRules = {
  title: [{ required: true, message: '请输入单集标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入单集描述', trigger: 'blur' }],
  audio_file: [{ required: true, message: '请上传音频文件', trigger: 'change' }]
}

// AI 生成模式
const generateFormRef = ref()
const generating = ref(false)

const generateForm = ref({
  show_id: null,
  title: '',
  script: `【大牛】大家好，欢迎来到今天的节目。
【一帆】大家好，我是你们的老朋友一帆。
【大牛】今天我们要聊什么话题呢？
【一帆】不如聊聊最近很火的 AI 播客生成吧。`
})

const generateRules = {
  title: [{ required: true, message: '请输入单集标题', trigger: 'blur' }],
  script: [{ required: true, message: '请输入脚本内容', trigger: 'blur' }]
}

onMounted(async () => {
  const showId = parseInt(route.params.id)
  form.value.show_id = showId
  generateForm.value.show_id = showId

  // 获取节目信息以确定内容类型
  try {
    const response = await api.get(`/shows/${showId}/`)
    showContentType.value = response.data.content_type || 'podcast'
  } catch (error) {
    console.error('Failed to fetch show info:', error)
  }
})

function handleAudioChange(file) {
  audioFile.value = file
  form.value.audio_file = file.raw
}

function removeAudio() {
  audioFile.value = null
  form.value.audio_file = null
}

async function handleUploadSubmit() {
  const valid = await uploadFormRef.value.validate().catch(() => false)
  if (!valid) return

  uploading.value = true
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    formData.append('show_id', form.value.show_id)
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    formData.append('audio_file', form.value.audio_file)

    // 播客字段
    if (showContentType.value === 'podcast') {
      formData.append('season_number', form.value.season_number)
      formData.append('episode_number', form.value.episode_number)
    }

    // 音乐字段
    if (showContentType.value === 'music') {
      if (form.value.artist) formData.append('artist', form.value.artist)
      if (form.value.genre) formData.append('genre', form.value.genre)
      if (form.value.album_name) formData.append('album_name', form.value.album_name)
      if (form.value.release_date) formData.append('release_date', form.value.release_date)
    }

    await api.podcasts.createEpisode(formData)

    ElMessage.success('上传成功！音频正在处理中...')
    router.push('/creator')
  } catch (error) {
    // 错误已处理
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

async function handleGenerateSubmit() {
  const valid = await generateFormRef.value.validate().catch(() => false)
  if (!valid) return

  generating.value = true

  try {
    const response = await api.post('/episodes/generate/', generateForm.value)
    ElMessage.success('生成任务已提交，请稍候查看')
    router.push('/creator')
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.message || '提交失败')
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.upload-episode-page {
  padding: var(--spacing-xl) 0;
}

.page-title {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--spacing-xl);
}

.form-card {
  max-width: 800px;
  padding: var(--spacing-xl);
}

.mode-selector {
  margin-bottom: 2rem;
  display: flex;
  justify-content: center;
}

.mode-selector :deep(.el-radio-button__inner) {
  padding: 12px 24px;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.audio-uploader {
  width: 100%;
}

.audio-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-default);
  border: 2px solid var(--border-color-light);
}

.audio-icon {
  font-size: 24px;
  color: var(--color-primary);
}

.form-hint {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-xs);
}

.script-helper {
  background: var(--bg-secondary);
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.script-helper p {
  margin: 0 0 0.5rem 0;
}

.script-helper code {
  display: block;
  font-family: monospace;
  color: var(--primary-color);
  margin-top: 0.25rem;
}
</style>
