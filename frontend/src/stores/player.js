/**
 * 全局播放器 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const usePlayerStore = defineStore('player', () => {
  const currentEpisode = ref(null)
  const audio = ref(null)

  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(0.8)
  const playbackRate = ref(1.0)
  const isLoading = ref(false)

  const progress = computed(() => {
    return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
  })

  const formattedCurrentTime = computed(() => formatTime(currentTime.value))
  const formattedDuration = computed(() => formatTime(duration.value))

  // 初始化音频
  function initAudio() {
    if (audio.value) return

    audio.value = new Audio()
    audio.value.volume = volume.value

    // 时间更新
    audio.value.addEventListener('timeupdate', () => {
      currentTime.value = audio.value.currentTime
    })

    // 加载元数据
    audio.value.addEventListener('loadedmetadata', () => {
      duration.value = audio.value.duration
      isLoading.value = false
    })

    // 播放结束
    audio.value.addEventListener('ended', () => {
      isPlaying.value = false
      saveProgress(true)
    })

    // 加载中
    audio.value.addEventListener('loadstart', () => {
      isLoading.value = true
    })

    audio.value.addEventListener('canplay', () => {
      isLoading.value = false
    })

    // 错误处理
    audio.value.addEventListener('error', () => {
      isLoading.value = false
      console.error('音频加载失败')
    })

    // 每30秒保存一次进度
    let lastSaveTime = 0
    audio.value.addEventListener('timeupdate', () => {
      if (currentTime.value - lastSaveTime > 30) {
        saveProgress()
        lastSaveTime = currentTime.value
      }
    })
  }

  // 播放单集
  function play(episode) {
    initAudio()

    // 切换单集
    if (!currentEpisode.value || currentEpisode.value.id !== episode.id) {
      currentEpisode.value = episode
      audio.value.src = episode.audio_url
      audio.value.load()

      // 恢复播放进度
      if (episode.play_position) {
        audio.value.currentTime = episode.play_position
      }
    }

    audio.value.play()
    isPlaying.value = true
  }

  // 暂停
  function pause() {
    if (audio.value) {
      audio.value.pause()
      isPlaying.value = false
    }
  }

  // 切换播放/暂停
  function toggle() {
    if (isPlaying.value) {
      pause()
    } else if (currentEpisode.value) {
      audio.value.play()
      isPlaying.value = true
    }
  }

  // 跳转
  function seek(time) {
    if (audio.value) {
      audio.value.currentTime = time
      currentTime.value = time
    }
  }

  // 快进/快退
  function skip(seconds) {
    const newTime = Math.max(0, Math.min(duration.value, currentTime.value + seconds))
    seek(newTime)
  }

  // 设置音量
  function setVolume(vol) {
    volume.value = vol
    if (audio.value) {
      audio.value.volume = vol
    }
  }

  // 设置播放速度
  function setPlaybackRate(rate) {
    playbackRate.value = rate
    if (audio.value) {
      audio.value.playbackRate = rate
    }
  }

  // 保存播放进度到服务器
  async function saveProgress(completed = false) {
    if (!currentEpisode.value) return

    try {
      await api.interactions.updatePlayProgress({
        episode_id: currentEpisode.value.id,
        position: Math.floor(currentTime.value),
        duration: Math.floor(duration.value)
      })
    } catch (error) {
      console.error('保存播放进度失败', error)
    }
  }

  // 格式化时间
  function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00'

    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)

    if (h > 0) {
      return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    }
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return {
    currentEpisode,
    isPlaying,
    currentTime,
    duration,
    volume,
    playbackRate,
    isLoading,
    progress,
    formattedCurrentTime,
    formattedDuration,
    play,
    pause,
    toggle,
    seek,
    skip,
    setVolume,
    setPlaybackRate
  }
})
