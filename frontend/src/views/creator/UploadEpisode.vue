<template>
  <div class="upload-episode-page">
    <div class="container">
      <h1 class="page-title">上传播客单集</h1>

      <div class="form-card mofa-card">
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
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

          <el-form-item label="季数">
            <el-input-number v-model="form.season_number" :min="1" />
          </el-form-item>

          <el-form-item label="集数">
            <el-input-number v-model="form.episode_number" :min="1" />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              @click="handleSubmit"
              :loading="uploading"
              :disabled="uploadProgress > 0 && uploadProgress < 100"
            >
              {{ uploading ? `上传中 ${uploadProgress}%` : '上传单集' }}
            </el-button>
            <el-button @click="$router.back()">取消</el-button>
          </el-form-item>

          <el-progress v-if="uploadProgress > 0" :percentage="uploadProgress" />
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
import { Upload, Headset } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const formRef = ref()
const uploading = ref(false)
const uploadProgress = ref(0)
const audioFile = ref(null)

const form = ref({
  show_id: null,
  title: '',
  description: '',
  audio_file: null,
  season_number: 1,
  episode_number: 1
})

const rules = {
  title: [{ required: true, message: '请输入单集标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入单集描述', trigger: 'blur' }],
  audio_file: [{ required: true, message: '请上传音频文件', trigger: 'change' }]
}

onMounted(() => {
  form.value.show_id = parseInt(route.params.id)
})

function handleAudioChange(file) {
  audioFile.value = file
  form.value.audio_file = file.raw
}

function removeAudio() {
  audioFile.value = null
  form.value.audio_file = null
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  uploading.value = true
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    formData.append('show_id', form.value.show_id)
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    formData.append('audio_file', form.value.audio_file)
    formData.append('season_number', form.value.season_number)
    formData.append('episode_number', form.value.episode_number)

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
</style>
