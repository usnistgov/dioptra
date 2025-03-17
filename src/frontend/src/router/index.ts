import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: HomeView,
      name: 'home'
    },
    {
      path: '/entrypoints',
      component: () => import('../views/EntryPointsView.vue'),
      name: 'entrypoints'
    },
    {
      path: '/entrypoints/:id',
      component: () => import('../views/CreateEntryPoint.vue'),
    },
    {
      path: '/plugins',
      component: () => import('../views/PluginsView.vue'),
      name: 'plugins'
    },
    {
      path: '/plugins/:id/files',
      component: () => import('../views/PluginFiles.vue'),
      name: 'pluginFiles'
    },
    {
      path: '/plugins/:id/files/:fileId',
      component: () => import('../views/CreatePluginFile.vue')
    },
    {
      path: '/queues',
      component: () => import('../views/QueuesView.vue'),
      name: 'queues'
    },
    {
      path: '/experiments',
      component: () => import('../views/ExperimentsView.vue'),
      name: 'experiments'
    },
    {
      path: '/jobs',
      component: () => import('../views/JobsView.vue'),
      name: 'allJobs'
    },
    {
      path: '/experiments/:id/jobs',
      component: () => import('../views/JobsView.vue'),
      name: 'experimentJobs'
    },
    {
      path: '/experiments/:id/jobs/:jobId',
      component: () => import('../views/CreateJob.vue')
    },
    {
      path: '/jobs/new',
      component: () => import('../views/CreateJob.vue')
    },
    {
      path: '/experiments/:id',
      component: () => import('../views/CreateExperiment.vue'),
      meta: { type: 'experiments' }
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
      component: () => import('../views/TagsView.vue'),
      name: 'tags'
    },
    {
      path: '/pluginParams',
      component: () => import('../views/PluginParamsView.vue'),
      name: 'pluginParams'
    },
    {
      path: '/models',
      component: () => import('../views/ModelsView.vue'),
      name: 'models'
    },
    {
      path: '/artifacts',
      component: () => import('../views/ArtifactsView.vue'),
      name: 'artifacts'
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
