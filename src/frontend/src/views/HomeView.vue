<template>
  <h1>Welcome to Dioptra</h1>
  <p>
    Here you can interact with the application by creating,
    viewing, and editing the components of your machine
    learning experiments.
  </p>
  <p>
    For reference and instructions, you can view our docs here: <br>
    <a href="https://pages.nist.gov/dioptra/" target="_blank" :class="darkMode && darkMode !== 'auto' ? 'darkLink' : ''">
      https://pages.nist.gov/dioptra/
    </a>
  </p>


</template>

<script setup>
  import { useQuasar } from 'quasar'
  import { computed } from 'vue'
  const $q = useQuasar()

  const darkMode = computed(() => {
    return $q.dark.mode
  })

</script>