import { createRouter, createWebHistory, START_LOCATION } from 'vue-router'
import { useLoginStore } from '@/stores/LoginStore'
import HomeView from '../views/HomeView.vue'
import * as api from '@/services/dataApi'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    // always scroll to top
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      component: HomeView,
      name: 'home'
    },
    {
      path: '/experiments',
      meta: { type: 'experiments' },
      children: [
        {
          path: '',
          component: () => import('../views/ExperimentsView.vue'),
          name: 'experiments',
        },
        {
          path: '/experiments/new',
          component: () => import('../views/CreateExperiment.vue'),
        },
        {
          path: '/experiments/:id',
          component: () => import('../views/EditExperiment.vue'),
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
      meta: { type: 'entrypoints' },
      children: [
        {
          path: '',
          component: () => import('../views/EntryPointsView.vue'),
          name: 'entrypoints',
        },
        {
          path: '/entrypoints/:id',
          component: () => import('../views/CreateEntryPoint.vue'),
        },
      ]
    },
    {
      path: '/plugins',
      meta: { type: 'plugins' },
      children: [
        {
          path: '',
          component: () => import('../views/PluginsView.vue'),
          name: 'plugins',
        },
        {
          path: '/plugins/new',
          component: () => import('../views/CreatePluginView.vue'),
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
      meta: { type: 'queues' },
      children: [
        {
          path: '',
          component: () => import('../views/QueuesView.vue'),
          name: 'queues',
        },
        {
          path: '/queues/:id/:draftType/:newResourceDraft?',
          component: () => import('../views/QueuesFormDraftView.vue'),
        },
        {
          path: '/queues/:id',
          component: () => import('../views/QueuesFormView.vue'),
        },
      ]
    },
    {
      path: '/jobs',
      meta: { type: 'jobs' },
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
          component: () => import('../views/JobDashboardView.vue'),
          name: 'jobDashboard'
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
      meta: { type: 'pluginParams' },
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
      meta: { type: 'artifacts' },
      children: [
        {
          path: '/artifacts',
          component: () => import('../views/ArtifactsView.vue'),
          name: 'artifacts',
        },
        {
          path: '/artifacts/:id',
          component: () => import('../views/EditArtifactView.vue'),
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
    store.initialPage = true
    await callGetLoginStatus()
  } else {
    store.initialPage = false
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

router.afterEach((to, from) => {
  // remember pagination when clicking into a resource then going back to the table
  const backButton = window.event?.type === 'popstate'
  const backToSameType = to.meta?.type === from.meta?.type
  const jobBackToExperiment = to.name === 'experimentJobs' && from.name === 'jobDashboard'
  const viaBadgeLink = window.history.state?.viaBadgeLink === true
  if (viaBadgeLink) {
    to.meta.viaBadgeLink = true
  }
  if(backButton && (backToSameType || jobBackToExperiment || from.meta?.viaBadgeLink)) {
    to.meta.backButton = true
  }

  // ensure only to and from pagination settings are stored
  const store = useLoginStore()
  const keep = new Set<string>([to.path, from.path])
  Object.keys(store.tablePaginationCache).forEach((k) => {
    if (!keep.has(k)) {
      delete (store.tablePaginationCache as any)[k]
    }
  })
})


export default router
