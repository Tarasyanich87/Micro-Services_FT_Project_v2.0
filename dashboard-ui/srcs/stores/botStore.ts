import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './authStore'

const API_URL = '/api/v1/bots'

export const useBotStore = defineStore('bots', {
  state: () => ({
    bots: [],
    statuses: {},
    loading: false
  }),
  actions: {
    async fetchBots() {
      this.loading = true
      const authStore = useAuthStore()
      try {
        const response = await axios.get(API_URL, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        this.bots = response.data
      } catch (error) {
        console.error('Failed to fetch bots:', error)
      } finally {
        this.loading = false
      }
    },
    async fetchBotStatuses() {
      const authStore = useAuthStore()
      try {
        const response = await axios.get(`${API_URL}/status/all`, {
          headers: { Authorization: `Bearer ${authStore.token}` }
        })
        this.statuses = response.data
      } catch (error) {
        console.error('Failed to fetch bot statuses:', error)
      }
    }
  }
})
