<template>
  <q-dialog v-model="showDialog" aria-labelledby="modalTitle">
    <q-card style="width: 95%; max-height: 80vh" flat >
      <q-card-section class="bg-primary text-white q-mb-md">
        <div class="text-h6">
          <slot name="title"  />
        </div>
      </q-card-section>
      <q-card-section style="overflow-y: auto; max-height: 60vh">
        <slot />
      </q-card-section>
      <q-separator />
      <q-card-actions align="right" class="text-primary">
        <q-btn color="primary" class="text-white" label="Close" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
  import { onMounted, ref } from 'vue'

  const showDialog = defineModel()

</script>