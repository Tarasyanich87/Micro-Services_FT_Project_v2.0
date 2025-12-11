import { createApp } from 'vue'
import router from './router'
import App from './App.vue'

// Simple CSS for testing
import './style.css'

const app = createApp(App)

app.use(router)

app.mount('#app')

console.log('Vue app initialized successfully')
