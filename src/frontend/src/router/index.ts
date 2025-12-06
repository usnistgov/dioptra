import { createRouter, createWebHistory, START_LOCATION } from 'vue-router'
import { useLoginStore } from '@/stores/LoginStore'
import HomeView from '../views/HomeView.vue'
import * as api from '@/services/dataApi'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: HomeView,
      name: 'home'
    },
    {
      path: '/experiments',
      children: [
        {
          path: '',
          component: () => import('../views/ExperimentsView.vue'),
          meta: { type: 'experiments' },
          name: 'experiments',
        },
        {
          path: '/experiments/new',
          component: () => import('../views/CreateExperiment.vue'),
          meta: { type: 'experiments' }
        },
        {
          path: '/experiments/:id',
          component: () => import('../views/EditExperiment.vue'),
          meta: { type: 'experiments' },
          name: 'experimentJobs'
        },
        {
          path: '/experiments/:id/jobs/:jobId',
          component: () => import('../views/CreateJob.vue'),
          name: 'createExperimentJob'
        },
      ]
    },
    {
      path: '/entrypoints',
      children: [
        {
          path: '',
          component: () => import('../views/EntryPointsView.vue'),
          name: 'entrypoints',
        },
        {
          path: '/entrypoints/:id',
          component: () => import('../views/CreateEntryPoint.vue'),
          meta: { type: 'entrypoints' }
        },
      ]
    },
    {
      path: '/plugins',
      children: [
        {
          path: '',
          component: () => import('../views/PluginsView.vue'),
          name: 'plugins',
        },
        {
          path: '/plugins/new',
          component: () => import('../views/CreatePluginView.vue'),
          meta: { type: 'plugins' }
        },
        {
          path: '/plugins/:id',
          component: () => import('../views/EditPluginView.vue'),
          name: 'editPlugin',
        },
        {
          path: '/plugins/:id/files/:fileId',
          component: () => import('../views/CreatePluginFile.vue'),
          name: 'pluginFile'
        },
      ]
    },
    {
      path: '/queues',
      children: [
        {
          path: '',
          component: () => import('../views/QueuesView.vue'),
          name: 'queues',
        },
        {
          path: '/queues/:id/:draftType/:newResourceDraft?',
          component: () => import('../views/QueuesFormDraftView.vue'),
          meta: { type: 'queues' }
        },
        {
          path: '/queues/:id',
          component: () => import('../views/QueuesFormView.vue'),
          meta: { type: 'queues' }
        },
      ]
    },
    {
      path: '/jobs',
      children: [
        {
          path: '',
          component: () => import('../views/JobsView.vue'),
          name: 'allJobs',
        },
        {
          path: '/jobs/new',
          component: () => import('../views/CreateJob.vue')
        },
        {
          path: '/jobs/:id',
          component: () => import('../views/JobDashboardView.vue')
        },
      ]
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
      children: [
        {
          path: '',
          component: () => import('../views/PluginParamsView.vue'),
          name: 'pluginParams',
        },
        {
          path: '/pluginParams/:id',
          component: () => import('../views/PluginParamForm.vue'),
          name: 'editPluginParam',
        }
      ]
    },
    {
      path: '/models',
      component: () => import('../views/ModelsView.vue'),
      name: 'models'
    },
    {
      path: '/artifacts',
      children: [
        {
          path: '/artifacts',
          component: () => import('../views/ArtifactsView.vue'),
          name: 'artifacts',
          meta: { type: 'artifacts' }
        },
        {
          path: '/artifacts/:id',
          component: () => import('../views/EditArtifactView.vue'),
          meta: { type: 'artifacts' }
        },
      ]
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


router.beforeEach(async (to, from) => {
  const store = useLoginStore()

  // on every route change, close snapshot drawer if open
  if(store.showRightDrawer) {
    store.showRightDrawer = false
    store.selectedSnapshot = null
  }

  // check login status on mounted and reloads
  if(from === START_LOCATION) {
    await callGetLoginStatus()
  }

  const isAuthRoute = to.path === '/login' || to.path === '/register'
  const isLoggedIn = !!store.loggedInUser

  // redirect to login if logged out
  if(!isLoggedIn && !isAuthRoute) {
    return '/login'
  }

  // allow navigation
  return true
})

async function callGetLoginStatus() {
  const store = useLoginStore()
  try {
    const res = await api.getLoginStatus()
    store.loggedInUser = res.data
    store.groups = res.data.groups
  } catch (err) {
    store.loggedInUser = ''
  }
}


export default router
