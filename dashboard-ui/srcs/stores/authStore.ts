import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = '/api/v1/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null,
    isAuthenticated: !!localStorage.getItem('token')
  }),
  actions: {
    async login(username, password) {
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)

      const response = await axios.post(`${API_URL}/login`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })

      this.token = response.data.access_token
      this.isAuthenticated = true
      localStorage.setItem('token', this.token)

      // Fetch user info
      await this.fetchUser()
    },
    logout() {
      this.token = ''
      this.user = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
    },
    async fetchUser() {
      if (this.token) {
        const response = await axios.get('/api/v1/users/me', {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        this.user = response.data
      }
    }
  }
})
