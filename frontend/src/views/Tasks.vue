<template>
  <div class="page-container">
    <el-card style="margin-bottom: 20px">
      <template #header>
        <span class="card-title">创建音频任务</span>
      </template>

      <el-form :model="createForm" label-width="100px">
        <el-form-item label="选择脚本">
          <el-select v-model="createForm.script_id" placeholder="请选择脚本" style="width: 100%">
            <el-option
              v-for="script in scripts"
              :key="script.id"
              :label="script.title"
              :value="script.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="大牛声音">
          <el-select v-model="createForm.voice_config.daniu" placeholder="选择声音" style="width: 100%">
            <el-option
              v-for="voice in maleVoices"
              :key="voice.voice_id"
              :label="voice.display_name"
              :value="voice.voice_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="一帆声音">
          <el-select v-model="createForm.voice_config.yifan" placeholder="选择声音" style="width: 100%">
            <el-option
              v-for="voice in femaleVoices"
              :key="voice.voice_id"
              :label="voice.display_name"
              :value="voice.voice_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleCreate" :loading="creating">
            生成音频
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">任务列表</span>
          <el-button @click="fetchTasks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading">
        <el-table-column prop="id" label="任务ID" width="280" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="row.status === 'completed' ? 'success' : null" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              size="small"
              type="success"
              @click="viewTask(row.id)"
            >
              下载
            </el-button>
            <el-button
              v-else
              size="small"
              @click="checkStatus(row.id)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 下载对话框 -->
    <el-dialog v-model="showDownloadDialog" title="下载音频" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag type="success">已完成</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="时长">
          {{ currentTask.duration }}秒
        </el-descriptions-item>
        <el-descriptions-item label="消耗Credit">
          {{ currentTask.credit_cost }}
        </el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px">
        <el-space>
          <el-button
            v-for="audio in currentTask.audios"
            :key="audio.id"
            type="primary"
            @click="downloadAudio(audio)"
          >
            下载 {{ audio.format.toUpperCase() }}
          </el-button>
        </el-space>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskAPI, scriptAPI } from '@/api'
import { useUserStore } from '@/store/user'

const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const creating = ref(false)
const scripts = ref([])
const tasks = ref([])
const voices = ref([])
const showDownloadDialog = ref(false)
const currentTask = ref({ audios: [] })

const createForm = ref({
  script_id: route.query.scriptId || '',
  voice_config: {
    daniu: '',
    yifan: ''
  }
})

const maleVoices = computed(() => voices.value.filter(v => v.category === 'male'))
const femaleVoices = computed(() => voices.value.filter(v => v.category === 'female'))

const statusType = (status) => {
  const map = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
  return map[status] || 'info'
}

const statusText = (status) => {
  const map = { pending: '等待中', processing: '生成中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const fetchScripts = async () => {
  try {
    scripts.value = await scriptAPI.list()
  } catch (error) {
    ElMessage.error('加载脚本失败')
  }
}

const fetchVoices = async () => {
  try {
    voices.value = await taskAPI.getVoices()
    if (voices.value.length > 0) {
      createForm.value.voice_config.daniu = maleVoices.value[0]?.voice_id
      createForm.value.voice_config.yifan = femaleVoices.value[0]?.voice_id
    }
  } catch (error) {
    ElMessage.error('加载声音列表失败')
  }
}

const fetchTasks = async () => {
  loading.value = true
  try {
    tasks.value = await taskAPI.list()
  } catch (error) {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!createForm.value.script_id) {
    ElMessage.warning('请选择脚本')
    return
  }

  creating.value = true
  try {
    await taskAPI.create(createForm.value)
    ElMessage.success('任务已创建')
    userStore.updateCredit(-50) // Mock 扣费
    fetchTasks()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const checkStatus = async (taskId) => {
  try {
    const task = await taskAPI.get(taskId)
    if (task.status === 'completed') {
      viewTask(taskId)
    } else {
      ElMessage.info(`任务状态：${statusText(task.status)}，进度：${task.progress}%`)
    }
  } catch (error) {
    ElMessage.error('查询失败')
  }
}

const viewTask = async (taskId) => {
  try {
    const task = await taskAPI.get(taskId)
    currentTask.value = {
      id: task.id,
      duration: task.audios[0]?.duration || 0,
      credit_cost: task.credit_cost,
      audios: task.audios
    }
    showDownloadDialog.value = true
  } catch (error) {
    ElMessage.error('加载任务详情失败')
  }
}

const downloadAudio = (audio) => {
  const url = taskAPI.downloadAudio(audio.id)
  window.open(url, '_blank')
}

onMounted(() => {
  fetchScripts()
  fetchVoices()
  fetchTasks()
})
</script>

<style scoped>
.card-header {
  padding: 0;
}
</style>
