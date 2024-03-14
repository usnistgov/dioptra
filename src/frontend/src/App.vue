<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import AccessibilityTest from '@/components/AccessibilityTest.vue'

</script>

<template>
  <NavBar />
  <main class="q-ma-xl">
    <RouterView />
  </main>
  <!-- <AccessibilityTest /> -->


</template>