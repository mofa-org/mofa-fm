<template>
  <div class="create-show-page">
    <div class="container">
      <h1 class="page-title">创建内容节目</h1>

      <div class="form-card mofa-card">
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="内容类型" prop="content_type">
            <el-radio-group v-model="form.content_type">
              <el-radio value="podcast">播客</el-radio>
              <el-radio value="music">音乐</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="节目名称" prop="title">
            <el-input
              v-model="form.title"
              :placeholder="form.content_type === 'podcast' ? '输入播客节目名称' : '输入音乐专辑/歌单名称'"
            />
          </el-form-item>

          <el-form-item label="节目描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="5"
              :placeholder="form.content_type === 'podcast' ? '介绍一下你的播客...' : '介绍一下你的音乐专辑...'"
            />
          </el-form-item>

          <el-form-item label="封面图片">
            <el-upload
              class="cover-uploader"
              :show-file-list="false"
              :on-change="handleCoverChange"
              :auto-upload="false"
              accept="image/*"
            >
              <img v-if="coverPreview" :src="coverPreview" class="cover-preview" />
              <el-icon v-else class="cover-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <p class="form-hint">可选；推荐尺寸：1400x1400 像素</p>
          </el-form-item>

          <el-form-item label="分类" prop="category_id" v-show="false">
            <el-select v-model="form.category_id" placeholder="选择分类">
              <el-option
                v-for="cat in (categories || [])"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="标签" v-show="false">
            <el-select v-model="form.tag_ids" multiple placeholder="选择标签（可选）">
              <el-option
                v-for="tag in (tags || [])"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </el-form-item>

          <el-divider />

          <div class="visibility-panel">
            <button
              type="button"
              class="visibility-toggle"
              @click="visibilityCollapsed = !visibilityCollapsed"
            >
              <span>谁可以看到这个节目？</span>
              <el-icon class="toggle-icon" :class="{ expanded: !visibilityCollapsed }">
                <ArrowDown />
              </el-icon>
            </button>
            <el-collapse-transition>
              <div v-show="!visibilityCollapsed" class="visibility-content">
                <VisibilitySelector v-model="form.visibility" label="" />
              </div>
            </el-collapse-transition>
          </div>

          <el-form-item>
            <el-button type="primary" @click="handleSubmit" :loading="loading">
              创建节目
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
import { useRouter } from 'vue-router'
import { usePodcastsStore } from '@/stores/podcasts'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Plus, ArrowDown } from '@element-plus/icons-vue'
import VisibilitySelector from '@/components/common/VisibilitySelector.vue'

const router = useRouter()
const podcastsStore = usePodcastsStore()

const formRef = ref()
const loading = ref(false)
const coverPreview = ref('')
const coverFile = ref(null)
const visibilityCollapsed = ref(true)

const form = ref({
  content_type: 'podcast',
  title: '',
  description: '',
  cover: null,
  category_id: null,
  tag_ids: [],
  visibility: 'public'
})

const categories = ref([])
const tags = ref([])

const rules = {
  content_type: [{ required: true, message: '请选择内容类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入节目名称', trigger: 'blur' }]
}

onMounted(async () => {
  try {
    const [categoriesData, tagsData] = await Promise.all([
      podcastsStore.fetchCategories().catch(() => []),
      podcastsStore.fetchTags().catch(() => [])
    ])

    categories.value = Array.isArray(categoriesData)
      ? categoriesData.filter(item => item !== null && item !== undefined)
      : []

    tags.value = Array.isArray(tagsData)
      ? tagsData.filter(item => item !== null && item !== undefined)
      : []
  } catch (error) {
    console.error('加载分类和标签失败：', error)
    categories.value = []
    tags.value = []
  }
})

function handleCoverChange(file) {
  coverFile.value = file.raw
  form.value.cover = file.raw
  coverPreview.value = URL.createObjectURL(file.raw)
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('content_type', form.value.content_type)
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    if (coverFile.value) {
      formData.append('cover', coverFile.value)
    }
    formData.append('visibility', form.value.visibility)
    // 如果没有选择分类，默认为科技类（ID=1）
    if (form.value.category_id) {
      formData.append('category_id', form.value.category_id)
    } else {
      formData.append('category_id', 1)
    }
    if (form.value.tag_ids.length > 0) {
      form.value.tag_ids.forEach(id => formData.append('tag_ids', id))
    }

    await api.podcasts.createShow(formData)
    ElMessage.success('创建成功')
    router.push('/creator')
  } catch (error) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-show-page {
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

.cover-uploader {
  display: block;
}

.cover-preview {
  width: 200px;
  height: 200px;
  object-fit: cover;
  border-radius: var(--radius-default);
}

.cover-uploader-icon {
  font-size: 48px;
  color: var(--color-text-placeholder);
  width: 200px;
  height: 200px;
  border: 3px dashed var(--border-color-light);
  border-radius: var(--radius-default);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
}

.cover-uploader-icon:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.form-hint {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-xs);
}

.visibility-panel {
  margin-bottom: var(--spacing-lg);
}

.visibility-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-default);
  background: var(--color-white);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
}

.toggle-icon {
  transition: transform 0.2s ease;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

.visibility-content {
  margin-top: var(--spacing-sm);
}

@media (max-width: 768px) {
  .create-show-page {
    padding: var(--spacing-lg) 0;
  }

  .page-title {
    font-size: var(--font-2xl);
    margin-bottom: var(--spacing-lg);
  }

  .form-card {
    padding: var(--spacing-lg);
  }

  .cover-preview,
  .cover-uploader-icon {
    width: 160px;
    height: 160px;
  }
}

@media (max-width: 480px) {
  .create-show-page {
    padding: var(--spacing-md) 0;
  }

  .page-title {
    font-size: var(--font-xl);
  }

  .form-card {
    padding: var(--spacing-md);
  }
}
</style>
