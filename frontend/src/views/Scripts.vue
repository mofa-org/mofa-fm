<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">我的脚本</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传脚本
          </el-button>
        </div>
      </template>

      <el-table :data="scripts" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="source" label="来源" width="120">
          <template #default="{ row }">
            <el-tag :type="row.source === 'ai_generated' ? 'success' : 'info'">
              {{ row.source === 'ai_generated' ? 'AI生成' : '手动上传' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_chars" label="字数" width="100" />
        <el-table-column prop="estimated_duration" label="预估时长" width="120">
          <template #default="{ row }">
            {{ row.estimated_duration.toFixed(1) }}秒
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewScript(row)">查看</el-button>
            <el-button size="small" type="primary" @click="generateAudio(row)">
              生成音频
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传脚本对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传脚本" width="600px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="uploadForm.title" placeholder="脚本标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="uploadForm.content"
            type="textarea"
            :rows="12"
            placeholder="【大牛】xxxxx&#10;&#10;【一帆】xxxxx"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看脚本对话框 -->
    <el-dialog v-model="showViewDialog" title="脚本内容" width="700px">
      <div style="white-space: pre-wrap; line-height: 1.8">
        {{ currentScript.content }}
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { scriptAPI } from '@/api'

const router = useRouter()
const loading = ref(false)
const uploading = ref(false)
const scripts = ref([])
const showUploadDialog = ref(false)
const showViewDialog = ref(false)
const currentScript = ref({})

const uploadForm = ref({
  title: '',
  content: ''
})

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchScripts = async () => {
  loading.value = true
  try {
    scripts.value = await scriptAPI.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleUpload = async () => {
  if (!uploadForm.value.content.trim()) {
    ElMessage.warning('请输入脚本内容')
    return
  }

  uploading.value = true
  try {
    await scriptAPI.create(uploadForm.value)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.value = { title: '', content: '' }
    fetchScripts()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const viewScript = (script) => {
  currentScript.value = script
  showViewDialog.value = true
}

const generateAudio = (script) => {
  router.push({
    path: '/tasks',
    query: { scriptId: script.id }
  })
}

onMounted(() => {
  fetchScripts()
})
</script>

<style scoped>
.card-header {
  padding: 0;
}
</style>
