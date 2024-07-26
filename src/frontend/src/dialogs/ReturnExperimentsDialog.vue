<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('submit')"
    @emitCancel="store.savedExperimentForm = {}"
  >
    <template #title>Load Unfinished Form?</template>
    <q-card-section class="q-pt-none">
      You have previously visited this form without submitting.  Load previous values?<br><br>
      Name: {{ store.savedExperimentForm.name }} <br>
      Group: {{ store.savedExperimentForm.group }} <br>
      <div v-if="store.savedExperimentForm.selectedEntryPoints?.length">
        Entry Points: {{ store.savedExperimentForm.selectedEntryPoints }}
      </div>
      <div v-if="store.savedExperimentForm.selectedTags?.length">
        Tags: {{ store.savedExperimentForm.selectedTags }}
      </div>
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'
  import { useDataStore } from '@/stores/DataStore.ts'

  const store = useDataStore()

  defineEmits(['submit'])

  const showDialog = defineModel()

</script>