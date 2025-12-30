<template>
  <div class="play-queue">
    <div class="queue-header">
      <h3>播放队列 ({{ playlist.length }})</h3>
      <el-button link type="primary" size="small" @click="playerStore.clearQueue">
        清空队列
      </el-button>
    </div>

    <el-scrollbar height="400px">
      <ul class="queue-list">
        <li 
          v-for="(episode, index) in playlist" 
          :key="episode.id"
          class="queue-item"
          :class="{ active: index === currentIndex }"
          @dblclick="playItem(episode)"
        >
          <div class="item-info">
            <span v-if="index === currentIndex" class="playing-indicator">
              <el-icon class="is-loading"><Loading /></el-icon>
            </span>
            <span v-else class="item-index">{{ index + 1 }}</span>
            <div class="item-meta">
              <div class="item-title">{{ episode.title }}</div>
              <div class="item-show">{{ episode.show?.title }}</div>
            </div>
          </div>
          
          <div class="item-actions">
            <el-button-group size="small">
              <el-button 
                :disabled="index === 0"
                @click.stop="moveUp(index)"
                link
                title="上移"
              >
                <el-icon><ArrowUp /></el-icon>
              </el-button>
              <el-button 
                :disabled="index === playlist.length - 1"
                @click.stop="moveDown(index)"
                link
                title="下移"
              >
                <el-icon><ArrowDown /></el-icon>
              </el-button>
            </el-button-group>
            
            <el-button 
              text 
              circle 
              size="small" 
              type="danger" 
              @click.stop="removeItem(index)"
              title="移除"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </li>
      </ul>
      <el-empty v-if="playlist.length === 0" description="队列为空" />
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { Loading, Close, ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const playerStore = usePlayerStore()

const playlist = computed(() => playerStore.playlist)
const currentIndex = computed(() => playerStore.currentIndex)

function playItem(episode) {
  playerStore.play(episode, playerStore.playlist)
}

function removeItem(index) {
  playerStore.removeFromQueue(index)
}

function moveUp(index) {
  if (index > 0) {
    playerStore.reorderQueue(index, index - 1)
  }
}

function moveDown(index) {
  if (index < playlist.value.length - 1) {
    playerStore.reorderQueue(index, index + 1)
  }
}
</script>

<style scoped>
.play-queue {
  background: var(--color-white);
  border-radius: var(--radius-lg);
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.queue-header h3 {
  margin: 0;
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
}

.queue-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: background-color 0.2s;
}

.queue-item:hover {
  background-color: var(--color-bg-secondary);
}

.queue-item.active {
  background-color: rgba(255, 81, 59, 0.05);
}

.queue-item.active .item-title {
  color: var(--color-primary);
  font-weight: var(--font-bold);
}

.item-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex: 1;
  min-width: 0; /* To allow text truncation */
}

.item-index {
  color: var(--color-text-tertiary);
  font-size: var(--font-sm);
  width: 20px;
  text-align: center;
}

.playing-indicator {
  color: var(--color-primary);
  width: 20px;
  display: flex;
  justify-content: center;
}

.item-meta {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: var(--font-sm);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-show {
  font-size: var(--font-xs);
  color: var(--color-text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  opacity: 0;
  transition: opacity 0.2s;
}

.queue-item:hover .item-actions {
  opacity: 1;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .item-actions {
    opacity: 1; /* Always show actions on mobile */
  }
}
</style>
