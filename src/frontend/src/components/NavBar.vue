<template>
  <q-toolbar class="bg-primary text-white">
    <q-btn
      v-if="store.loggedInUser"
      class="lt-lg"
      icon="menu"
      flat
      :ripple="false"
    >
      <span class="sr-only">Navigation Menu</span>
      <q-menu class="text-h6">
        <q-list style="min-width: 150px">
          <q-item clickable v-close-popup to="/">
            <q-item-section>Home</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/experiments">
            <q-item-section>Experiments</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/jobs">
            <q-item-section>Jobs</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/artifacts">
            <q-item-section>Artifacts</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/entryPoints">
            <q-item-section>Entrypoints</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/plugins">
            <q-item-section>Plugins</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/pluginParams">
            <q-item-section>Plugin Parameters</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/queues">
            <q-item-section>Queues</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/tags">
            <q-item-section>Tags</q-item-section>
          </q-item>
          <!-- <q-item clickable v-close-popup to="/models">
            <q-item-section>Models</q-item-section>
          </q-item> -->
          <q-item clickable v-close-popup to="/groups">
            <q-item-section>Groups</q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>
    <nav v-if="store.loggedInUser" class="gt-md">
      <q-tabs no-caps>
        <q-route-tab label="Home" to="/" />
        <q-route-tab label="Experiments" to="/experiments" />
        <q-route-tab label="Jobs" to="/jobs" />
        <q-route-tab label="Artifacts" to="/artifacts" />
        <q-route-tab label="Entrypoints" to="/entrypoints" />
        <q-route-tab label="Plugins" to="/plugins" />
        <q-route-tab label="Plugin Parameters" to="/pluginParams" />
        <q-route-tab label="Queues" to="/queues" />
        <q-route-tab label="Tags" to="/tags" />
        <!-- <q-route-tab label="Models" to="/models" /> -->
      </q-tabs>
    </nav>

    <q-space />
    <a href="https://github.com/usnistgov/dioptra" target="_blank" class="q-mr-md text-white">
      <q-icon name="fa-brands fa-github" size="sm" />
      <span class="sr-only">Source Repository</span>
      <q-tooltip>
        Source Repository
      </q-tooltip>
    </a>
    <q-icon
      v-if="!isMobile" 
      name="sym_o_fullscreen" 
      size="sm" 
      @click="$q.fullscreen.toggle()"
      @keyup.enter="$q.fullscreen.toggle()"
      class="q-mr-md" 
      style="cursor: pointer" 
      tabindex="0" 
      role="button"
      aria-hidden="false"
    >
      <q-tooltip>
        Toggle Fullscreen Mode
      </q-tooltip>
    </q-icon>
    <q-icon 
      :name="getIcon()" 
      size="sm" 
      @click="$q.dark.toggle(); setLightDarkPreference()"
      @keyup.enter="$q.dark.toggle()"
      class="q-mr-lg" 
      style="cursor: pointer"
      tabindex="0" 
      role="button"
      aria-hidden="false"
      aria-label="Toggle light/dark mode"
    >
      <q-tooltip>
        Toggle Light/Dark Mode
      </q-tooltip>
    </q-icon> 
    <q-icon
      name="upload"
      size="sm"
      @click="showImportDialog = true"
      @keyup.enter="showImportDialog = true"
      v-if="store.loggedInUser"
      class="q-mr-md"
      style="cursor: pointer"
      tabindex="0"
      role="button"
      aria-hidden="false"
    >
      <q-tooltip>
        Import resources
      </q-tooltip>
    </q-icon>
    <q-separator vertical inset color="white" />
    <q-tabs shrink no-caps class="header q-ml-sm">
      <q-route-tab 
        v-if="!store.loggedInUser"
        :label="getLabel()" to="/login"
      />
      <div v-else class="row">
        <q-tabs no-caps inline-label>
          <q-route-tab class="gt-md" label="Groups" to="/groups" />
          <q-route-tab :label="isMobile ? '' : store.loggedInUser.username" to="/login" icon="person" />
          <q-btn-dropdown style="background-color: #CF5C36;" icon="groups" :label="isMobile ? '' : store.loggedInGroup.name" dense class="q-pl-md q-my-xs">
            <q-list>
              <q-item 
                v-for="(group, i) in store.groups" 
                :key="i" 
                clickable 
                v-close-popup 
                @click="console.log('Selected group = ', group)" 
                :active="group.id === store.loggedInGroup.id"
                active-class="bg-blue-3 text-bold"
              >
                <q-item-section>
                  <q-item-label>{{ group.name }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </q-tabs>
      </div>
    </q-tabs>
  </q-toolbar>
  <ImportResourcesDialog v-model="showImportDialog" />
</template>

<script setup>
  import { useQuasar } from 'quasar'
  import { computed, inject, ref } from 'vue'
  import { useRouter, START_LOCATION } from 'vue-router'
  import { useLoginStore } from '@/stores/LoginStore'
  import * as api from '@/services/dataApi'

  import ImportResourcesDialog from '../dialogs/ImportResourcesDialog.vue';
  const showImportDialog = defineModel()

  const router = useRouter()

  const store = useLoginStore()
  // const { loggedInUser } = storeToRefs(store);

  const $q = useQuasar()

  const isMobile = inject('isMobile')

  function getIcon() {
    if($q.dark.mode === 'auto') return 'sym_o_routine'
    if($q.dark.mode) return 'sym_o_dark_mode'
    else return 'sym_o_sunny'
  }

  function setLightDarkPreference(){
    localStorage.setItem('darkMode', $q.dark.mode)
  }

  function getLabel() {
    if(!store.loggedInUser) return 'Sign In'
    else return `${store.loggedInUser}`
  }

  router.beforeEach(async(to, from) => {
    // check login status on mounted and reloads
    if (from === START_LOCATION) {
      await callGetLoginStatus()
    }
    // redirect to login if logged out
    if(!store.loggedInUser && to.path !== '/login' && to.path !== '/register') {
      router.push('/login')
    }
  })

  async function callGetLoginStatus() {
    try {
      const res = await api.getLoginStatus()
      store.loggedInUser = res.data
      store.groups = res.data.groups
    } catch(err) {
      store.loggedInUser = ''
    }
  }

</script>
