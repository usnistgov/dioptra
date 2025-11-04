<template>
  <q-layout view="hHh lpR fFf">

    <q-header>
      <NavBar />
    </q-header>

    <q-drawer v-model="store.showRightDrawer" side="right" bordered :width="240">
      <SnapshotList />
    </q-drawer>

    <q-page-container>
      <div
        :class="isMobile ? 'q-ma-md' : 'q-ma-xl'" 
        :style="{ 'margin-top': isMobile ? '10px' : '25px', height: '100' }"
      >
        <router-view :key="route.path" />
        <CreateButton v-if="addCreateButton" />
      </div>
    </q-page-container>

  </q-layout>
</template>

<script setup lang="ts">
  import { RouterView, useRoute } from 'vue-router'
  import NavBar from '@/components/NavBar.vue'
  import AccessibilityTest from '@/components/AccessibilityTest.vue'
  import { useQuasar } from 'quasar'
  import { computed, provide, watch } from 'vue'
  import CreateButton from './components/CreateButton.vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import SnapshotList from './components/SnapshotList.vue'

  const store = useLoginStore()
  
  const route = useRoute()

  const $q = useQuasar()

  const isExtraSmall = computed(() => {
    return $q.screen.xs
  })

  const isMobile = computed(() => {
    return $q.screen.sm || $q.screen.xs
  })

  const isMedium = computed(() => {
    return $q.screen.md || $q.screen.sm || $q.screen.xs
  })

  const darkMode = computed(() => {
    return $q.dark.isActive
  })
  
  provide('isMobile', isMobile)
  provide('isMedium', isMedium)
  provide('isExtraSmall', isExtraSmall)
  provide('darkMode', darkMode)

  watch(route, (to) => {
    // on every route change, close snapshot drawer if open
    if(store.showRightDrawer) {
      store.showRightDrawer = false
      store.selectedSnapshot = null
    }
  })

  const includeCreateButton = [
    'home',
    'experiments',
    'entrypoints',
    'plugins',
    'queues',
    'allJobs',
    'pluginParams',
    'tags',
    'models',
    'artifacts'
  ]

  const addCreateButton = computed(() => {
    return typeof route.name === 'string' && includeCreateButton.includes(route.name)
  })


</script>