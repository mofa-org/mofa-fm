import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Discover from '@/views/Discover.vue'
import { createTestingPinia } from '@pinia/testing'
import { usePodcastsStore } from '@/stores/podcasts'
import api from '@/api'

// Mock API
vi.mock('@/api', () => ({
  default: {
    podcasts: {
      getShows: vi.fn(),
      getCategories: vi.fn() // Although fetchCategories comes from store, we mock api just in case
    }
  }
}))

describe('Discover.vue', () => {
  let wrapper
  let podcastsStore

  beforeEach(async () => {
    // Reset mocks
    vi.clearAllMocks()

    // Mock store implementation
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      stubActions: false // needed to trigger store actions if real impl is wanted (or mock it)
    })
    
    // We want to mock fetchCategories action in the store
    const store = usePodcastsStore()
    store.fetchCategories = vi.fn().mockResolvedValue([
      { id: 1, name: 'Tech' },
      { id: 2, name: 'Art' },
      { id: 3, name: 'Science' }
    ])

    // Mock api response for shows
    api.podcasts.getShows.mockResolvedValue([
        { id: 101, title: 'Tech Talk' }
    ])

    wrapper = mount(Discover, {
      global: {
        plugins: [pinia],
        stubs: {
          ShowCard: true, // Stub child components
          'el-empty': true
        },
        directives: {
          loading: () => {} // Stub v-loading directive properly
        }
      }
    })
    
    // Construct component
    await flushPromises()
  })

  it('renders categories', async () => {
    const buttons = wrapper.findAll('.category-btn')
    expect(buttons.length).toBe(3)
    expect(buttons[0].text()).toBe('Tech')
  })

  it('filters shows when category is clicked', async () => {
    // Initial call
    expect(api.podcasts.getShows).toHaveBeenCalledWith({})

    // Click 'Art' category (id: 2)
    const artBtn = wrapper.findAll('.category-btn')[1]
    await artBtn.trigger('click')

    // Expect 'selectedCategory' to update and fetchShows to be called with category id
    expect(wrapper.vm.selectedCategory).toBe(2)
    expect(api.podcasts.getShows).toHaveBeenCalledWith({ category: 2 })
  })

  it('fetches shows without category when category desisted (optional logic) or initial load', async () => {
    // This test just confirms the initial load behavior mentioned above
    expect(api.podcasts.getShows).toHaveBeenCalledTimes(1) // from mount
    expect(api.podcasts.getShows).toHaveBeenCalledWith({})
  })
})
