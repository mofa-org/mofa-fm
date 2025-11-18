/**
 * 播客数据 Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const usePodcastsStore = defineStore('podcasts', () => {
  const categories = ref([])
  const tags = ref([])
  const featuredShows = ref([])

  // 获取分类
  async function fetchCategories() {
    if (categories.value.length > 0) return categories.value

    const data = await api.podcasts.getCategories()
    categories.value = data
    return data
  }

  // 获取标签
  async function fetchTags() {
    const data = await api.podcasts.getTags()
    tags.value = data
    return data
  }

  // 获取精选节目
  async function fetchFeaturedShows() {
    const data = await api.podcasts.getShows({ is_featured: true, page_size: 6 })
    featuredShows.value = data.results || data
    return data
  }

  return {
    categories,
    tags,
    featuredShows,
    fetchCategories,
    fetchTags,
    fetchFeaturedShows
  }
})
