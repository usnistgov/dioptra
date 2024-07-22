import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
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
      path: '/entrypoints/:id',
      component: () => import('../views/CreateEntryPoint.vue')
    },
    {
      path: '/plugins',
      component: () => import('../views/PluginsView.vue')
    },
    {
      path: '/plugins/:id',
      component: () => import('../views/EditPluginsView.vue')
    },
    {
      path: '/oldplugins/:id',
      component: () => import('../views/OldEditPluginsView.vue')
    },
    {
      path: '/plugins/:id/files',
      component: () => import('../views/PluginFiles.vue')
    },
    {
      path: '/plugins/:id/files/:fileId',
      component: () => import('../views/CreatePluginFile.vue')
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
      path: '/jobs',
      component: () => import('../views/AllJobsView.vue')
    },
    {
      path: '/experiments/:id/jobs',
      component: () => import('../views/JobsView.vue')
    },
    {
      path: '/experiments/:id/jobs/:jobId',
      component: () => import('../views/CreateJob.vue')
    },
    {
      path: '/experiments/:id',
      component: () => import('../views/CreateExperiment.vue')
    },
    {
      path: '/groups',
      component: () => import('../views/GroupsView.vue')
    },
    {
      path: '/groups/admin',
      component: () => import('../views/GroupsAdminView.vue')
    },
    {
      path: '/tags',
      component: () => import('../views/TagsView.vue')
    },
    {
      path: '/pluginParams',
      component: () => import('../views/PluginParamsView.vue')
    },
    {
      path: '/models',
      component: () => import('../views/ModelsView.vue')
    },
    {
      path: '/artifacts',
      component: () => import('../views/ArtifactsView.vue')
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
