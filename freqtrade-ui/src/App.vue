<template>
  <div>
    <header class="navbar">
      <nav>
        <router-link to="/">Home</router-link>
        <router-link to="/bots">Bots</router-link>
        <router-link to="/strategies">Strategies</router-link>
        <router-link to="/analytics">Analytics</router-link>
        <router-link to="/audit">Audit</router-link>
      </nav>
    </header>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  document.title = 'Freqtrade UI'
  console.log('App mounted, token:', authStore.token)
})
</script>

<style scoped>
.navbar {
  background-color: #333;
  padding: 1rem;
  color: white;
}
.navbar nav {
  display: flex;
  gap: 1rem;
}
.navbar a {
  color: white;
  text-decoration: none;
}
.navbar a:hover {
  text-decoration: underline;
}
.content {
  padding: 1rem;
}
</style>
