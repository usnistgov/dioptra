<template>
  <NavBar />
  <main :class="isMobile ? 'q-ma-md' : 'q-ma-xl'">
    <RouterView />
  </main>
  <!-- <AccessibilityTest /> -->
</template>

<script setup lang="ts">
  import { RouterView } from 'vue-router'
  import NavBar from '@/components/NavBar.vue'
  import AccessibilityTest from '@/components/AccessibilityTest.vue'
  import { useQuasar } from 'quasar'
  import { computed, provide } from 'vue'

  const $q = useQuasar()

  const isMobile = computed(() => {
    return $q.screen.sm || $q.screen.xs
  })
  
  provide('isMobile', isMobile)

</script>