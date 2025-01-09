<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('submit')"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Delete {{ type }}
      </label>
    </template>
    <q-card-section class="q-pt-none">
      Are you sure you want to delete this {{ type }}? <br>
      Name: <span class="text-bold">{{ name }}</span>
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'

  defineEmits(['submit'])
  defineProps(['type', 'name'])

  const showDialog = defineModel()

</script>