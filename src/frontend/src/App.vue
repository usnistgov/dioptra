<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import NavBar from '@/components/NavBar.vue'

</script>

<template>
  <NavBar />
  <div class="q-ma-xl">
    <RouterView />
  </div>

</template>