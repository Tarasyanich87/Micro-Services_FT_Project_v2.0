<template>
  <div class="login-dashboard">
    <div class="login-container">
      <div class="login-header">
        <h1>🔐 Freqtrade</h1>
        <p>Вход в систему управления ботами</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Имя пользователя</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            :disabled="loading"
            placeholder="Введите имя пользователя"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            :disabled="loading"
            placeholder="Введите пароль"
          />
        </div>

        <button
          type="submit"
          class="login-btn"
          :disabled="loading || !form.username || !form.password"
        >
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'Вход...' : '🚀 Войти' }}
        </button>
      </form>

      <div v-if="error" class="error-message">
        <p>❌ {{ error }}</p>
      </div>

      <div class="login-footer">
        <p>Demo credentials: <code>analytics_user</code> / <code>testpass123</code></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

// Reactive data
const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

// Composables
const router = useRouter()

// Methods
const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    error.value = 'Заполните все поля'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/v1/auth/login/json', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: form.value.username,
        password: form.value.password
      })
    })

    if (response.ok) {
      const data = await response.json()
      // Store token in localStorage
      localStorage.setItem('auth', JSON.stringify({
        token: data.access_token,
        user: data.user
      }))
      router.push('/')
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || 'Ошибка входа'
    }
  } catch (err: any) {
    console.error('Login error:', err)
    error.value = 'Ошибка подключения к серверу'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-container {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 3rem;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 2.5rem;
}

.login-header p {
  margin: 0;
  color: #666;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-group input {
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.login-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #f5c6cb;
}

.error-message p {
  margin: 0;
  font-weight: 500;
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
  color: #666;
  font-size: 0.9rem;
}

.login-footer code {
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
}

@media (max-width: 480px) {
  .login-dashboard {
    padding: 1rem;
  }

  .login-container {
    padding: 2rem;
  }

  .login-header h1 {
    font-size: 2rem;
  }
}
</style>

<style scoped>
.login-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-container {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 3rem;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 2.5rem;
}

.login-header p {
  margin: 0;
  color: #666;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-group input {
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.login-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #f5c6cb;
}

.error-message p {
  margin: 0;
  font-weight: 500;
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
  color: #666;
  font-size: 0.9rem;
}

.login-footer code {
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
}

@media (max-width: 480px) {
  .login-dashboard {
    padding: 1rem;
  }

  .login-container {
    padding: 2rem;
  }

  .login-header h1 {
    font-size: 2rem;
  }
}
</style>