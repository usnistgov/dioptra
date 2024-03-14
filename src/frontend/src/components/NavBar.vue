<template>
  <q-toolbar class="bg-primary text-white">
    <nav>
      <q-tabs shrink no-caps class="header">
        <q-route-tab label="Home" to="/" />
        <q-route-tab label="Entry-Points" to="/entrypoints" />
        <q-route-tab label="Task-Plugins" to="/" />
        <q-route-tab label="Queues" to="/queues" />
        <q-route-tab label="Experiments" to="/experiments" />
        <q-route-tab label="Jobs" to="/" />
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
      <q-btn v-else color="primary" icon-right="person" :label="store.loggedInUser" to="/login" dense />
    </q-tabs>
  </q-toolbar>
</template>

<script setup>
  import { useQuasar } from 'quasar'
  import { computed } from 'vue'
  import { useRouter, START_LOCATION } from 'vue-router'
  import { useLoginStore } from '@/stores/LoginStore'
  import { storeToRefs } from 'pinia'
  import * as api from '@/services/loginApi'

  const router = useRouter()

  const store = useLoginStore()
  const { loggedInUser } = storeToRefs(store);

  const $q = useQuasar()

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
      loggedInUser.value = res.data.username
    } catch(err) {
      loggedInUser.value = ''
    }
  }


</script>
