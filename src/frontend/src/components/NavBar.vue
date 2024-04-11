<template>
  <q-toolbar class="bg-primary text-white">
    <q-btn
      v-if="isMobile"
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
          <q-item clickable v-close-popup to="/entryPoints">
            <q-item-section>Entry-Points</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/taskPlugins">
            <q-item-section>Task-Plugins</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/queues">
            <q-item-section>Queues</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/experiments">
            <q-item-section>Experiments</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/jobs">
            <q-item-section>Jobs</q-item-section>
          </q-item>
          <q-item clickable v-close-popup to="/groups">
            <q-item-section>Groups</q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-btn>
    <nav v-if="!isMobile">
      <q-tabs shrink no-caps class="header">
        <q-route-tab label="Home" to="/" />
        <q-route-tab label="Entry-Points" to="/entrypoints" />
        <q-route-tab label="Task-Plugins" to="/" />
        <q-route-tab label="Queues" to="/queues" />
        <q-route-tab label="Experiments" to="/experiments" />
        <q-route-tab label="Jobs" to="/" />
        <q-route-tab label="Groups" to="/groups" />
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
      @click="$q.dark.toggle()"
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
    <q-separator vertical inset color="white" />
    <q-tabs shrink no-caps class="header q-ml-sm">
      <q-route-tab 
        v-if="!store.loggedInUser"
        :label="getLabel()" to="/login"
      />
      <div v-else >
        <q-btn color="primary" icon="person" :label="isMobile ? '' : store.loggedInUser" to="/login" dense class="q-mr-sm" />
        <q-btn-dropdown style="background-color: #CF5C36;" icon="groups" :label="isMobile ? '' : store.loggedInGroup" dense class="q-pl-md">
          <q-list>
            <q-item 
              v-for="(group, i) in store.groups" 
              :key="i" 
              clickable 
              v-close-popup 
              @click="store.loggedInGroup = group.name" 
              :active="group === store.loggedInGroup"
              active-class="bg-blue-3 text-bold"
            >
              <q-item-section>
                <q-item-label>{{ group.name }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </div>
    </q-tabs>
  </q-toolbar>
</template>

<script setup>
  import { useQuasar } from 'quasar'
  import { computed, inject, ref } from 'vue'
  import { useRouter, START_LOCATION } from 'vue-router'
  import { useLoginStore } from '@/stores/LoginStore'
  import { storeToRefs } from 'pinia'
  import * as api from '@/services/loginApi'

  const router = useRouter()

  const store = useLoginStore()
  // const { loggedInUser } = storeToRefs(store);

  const $q = useQuasar()

  const isMobile = inject('isMobile')

  const darkMode = computed(() => {
    return $q.dark.mode
  })


  function getIcon() {
    if(darkMode.value === 'auto') return 'sym_o_routine'
    if(darkMode.value) return 'sym_o_dark_mode'
    else return 'sym_o_sunny'
  }

  function getLabel() {
    if(!store.loggedInUser) return 'Sign In'
    else return `${store.loggedInUser}`
  }

  // check login status on mounted and reloads
  router.beforeEach((to, from) => {
    if (from === START_LOCATION) {
      callGetLoginStatus()
    }
  })

  async function callGetLoginStatus() {
    try {
      const res = await api.getLoginStatus()
      store.loggedInUser = res.data.username
    } catch(err) {
      store.loggedInUser = ''
    }
  }




</script>
