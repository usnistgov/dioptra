<template>
  <NavBar class="fixed-top" style="z-index: 999;" />
  <main :class="isMobile ? 'q-ma-md' : 'q-ma-xl'" style="margin-top: 75px;">
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
  
  const route = useRoute()

  const $q = useQuasar()

  const isMobile = computed(() => {
    return $q.screen.sm || $q.screen.xs
  })
  
  provide('isMobile', isMobile)

</script>