<template>
  <div class="login-container">
    <div class="login-card">
      <h1>Login</h1>
      <form @submit.prevent="handleLogin">
        <div class="p-field">
          <label for="username">Username</label>
          <InputText id="username" v-model="username" />
        </div>
        <div class="p-field">
          <label for="password">Password</label>
          <InputText id="password" type="password" v-model="password" />
        </div>
        <Button type="submit" label="Login" />
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

const username = ref('')
const password = ref('')
const authStore = useAuthStore()
const router = useRouter()

const handleLogin = async () => {
  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch (error) {
    console.error('Login failed:', error)
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}
.login-card {
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  border-radius: 6px;
}
</style>
