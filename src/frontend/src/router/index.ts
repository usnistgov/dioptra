import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: HomeView
    },
    {
      path: '/entrypoints',
      component: () => import('../views/EntryPointsView.vue')
    },
    {
      path: '/queues',
      component: () => import('../views/QueuesView.vue')
    },
    {
      path: '/experiments',
      component: () => import('../views/ExperimentsView.vue')
    },
    {
      path: '/experiments/create',
      component: () => import('../views/CreateExperiment.vue')
    },
    {
      path: '/login',
      component: () => import('../views/BasicLoginView.vue')
    },
    {
      path: '/register',
      component: () => import('@/components/RegisterForm.vue')
    }
  ]
})

export default router
