<template>
  <DialogComponent 
    v-model="showDialog"
    @emitSubmit="$emit('submit', resourceDraftMode ? true : false)"
    :hideDraftBtn="true"
  >
    <template #title>
      <label id="modalTitle">
        Delete {{ type }} {{ resourceDraftMode ? 'Draft' : '' }}
      </label>
    </template>
    <q-card-section class="q-pt-none">
      Are you sure you want to delete 
      <span v-if="resourceDraftMode"> the <span class="text-bold">draft</span> for </span> 
      this {{ type }}? <br>
      Name: <span class="text-bold">{{ name }}</span>
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
  import { watch } from 'vue'
  import DialogComponent from './DialogComponent.vue'

  defineEmits(['submit'])
  defineProps(['type', 'name'])

  const showDialog = defineModel('showDialog')
  const resourceDraftMode = defineModel('resourceDraftMode')

  watch(showDialog, (newVal) => {
    if(!newVal) resourceDraftMode.value = false
  })

</script>