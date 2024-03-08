<template>
  <q-dialog v-model="showDialog">
    <q-card style="width: 95%" flat >
      <q-form @submit="$emit('emitSubmit')">
        <q-card-section class="bg-primary text-white q-mb-md">
          <div class="text-h6">
            <slot name="title" />
          </div>
        </q-card-section>
        <q-card-section>
          <slot />
        </q-card-section>
        <q-separator />
        <q-card-actions align="right" class="text-primary">
          <q-btn color="secondary" class="text-white" label="Cancel" @click="$emit('emitCancel')" v-close-popup />
          <q-btn color="primary" label="Confirm" type="submit" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
  const showDialog = defineModel()
  defineEmits(['emitSubmit', 'emitCancel'])
</script>