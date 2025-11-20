<template>
  <div class="global-player">
    <div class="player-content">
      <!-- 左侧：单集信息 -->
      <div class="player-info">
        <img :src="currentEpisode.cover_url" alt="封面" class="player-cover" />
        <div class="player-meta">
          <div class="episode-title">{{ currentEpisode.title }}</div>
          <div class="show-title">{{ currentEpisode.show.title }}</div>
        </div>
      </div>

      <!-- 中间：播放控制 -->
      <div class="player-controls">
        <div class="control-buttons">
          <button
            class="player-btn player-btn-nav"
            @click="playerStore.playPrevious()"
            :disabled="!hasPrevious"
            title="上一首"
          >
            <el-icon><ArrowLeftBold /></el-icon>
          </button>
          <button class="player-btn player-btn-skip" @click="playerStore.skip(-15)" title="后退15秒">
            <el-icon><DArrowLeft /></el-icon>
          </button>
          <button class="player-btn player-btn-play" @click="playerStore.toggle()">
            <el-icon :size="24">
              <VideoPause v-if="isPlaying" />
              <VideoPlay v-else />
            </el-icon>
          </button>
          <button class="player-btn player-btn-skip" @click="playerStore.skip(15)" title="前进15秒">
            <el-icon><DArrowRight /></el-icon>
          </button>
          <button
            class="player-btn player-btn-nav"
            @click="playerStore.playNext()"
            :disabled="!hasNext"
            title="下一首"
          >
            <el-icon><ArrowRightBold /></el-icon>
          </button>
        </div>

        <div class="progress-bar">
          <span class="time-text">{{ formattedCurrentTime }}</span>
          <el-slider
            v-model="sliderValue"
            :show-tooltip="false"
            @change="handleSeek"
            class="progress-slider"
          />
          <span class="time-text">{{ formattedDuration }}</span>
        </div>
      </div>

      <!-- 右侧：倍速控制 -->
      <div class="player-options">
        <el-dropdown @command="handleRateChange" trigger="click">
          <button class="player-btn player-btn-speed" title="播放速度">
            <span class="speed-text">{{ playbackRate }}x</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="0.5">0.5x</el-dropdown-item>
              <el-dropdown-item command="0.75">0.75x</el-dropdown-item>
              <el-dropdown-item command="1">1.0x</el-dropdown-item>
              <el-dropdown-item command="1.25">1.25x</el-dropdown-item>
              <el-dropdown-item command="1.5">1.5x</el-dropdown-item>
              <el-dropdown-item command="2">2.0x</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { usePlayerStore } from '@/stores/player'
import {
  VideoPlay,
  VideoPause,
  DArrowLeft,
  DArrowRight,
  ArrowLeftBold,
  ArrowRightBold
} from '@element-plus/icons-vue'

const playerStore = usePlayerStore()

const sliderValue = ref(0)

const currentEpisode = computed(() => playerStore.currentEpisode)
const isPlaying = computed(() => playerStore.isPlaying)
const currentTime = computed(() => playerStore.currentTime)
const duration = computed(() => playerStore.duration)
const playbackRate = computed(() => playerStore.playbackRate)
const formattedCurrentTime = computed(() => playerStore.formattedCurrentTime)
const formattedDuration = computed(() => playerStore.formattedDuration)
const hasPrevious = computed(() => playerStore.hasPrevious)
const hasNext = computed(() => playerStore.hasNext)

// 同步进度条
watch(() => playerStore.progress, (val) => {
  sliderValue.value = val
})

function handleSeek(val) {
  const newTime = (val / 100) * duration.value
  playerStore.seek(newTime)
}

function handleRateChange(rate) {
  playerStore.setPlaybackRate(parseFloat(rate))
}
</script>

<style scoped>
.global-player {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--player-height);
  background: var(--color-white);
  border-top: var(--border-width) solid var(--border-color);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
  z-index: 99;
}

.global-player::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-bar);
}

.player-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 var(--spacing-lg);
  gap: var(--spacing-xl);
}

.player-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  min-width: 0;
  flex: 0 0 300px;
}

.player-cover {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-default);
  border: 2px solid var(--border-color);
  object-fit: cover;
}

.player-meta {
  flex: 1;
  min-width: 0;
}

.episode-title {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.show-title {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.player-controls {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--spacing-xs);
  min-width: 0;
}

.control-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
}

.progress-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.time-text {
  font-size: var(--font-sm);
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
  min-width: 45px;
}

.player-options {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex: 0 0 auto;
}

/* 播放器按钮 - 马卡龙风格 */
.player-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 2px solid var(--border-color);
  border-radius: 50%;
  background: var(--color-white);
  cursor: pointer;
  transition: var(--transition-fast);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.08);
  padding: 0;
  outline: none;
}

.player-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.12);
}

.player-btn:active {
  transform: translate(0, 0);
  box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.08);
}

/* 上一首/下一首按钮 */
.player-btn-nav {
  width: 40px;
  height: 40px;
  color: var(--color-text-primary);
}

.player-btn-nav:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.player-btn-nav:disabled:hover {
  transform: none;
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.08);
}

/* 跳过按钮 */
.player-btn-skip {
  width: 36px;
  height: 36px;
  color: var(--color-text-primary);
}

/* 播放/暂停按钮 */
.player-btn-play {
  width: 48px;
  height: 48px;
  background: var(--gradient-primary);
  color: var(--color-white);
  border-color: var(--color-primary-dark);
}

.player-btn-play:hover {
  box-shadow: 4px 4px 0 rgba(255, 81, 59, 0.3);
}

/* 速度按钮 */
.player-btn-speed {
  min-width: 48px;
  height: 36px;
  padding: 0 8px;
  border-radius: var(--radius-default);
  color: var(--color-text-primary);
}

.speed-text {
  font-size: var(--font-sm);
  font-weight: var(--font-bold);
  line-height: 1;
}

/* 进度条样式 */
.progress-slider {
  flex: 1;
}

.progress-slider :deep(.el-slider__runway) {
  height: 6px;
  background: var(--color-light-gray);
  border-radius: 3px;
}

.progress-slider :deep(.el-slider__bar) {
  height: 6px;
  background: var(--gradient-primary);
  border-radius: 3px;
}

.progress-slider :deep(.el-slider__button-wrapper) {
  width: 16px;
  height: 16px;
  top: -5px;
}

.progress-slider :deep(.el-slider__button) {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-primary);
  background: var(--color-white);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.1);
}

.progress-slider :deep(.el-slider__button):hover {
  transform: scale(1.2);
}

/* 响应式 */
@media (max-width: 768px) {
  .player-content {
    padding: 0 var(--spacing-md);
    gap: var(--spacing-md);
  }

  .player-info {
    flex: 0 0 auto;
    min-width: 0;
  }

  .player-cover {
    width: 40px;
    height: 40px;
  }

  .episode-title {
    font-size: var(--font-sm);
  }

  .show-title {
    font-size: var(--font-xs);
  }

  .player-btn-nav {
    width: 36px;
    height: 36px;
  }

  .player-btn-skip {
    width: 32px;
    height: 32px;
  }

  .player-btn-play {
    width: 40px;
    height: 40px;
  }

  .time-text {
    font-size: var(--font-xs);
    min-width: 35px;
  }

  .player-options {
    flex: 0 0 auto;
  }

  .player-btn-speed {
    min-width: 40px;
    height: 32px;
    padding: 0 6px;
  }

  .speed-text {
    font-size: var(--font-xs);
  }
}

@media (max-width: 480px) {
  .player-content {
    padding: 0 var(--spacing-sm);
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .player-info {
    flex: 0 0 auto;
    gap: var(--spacing-xs);
    order: 1;
  }

  .player-cover {
    width: 48px;
    height: 48px;
  }

  .player-meta {
    display: none;
  }

  .player-controls {
    order: 3;
    width: 100%;
    gap: var(--spacing-xs);
  }

  .control-buttons {
    gap: var(--spacing-sm);
  }

  .player-btn-nav {
    width: 32px;
    height: 32px;
  }

  .player-btn-nav :deep(.el-icon) {
    font-size: 16px !important;
  }

  .player-btn-skip {
    width: 28px;
    height: 28px;
  }

  .player-btn-skip :deep(.el-icon) {
    font-size: 14px !important;
  }

  .player-btn-play {
    width: 44px;
    height: 44px;
  }

  .player-btn-play :deep(.el-icon) {
    font-size: 20px !important;
  }

  .progress-bar {
    gap: 0;
  }

  .time-text {
    display: none;
  }

  .progress-slider {
    flex: 1;
  }

  .progress-slider :deep(.el-slider__runway) {
    height: 6px;
    background: var(--color-light-gray);
  }

  .progress-slider :deep(.el-slider__bar) {
    height: 6px;
  }

  .progress-slider :deep(.el-slider__button-wrapper) {
    width: 16px;
    height: 16px;
    top: -5px;
  }

  .progress-slider :deep(.el-slider__button) {
    width: 16px;
    height: 16px;
    border: 2px solid var(--color-primary);
  }

  .player-options {
    order: 2;
    flex: 0 0 auto;
  }

  .player-btn-speed {
    min-width: 40px;
    height: 32px;
    padding: 0 6px;
  }

  .speed-text {
    font-size: var(--font-xs);
  }
}
</style>
