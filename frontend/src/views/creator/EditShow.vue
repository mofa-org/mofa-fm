<template>
  <div class="edit-show-page">
    <div class="container">
      <h1 class="page-title">编辑节目</h1>

      <div class="form-card mofa-card" v-if="dataLoaded">
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

          <el-form-item label="节目描述" prop="description">
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
            <p class="form-hint">推荐尺寸：1400x1400 像素，留空则不更新封面</p>
          </el-form-item>

          <el-form-item label="分类" prop="category_id" v-if="categories.length > 0" v-show="false">
            <el-select v-model="form.category_id" placeholder="选择分类">
              <el-option
                v-for="cat in categories"
                :key="cat.id"
                :label="cat.name"
                :value="cat.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="标签" v-if="tags.length > 0" v-show="false">
            <el-select v-model="form.tag_ids" multiple placeholder="选择标签（可选）">
              <el-option
                v-for="tag in tags"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-select>
          </el-form-item>

          <el-divider />

          <el-form-item label="">
            <VisibilitySelector v-model="form.visibility" label="谁可以看到这个节目？" />
          </el-form-item>

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
import { usePodcastsStore } from '@/stores/podcasts'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { Plus, Loading } from '@element-plus/icons-vue'
import VisibilitySelector from '@/components/common/VisibilitySelector.vue'

const route = useRoute()
const router = useRouter()
const podcastsStore = usePodcastsStore()

const formRef = ref()
const dataLoaded = ref(false)
const submitting = ref(false)
const coverPreview = ref('')
const coverFile = ref(null)

const form = ref({
  content_type: 'podcast',
  title: '',
  description: '',
  category_id: null,
  tag_ids: [],
  visibility: 'public'
})

const categories = ref([])
const tags = ref([])

const rules = {
  content_type: [{ required: true, message: '请选择内容类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入节目名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入节目描述', trigger: 'blur' }]
}

onMounted(async () => {
  try {
    const slug = route.params.slug

    // 并行加载所有数据
    const [categoriesData, tagsData, show] = await Promise.all([
      podcastsStore.fetchCategories().catch(() => []),
      podcastsStore.fetchTags().catch(() => []),
      api.podcasts.getShow(slug)
    ])

    // 确保数据是数组且过滤掉 null 值
    categories.value = Array.isArray(categoriesData)
      ? categoriesData.filter(item => item !== null && item !== undefined)
      : []

    tags.value = Array.isArray(tagsData)
      ? tagsData.filter(item => item !== null && item !== undefined)
      : []

    // 填充表单
    form.value.content_type = show.content_type || 'podcast'
    form.value.title = show.title
    form.value.description = show.description
    form.value.category_id = show.category?.id || null
    form.value.tag_ids = Array.isArray(show.tags)
      ? show.tags.map(tag => tag.id).filter(id => id !== null && id !== undefined)
      : []
    form.value.visibility = show.visibility || 'public'
    coverPreview.value = show.cover_url

    // 所有数据加载完成后才显示表单
    dataLoaded.value = true
  } catch (error) {
    console.error('加载节目信息失败：', error)
    ElMessage.error('加载节目信息失败')
    router.push('/creator')
  }
})

function handleCoverChange(file) {
  coverFile.value = file.raw
  coverPreview.value = URL.createObjectURL(file.raw)
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('content_type', form.value.content_type)
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    formData.append('visibility', form.value.visibility)

    // 只在有新封面时才上传
    if (coverFile.value) {
      formData.append('cover', coverFile.value)
    }

    if (form.value.category_id) {
      formData.append('category_id', form.value.category_id)
    }

    if (form.value.tag_ids.length > 0) {
      form.value.tag_ids.forEach(id => formData.append('tag_ids', id))
    }

    const slug = route.params.slug
    await api.podcasts.updateShow(slug, formData)

    ElMessage.success('保存成功')
    router.push('/creator')
  } catch (error) {
    console.error('保存失败：', error)
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.edit-show-page {
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

.cover-uploader {
  display: block;
}

.cover-preview {
  width: 200px;
  height: 200px;
  object-fit: cover;
  border-radius: var(--radius-default);
  cursor: pointer;
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
