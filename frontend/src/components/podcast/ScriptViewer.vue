<template>
  <div class="script-viewer">
    <div class="script-header">
      <h3>播客脚本</h3>
      <div class="script-actions">
        <el-button
          v-if="isCreator && !isEditing"
          @click="startEdit"
          size="small"
          :icon="Edit"
        >
          编辑脚本
        </el-button>
        <template v-if="isEditing">
          <el-button
            @click="cancelEdit"
            size="small"
          >
            取消
          </el-button>
          <el-button
            type="primary"
            @click="saveScript"
            size="small"
            :loading="saving"
          >
            保存
          </el-button>
        </template>
      </div>
    </div>

    <div v-if="!script && !isEditing" class="empty-state">
      <el-empty description="暂无脚本内容" />
    </div>

    <div v-else class="script-content">
      <!-- 编辑模式 -->
      <el-input
        v-if="isEditing"
        v-model="editedScript"
        type="textarea"
        :rows="20"
        placeholder="请输入脚本内容（支持Markdown格式，使用【角色名】标记角色对话）"
        class="script-editor"
      />

      <!-- 查看模式 -->
      <div v-else class="script-display">
        <div
          v-for="(block, index) in parsedScript"
          :key="index"
          :class="['script-block', block.type]"
        >
          <div v-if="block.type === 'speaker'" class="speaker-tag">
            【{{ block.content }}】
          </div>
          <div v-else-if="block.type === 'dialogue'" class="dialogue-text">
            {{ block.content }}
          </div>
          <div v-else class="normal-text">
            {{ block.content }}
          </div>
        </div>
      </div>

      <div v-if="isCreator && !isEditing" class="tip">
        <el-icon><InfoFilled /></el-icon>
        提示：您可以编辑脚本来调整TTS发音，比如使用错别字让AI读得更准确
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, InfoFilled } from '@element-plus/icons-vue'
import api from '@/api'

const props = defineProps({
  episodeId: {
    type: Number,
    required: true
  },
  script: {
    type: String,
    default: ''
  },
  isCreator: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['scriptUpdated'])

const isEditing = ref(false)
const editedScript = ref('')
const saving = ref(false)

// 解析脚本为结构化数据
const parsedScript = computed(() => {
  if (!props.script) return []

  const blocks = []
  const lines = props.script.split('\n')

  for (let line of lines) {
    line = line.trim()
    if (!line) continue

    // 匹配【角色名】
    const speakerMatch = line.match(/^【([^】]+)】(.*)/)
    if (speakerMatch) {
      blocks.push({
        type: 'speaker',
        content: speakerMatch[1]
      })
      if (speakerMatch[2].trim()) {
        blocks.push({
          type: 'dialogue',
          content: speakerMatch[2].trim()
        })
      }
    } else if (line.startsWith('#')) {
      // 标题
      blocks.push({
        type: 'heading',
        content: line
      })
    } else {
      // 普通对话或文本
      // 如果前一个block是speaker，则这是对话
      if (blocks.length > 0 && blocks[blocks.length - 1].type === 'speaker') {
        blocks.push({
          type: 'dialogue',
          content: line
        })
      } else {
        blocks.push({
          type: 'text',
          content: line
        })
      }
    }
  }

  return blocks
})

const startEdit = () => {
  editedScript.value = props.script
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
  editedScript.value = ''
}

const saveScript = async () => {
  if (!editedScript.value.trim()) {
    ElMessage.warning('脚本内容不能为空')
    return
  }

  saving.value = true
  try {
    const response = await api.patch(`/podcasts/episodes/${props.episodeId}/update-script/`, {
      script: editedScript.value
    })

    ElMessage.success('脚本更新成功')
    isEditing.value = false
    emit('scriptUpdated', response.data)
  } catch (error) {
    console.error('更新脚本失败:', error)
    ElMessage.error(error.response?.data?.error || '更新脚本失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.script-viewer {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.script-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.script-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.script-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.script-content {
  position: relative;
}

.script-editor {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
}

.script-editor :deep(textarea) {
  line-height: 1.6;
}

.script-display {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  line-height: 1.8;
}

.script-block {
  margin-bottom: 12px;
}

.script-block.speaker {
  margin-top: 20px;
}

.speaker-tag {
  display: inline-block;
  font-weight: 600;
  color: #ff513b;
  font-size: 15px;
  padding: 4px 12px;
  background: #fff5f3;
  border-radius: 6px;
  margin-bottom: 8px;
}

.dialogue-text {
  color: #333;
  font-size: 14px;
  line-height: 1.8;
  margin-left: 12px;
  padding-left: 12px;
  border-left: 3px solid #ff513b20;
}

.normal-text,
.heading {
  color: #666;
  font-size: 14px;
}

.heading {
  font-weight: 600;
  color: #333;
  margin: 16px 0 8px 0;
}

.tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: #e6f4ff;
  border: 1px solid #91caff;
  border-radius: 6px;
  color: #0958d9;
  font-size: 13px;
}

.tip .el-icon {
  flex-shrink: 0;
}
</style>
