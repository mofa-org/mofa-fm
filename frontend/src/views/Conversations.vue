<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">AI 对话</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建对话
          </el-button>
        </div>
      </template>

      <el-table :data="conversations" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="topic" label="话题" min-width="200" />
        <el-table-column prop="style" label="风格" width="120">
          <template #default="{ row }">
            <el-tag :type="styleType(row.style)">{{ styleText(row.style) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'info'">
              {{ row.status === 'completed' ? '已完成' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message_count" label="消息数" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openConversation(row.id)">
              继续对话
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建对话对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建新对话"
      width="500px"
    >
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="话题">
          <el-input
            v-model="createForm.topic"
            placeholder="例如：人工智能的最新进展"
          />
        </el-form-item>
        <el-form-item label="风格">
          <el-select v-model="createForm.style" style="width: 100%">
            <el-option label="教育科普" value="educational" />
            <el-option label="轻松闲聊" value="casual" />
            <el-option label="深度访谈" value="interview" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标时长">
          <el-input-number
            v-model="createForm.target_duration"
            :min="60"
            :max="600"
            :step="30"
          />
          秒
        </el-form-item>
        <el-form-item label="说话人">
          <el-checkbox-group v-model="createForm.speakers">
            <el-checkbox label="大牛" />
            <el-checkbox label="一帆" />
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { conversationAPI } from '@/api'

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const conversations = ref([])
const showCreateDialog = ref(false)

const createForm = ref({
  topic: '',
  style: 'educational',
  target_duration: 300,
  speakers: ['大牛', '一帆']
})

const styleType = (style) => {
  const map = { educational: 'primary', casual: 'success', interview: 'warning' }
  return map[style] || 'info'
}

const styleText = (style) => {
  const map = { educational: '教育科普', casual: '轻松闲聊', interview: '深度访谈' }
  return map[style] || style
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchConversations = async () => {
  loading.value = true
  try {
    conversations.value = await conversationAPI.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!createForm.value.topic) {
    ElMessage.warning('请输入话题')
    return
  }

  creating.value = true
  try {
    const conv = await conversationAPI.create(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    router.push(`/conversations/${conv.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const openConversation = (id) => {
  router.push(`/conversations/${id}`)
}

onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.card-header {
  padding: 0;
}
</style>
