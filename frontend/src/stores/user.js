import { defineStore } from 'pinia'
import { getMe } from '../api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    info: null, // { id, username, nickname, shop_name, phone }
  }),
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('token', token)
    },
    logout() {
      this.token = ''
      this.info = null
      localStorage.removeItem('token')
    },
    async fetchInfo() {
      if (!this.token) return
      this.info = await getMe()
    },
  },
})
