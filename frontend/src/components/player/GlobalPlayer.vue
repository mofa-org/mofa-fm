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
          <el-button :icon="DArrowLeft" circle @click="playerStore.skip(-15)" title="后退15秒" />
          <el-button
            :icon="isPlaying ? VideoPause : VideoPlay"
            circle
            size="large"
            type="primary"
            @click="playerStore.toggle()"
          />
          <el-button :icon="DArrowRight" circle @click="playerStore.skip(15)" title="前进15秒" />
        </div>

        <div class="progress-bar">
          <span class="time-text">{{ formattedCurrentTime }}</span>
          <el-slider
            v-model="sliderValue"
            :show-tooltip="false"
            @change="handleSeek"
          />
          <span class="time-text">{{ formattedDuration }}</span>
        </div>
      </div>

      <!-- 右侧：音量和播放速度 -->
      <div class="player-options">
        <!-- 播放速度 -->
        <el-dropdown @command="handleRateChange">
          <el-button :icon="Odometer">
            {{ playbackRate }}x
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="0.75">0.75x</el-dropdown-item>
              <el-dropdown-item command="1.0">1.0x</el-dropdown-item>
              <el-dropdown-item command="1.25">1.25x</el-dropdown-item>
              <el-dropdown-item command="1.5">1.5x</el-dropdown-item>
              <el-dropdown-item command="2.0">2.0x</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 音量控制 -->
        <el-popover placement="top" :width="60" trigger="hover">
          <el-slider
            v-model="volumeValue"
            vertical
            :height="100"
            :show-tooltip="false"
            @input="handleVolumeChange"
          />
          <template #reference>
            <el-button :icon="volume > 0 ? Microphone : Mute" />
          </template>
        </el-popover>
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
  Microphone,
  Mute,
  Odometer
} from '@element-plus/icons-vue'

const playerStore = usePlayerStore()

const sliderValue = ref(0)
const volumeValue = ref(80)

const currentEpisode = computed(() => playerStore.currentEpisode)
const isPlaying = computed(() => playerStore.isPlaying)
const currentTime = computed(() => playerStore.currentTime)
const duration = computed(() => playerStore.duration)
const volume = computed(() => playerStore.volume)
const playbackRate = computed(() => playerStore.playbackRate)
const formattedCurrentTime = computed(() => playerStore.formattedCurrentTime)
const formattedDuration = computed(() => playerStore.formattedDuration)

// 同步进度条
watch(() => playerStore.progress, (val) => {
  sliderValue.value = val
})

// 同步音量
watch(() => playerStore.volume, (val) => {
  volumeValue.value = val * 100
})

function handleSeek(val) {
  const newTime = (val / 100) * duration.value
  playerStore.seek(newTime)
}

function handleVolumeChange(val) {
  playerStore.setVolume(val / 100)
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
  gap: var(--spacing-sm);
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

@media (max-width: 768px) {
  .player-info {
    flex: 0 0 auto;
  }

  .player-options {
    display: none;
  }
}
</style>
