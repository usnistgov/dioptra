import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      name: 'home',
      path: '/',
      component: HomeView
    },
    {
      name: 'entrypoints',
      path: '/entrypoints',
      component: () => import('../views/EntryPointsView.vue')
    },
    {
      name: 'queues',
      path: '/queues',
      component: () => import('../views/QueuesView.vue')
    },
    {
      name: 'login',
      path: '/login',
      component: () => import('../views/BasicLoginView.vue')
    },
    {
      name: 'register',
      path: '/register',
      component: () => import('@/components/RegisterForm.vue')
    }
  ]
})

export default router
