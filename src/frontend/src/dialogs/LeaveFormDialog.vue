<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('leaveForm')"
    :hideDraftBtn="true"
  >
    <template #title>Leave <span class="text-capitalize">{{ type }}</span> Form?</template>
    <q-card-section class="q-pt-none">
      You are about to leave the {{ type }} form and have unsaved changes. <br>
      All unsaved changes will be lost.  Continue?
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import DialogComponent from './DialogComponent.vue'

  defineEmits(['leaveForm'])
  defineProps(['type'])

  const showDialog = defineModel()

</script>