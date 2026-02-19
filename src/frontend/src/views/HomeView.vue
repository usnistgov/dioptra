<template>
  <h1>Welcome to Dioptra</h1>
  <p>
    Here you can interact with the application by creating,
    viewing, and editing the components of your machine
    learning experiments.
  </p>
  <p>
    To get started, consider importing the example entrypoints and plugins distributed with Dioptra <a href="#" @click="showImportDialog = true">here</a>.
  </p>
  <p>
    For reference and instructions, you can view our docs here: <br>
    <a href="https://pages.nist.gov/dioptra/" target="_blank">
      https://pages.nist.gov/dioptra/
    </a>
  </p>

  <ImportResourcesDialog v-model="showImportDialog" />
</template>

<script setup>
  import { useQuasar } from 'quasar'
  import { computed } from 'vue'
  const $q = useQuasar()

  import ImportResourcesDialog from '../dialogs/ImportResourcesDialog.vue';
  const showImportDialog = defineModel()

  const darkMode = computed(() => {
    return $q.dark.mode
  })
</script>
