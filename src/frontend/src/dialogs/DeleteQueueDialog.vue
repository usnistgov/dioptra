<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('submit')"
  >
    <template #title>Confirm Delete</template>
    <q-card-section class="q-pt-none">
      Are you sure you want to delete this Queue? <br>
      Name: <span class="text-bold">{{ name }}</span>
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'

  defineEmits(['submit'])
  defineProps(['name'])

  const showDialog = defineModel()

</script>