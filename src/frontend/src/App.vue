<template>
  <NavBar />
  <main :class="isMobile ? 'q-ma-md' : 'q-ma-xl'">
    <PageTitle v-if="!hidePageTitle" />
    <RouterView />
  </main>
  <!-- <AccessibilityTest /> -->
</template>

<script setup lang="ts">
  import { RouterView, useRoute } from 'vue-router'
  import NavBar from '@/components/NavBar.vue'
  import AccessibilityTest from '@/components/AccessibilityTest.vue'
  import { useQuasar } from 'quasar'
  import { computed, provide } from 'vue'
  import PageTitle from '@/components/PageTitle.vue'

  const route = useRoute()

  const $q = useQuasar()

  const isMobile = computed(() => {
    return $q.screen.sm || $q.screen.xs
  })

  const hidePageTitle = computed(() => {
    if(route.path === '/' || route.path === '/login' || route.path === '/register') {
      return true
    }
    return false
  })
  
  provide('isMobile', isMobile)

</script>