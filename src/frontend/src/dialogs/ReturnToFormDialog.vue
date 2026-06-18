<template>
  <DialogComponent 
    v-model="showDialog"
    :hideDraftBtn="true"
    @emitSubmit="showDialog = false"
    @emitCancel="$emit('cancel')"
    :persistent="true"
  >
    <template #title>Load Unsaved Form?</template>
    <q-card-section class="q-pt-none">
      You have previously visited this form without submitting.  Load previous inputs?
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'

  const store = useLoginStore()

  defineEmits(['cancel'])

  const showDialog = defineModel()

</script>