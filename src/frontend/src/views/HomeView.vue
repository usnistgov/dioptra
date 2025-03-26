<template>
  <h1>Welcome to Dioptra</h1>
  <p>
    Here you can interact with the application by creating,
    viewing, and editing the components of your machine
    learning experiments.
  </p>
  <p>
    For reference and instructions, you can view our docs here: <br>
    <a href="https://pages.nist.gov/dioptra/" target="_blank">
      https://pages.nist.gov/dioptra/
    </a>
  </p>

  <br />
  <div :class="`flex flex-center q-mt-xl ${isMobile ? '' : 'q-pt-xl' } `">
	  <ImportResourcesForm />
  </div>

</template>

<script setup>
  import { useQuasar } from 'quasar'
  import { computed } from 'vue'
  import ImportResourcesForm from '../components/ImportResourcesForm.vue';
  const $q = useQuasar()

  const darkMode = computed(() => {
    return $q.dark.mode
  })
</script>
