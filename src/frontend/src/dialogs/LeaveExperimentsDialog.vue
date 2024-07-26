<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('leaveForm')"
    :hideDraftBtn="true"
  >
    <template #title>Leave New Experiment Form?</template>
    <q-card-section class="q-pt-none">
      You are about to leave the new experiment form. <br>
      All unsaved changes will be lost.  Continue?
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'

  defineEmits(['leaveForm'])
  defineProps(['name'])

  const showDialog = defineModel()

</script>