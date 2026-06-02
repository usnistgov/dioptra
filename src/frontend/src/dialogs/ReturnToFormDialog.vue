<template>
  <DialogComponent
    v-model="showDialog"
    :hideDraftBtn="true"
    :persistent="true"
    @emitSubmit="showDialog = false"
    @emitCancel="$emit('cancel')"
  >
    <template #title>Load Unsaved Form?</template>
    <q-card-section class="q-pt-none">
      You have previously visited this form without submitting. Load previous inputs?
    </q-card-section>
  </DialogComponent>
</template>

<script setup>
import DialogComponent from "./DialogComponent.vue";

defineEmits(["cancel"]);

const showDialog = defineModel();
</script>
