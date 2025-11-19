<template>
  <div class="create-show-page">
    <div class="container">
      <h1 class="page-title">创建播客节目</h1>

      <div class="form-card mofa-card">
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="节目名称" prop="title">
            <el-input v-model="form.title" placeholder="输入节目名称" />
          </el-form-item>

          <el-form-item label="节目描述" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="5"
              placeholder="介绍一下你的播客..."
            />
          </el-form-item>

          <el-form-item label="封面图片" prop="cover">
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
            <p class="form-hint">推荐尺寸：1400x1400 像素</p>
          </el-form-item>

          <el-form-item label="分类" prop="category_id">
            <el-select v-model="form.category_id" placeholder="选择分类">
              <el-option
                v-for="cat in (categories || [])"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="标签">
            <el-select v-model="form.tag_ids" multiple placeholder="选择标签（可选）">
              <el-option
                v-for="tag in (tags || [])"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </el-form-item>

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
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()
const podcastsStore = usePodcastsStore()

const formRef = ref()
const loading = ref(false)
const coverPreview = ref('')
const coverFile = ref(null)

const form = ref({
  title: '',
  description: '',
  cover: null,
  category_id: null,
  tag_ids: []
})

const categories = ref([])
const tags = ref([])

const rules = {
  title: [{ required: true, message: '请输入节目名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入节目描述', trigger: 'blur' }],
  cover: [{ required: true, message: '请上传封面图片', trigger: 'change' }]
}

onMounted(async () => {
  categories.value = await podcastsStore.fetchCategories()
  tags.value = await podcastsStore.fetchTags()
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
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    formData.append('cover', coverFile.value)
    if (form.value.category_id) {
      formData.append('category_id', form.value.category_id)
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
</style>
