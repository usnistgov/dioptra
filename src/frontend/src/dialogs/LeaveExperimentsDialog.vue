<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('submit')"
  >
    <template #title>Leave New Experiment Form?</template>
    <q-card-section class="q-pt-none">
      You are about to leave the new experiment form to create a new Entry Point. <br>
      Your progress will be saved.  Continue?
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'

  defineEmits(['submit'])
  defineProps(['name'])

  const showDialog = defineModel()

</script>