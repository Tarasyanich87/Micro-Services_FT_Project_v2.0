<template>
  <div class="dashboard-container">
    <div class="header">
      <h1>🚀 Freqtrade Multi-Bot Dashboard</h1>
<<<<<<< HEAD
      <div>
        <router-link to="/monitoring">
          <Button label="Monitoring" class="p-button-secondary" />
        </router-link>
        <router-link to="/strategies">
          <Button label="Strategies" class="p-button-secondary" />
        </router-link>
        <router-link to="/analytics">
          <Button label="Analytics" class="p-button-secondary" />
        </router-link>
        <Button icon="pi pi-sign-out" label="Logout" @click="handleLogout" />
      </div>
=======
      <Button icon="pi pi-sign-out" label="Logout" @click="handleLogout" />
>>>>>>> origin/refactor/full-system-rewrite
    </div>
    <div v-if="botStore.loading">Loading...</div>
    <div v-else class="bots-grid">
      <div v-for="bot in botStore.bots" :key="bot.id" class="bot-card" :class="bot.status">
        <div class="service-icon">📈</div>
        <div class="service-title">{{ bot.name }}</div>
        <div class="service-description">{{ bot.description }}</div>
        <a :href="bot.ui_url || '#'" class="service-link" target="_blank">Open FreqUI</a>
        <div class="status" :class="bot.status">{{ bot.status }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
<<<<<<< HEAD
import { useAuthStore } from '../stores/authStore'
import { useBotStore } from '../stores/botStore'
=======
import { useAuthStore } from '@/stores/authStore'
import { useBotStore } from '@/stores/botStore'
>>>>>>> origin/refactor/full-system-rewrite
import { useRouter } from 'vue-router'
import Button from 'primevue/button'

const authStore = useAuthStore()
const botStore = useBotStore()
const router = useRouter()

onMounted(() => {
  botStore.fetchBots()
<<<<<<< HEAD
=======
  // We can also fetch statuses periodically
  // setInterval(() => botStore.fetchBotStatuses(), 5000)
>>>>>>> origin/refactor/full-system-rewrite
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
<<<<<<< HEAD
/* Styles from old dashboard.html */
=======
/* Styles adapted from the old dashboard.html */
>>>>>>> origin/refactor/full-system-rewrite
.dashboard-container {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.bots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}
.bot-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 25px;
  text-align: center;
  border: 1px solid #e9ecef;
}
.bot-card.running { border-left: 5px solid #28a745; }
.bot-card.stopped { border-left: 5px solid #dc3545; }
.service-icon { font-size: 3em; margin-bottom: 15px; }
.service-title { font-size: 1.4em; font-weight: 600; margin: 10px 0; }
.service-description { color: #666; margin-bottom: 20px; }
.service-link {
  display: inline-block;
  background: #007bff;
  color: white;
  padding: 12px 25px;
  text-decoration: none;
  border-radius: 5px;
}
.status {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8em;
  font-weight: 600;
  text-transform: uppercase;
  margin-top: 10px;
}
.status.running { background: #d4edda; color: #155724; }
.status.stopped { background: #f8d7da; color: #721c24; }
</style>
