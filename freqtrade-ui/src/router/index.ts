import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginDashboard.vue'),
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bots',
    name: 'BotManagement',
    component: () => import('@/views/BotManagementDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/strategies',
    name: 'Strategies',
    component: () => import('@/views/StrategiesDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('@/views/AnalyticsDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/freqai-lab',
    name: 'FreqAILab',
    component: () => import('@/views/FreqAILabDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/data',
    name: 'DataManagement',
    component: () => import('@/views/DataManagementDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/hyperopt',
    name: 'Hyperopt',
    component: () => import('@/views/HyperoptDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/monitoring',
    name: 'SystemMonitoring',
    component: () => import('@/views/MonitoringDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/audit',
    name: 'AuditLog',
    component: () => import('@/views/AuditDashboard.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  // Check token in localStorage directly
  const token = localStorage.getItem('auth') ? JSON.parse(localStorage.getItem('auth') || '{}').token : null
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
