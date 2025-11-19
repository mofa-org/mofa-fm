<template>
  <div class="edit-episode-page">
    <div class="container">
      <h1 class="page-title">编辑单集</h1>

      <div class="form-card mofa-card" v-if="!loading">
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

          <el-form-item label="音频文件">
            <el-upload
              class="audio-uploader"
              :on-change="handleAudioChange"
              :auto-upload="false"
              accept="audio/*"
              :show-file-list="false"
            >
              <el-button v-if="!audioFile" type="primary">
                <el-icon><Upload /></el-icon>
                更换音频文件
              </el-button>
              <div v-else class="audio-info">
                <el-icon class="audio-icon"><Headset /></el-icon>
                <span>{{ audioFile.name }}</span>
                <el-button type="danger" text @click.stop="removeAudio">
                  删除
                </el-button>
              </div>
            </el-upload>
            <p class="form-hint">留空则不更新音频文件。支持 MP3、WAV、M4A 等格式，最大 500MB</p>
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
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              保存修改
            </el-button>
            <el-button @click="$router.back()">取消</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-else class="loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Upload, Headset, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const formRef = ref()
const loading = ref(true)
const submitting = ref(false)
const audioFile = ref(null)
const showContentType = ref('podcast')

const form = ref({
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

const rules = {
  title: [{ required: true, message: '请输入单集标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入单集描述', trigger: 'blur' }]
}

onMounted(async () => {
  try {
    const { showSlug, episodeSlug } = route.params

    // 加载单集详情
    const episode = await api.podcasts.getEpisode(showSlug, episodeSlug)

    // 获取节目内容类型
    showContentType.value = episode.show.content_type || 'podcast'

    // 填充表单
    form.value.title = episode.title
    form.value.description = episode.description
    form.value.season_number = episode.season_number || 1
    form.value.episode_number = episode.episode_number || 1

    // 音乐字段
    form.value.artist = episode.artist || ''
    form.value.genre = episode.genre || ''
    form.value.album_name = episode.album_name || ''
    form.value.release_date = episode.release_date || null

    loading.value = false
  } catch (error) {
    console.error('加载单集信息失败：', error)
    ElMessage.error('加载单集信息失败')
    router.push('/creator')
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

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)

    // 只在有新音频文件时才上传
    if (form.value.audio_file) {
      formData.append('audio_file', form.value.audio_file)
    }

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

    const { showSlug, episodeSlug } = route.params
    await api.podcasts.updateEpisode(showSlug, episodeSlug, formData)

    ElMessage.success('保存成功')
    router.push(`/shows/${showSlug}`)
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.edit-episode-page {
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

.loading {
  text-align: center;
  padding: 4rem 0;
  color: var(--color-text-secondary);
}

.loading .el-icon {
  font-size: 48px;
  margin-bottom: 1rem;
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
