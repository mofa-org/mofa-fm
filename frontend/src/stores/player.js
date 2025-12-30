/**
 * 全局播放器 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const usePlayerStore = defineStore('player', () => {
  const currentEpisode = ref(null)
  const audio = ref(null)
  const playlist = ref([]) // 播放列表
  const currentIndex = ref(-1) // 当前播放索引

  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(parseFloat(localStorage.getItem('player_volume') || 0.8))
  const isMuted = ref(localStorage.getItem('player_muted') === 'true')
  const playbackRate = ref(1.0)
  const isLoading = ref(false)

  const progress = computed(() => {
    return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
  })

  const formattedCurrentTime = computed(() => formatTime(currentTime.value))
  const formattedDuration = computed(() => formatTime(duration.value))

  // 是否有上一首
  const hasPrevious = computed(() => currentIndex.value > 0)

  // 是否有下一首
  const hasNext = computed(() => currentIndex.value < playlist.value.length - 1)

  // 初始化音频
  function initAudio() {
    if (audio.value) return

    audio.value = new Audio()
    // 应用持久化的音量和静音状态
    updateAudioVolume()

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
      // 自动播放下一首
      if (hasNext.value) {
        playNext()
      }
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

  // 更新音频音量状态
  function updateAudioVolume() {
    if (!audio.value) return
    audio.value.volume = volume.value
    audio.value.muted = isMuted.value
  }

  // 播放单集
  function play(episode, episodeList = null) {
    initAudio()

    // 如果提供了播放列表，更新播放列表
    if (episodeList && Array.isArray(episodeList)) {
      playlist.value = episodeList
      currentIndex.value = episodeList.findIndex(e => e.id === episode.id)
    } else if (!currentEpisode.value || currentEpisode.value.id !== episode.id) {
      // 如果是单独播放，将当前单集作为播放列表
      playlist.value = [episode]
      currentIndex.value = 0
    }

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

  // 播放上一首
  function playPrevious() {
    if (!hasPrevious.value) return

    currentIndex.value--
    const previousEpisode = playlist.value[currentIndex.value]
    if (previousEpisode) {
      currentEpisode.value = previousEpisode
      audio.value.src = previousEpisode.audio_url
      audio.value.load()
      audio.value.play()
      isPlaying.value = true
    }
  }

  // 播放下一首
  function playNext() {
    if (!hasNext.value) return

    currentIndex.value++
    const nextEpisode = playlist.value[currentIndex.value]
    if (nextEpisode) {
      currentEpisode.value = nextEpisode
      audio.value.src = nextEpisode.audio_url
      audio.value.load()
      audio.value.play()
      isPlaying.value = true
    }
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
    localStorage.setItem('player_volume', vol)
    if (isMuted.value && vol > 0) {
      isMuted.value = false
      localStorage.setItem('player_muted', 'false')
    }
    updateAudioVolume()
  }

  // 切换静音
  function toggleMute() {
    isMuted.value = !isMuted.value
    localStorage.setItem('player_muted', isMuted.value)
    updateAudioVolume()
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
    playlist,
    currentIndex,
    isPlaying,
    currentTime,
    duration,
    volume,
    isMuted,
    playbackRate,
    isLoading,
    progress,
    formattedCurrentTime,
    formattedDuration,
    hasPrevious,
    hasNext,
    play,
    pause,
    toggle,
    seek,
    skip,
    setVolume,
    toggleMute,
    setPlaybackRate,
    playPrevious,
    playNext,
    removeFromQueue,
    clearQueue,
    reorderQueue,
    updateQueue
  }

  // 从队列移除
  function removeFromQueue(index) {
    if (index === currentIndex.value) {
      // 如果移除的是当前播放的，自动播放下一首或停止
      if (hasNext.value) {
        playNext()
        // 播放下一首后，索引会自动更新，但因为移除了一个元素，播放列表变更后的索引需要调整
        // 这里简化处理：playNext已经更新了索引和currentEpisode，我们只需要从列表移除旧的
        playlist.value.splice(index, 1)
        currentIndex.value-- // 因为移除了前面的（或当前的），索引减一
      } else if (hasPrevious.value) {
        playPrevious()
        playlist.value.splice(index, 1)
      } else {
        //只剩一首且被移除
        pause()
        currentEpisode.value = null
        audio.value.src = ''
        playlist.value = []
        currentIndex.value = -1
      }
    } else {
      playlist.value.splice(index, 1)
      if (index < currentIndex.value) {
        currentIndex.value--
      }
    }
  }

  // 清空队列
  function clearQueue() {
    // 保留当前播放的
    if (currentEpisode.value) {
      playlist.value = [currentEpisode.value]
      currentIndex.value = 0
    } else {
      playlist.value = []
      currentIndex.value = -1
    }
  }

  // 重排队列（简单的交换位置）
  function reorderQueue(fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= playlist.value.length || toIndex >= playlist.value.length) return
    
    // 如果移动的是当前播放的，更新索引
    if (currentIndex.value === fromIndex) {
      currentIndex.value = toIndex
    } else if (currentIndex.value === toIndex) {
      // 目标位置是当前播放的，现在的当前播放的会被挤走
      // 这种情况比较复杂，简单处理：如果是当播放位置受影响
      if (fromIndex < currentIndex.value && toIndex >= currentIndex.value) {
        currentIndex.value--
      } else if (fromIndex > currentIndex.value && toIndex <= currentIndex.value) {
        currentIndex.value++
      }
    } else {
      // 移动范围跨越了当前播放的
        if (fromIndex < currentIndex.value && toIndex >= currentIndex.value) {
        currentIndex.value--
      } else if (fromIndex > currentIndex.value && toIndex <= currentIndex.value) {
        currentIndex.value++
      }
    }

    const item = playlist.value.splice(fromIndex, 1)[0]
    playlist.value.splice(toIndex, 0, item)
  }

  // 直接更新队列（用于拖拽排序库）
  function updateQueue(newPlaylist) {
    // 找到当前播放的单集在新列表中的位置
    const currentId = currentEpisode.value?.id
    playlist.value = newPlaylist
    if (currentId) {
      currentIndex.value = newPlaylist.findIndex(e => e.id === currentId)
    }
  }
})
