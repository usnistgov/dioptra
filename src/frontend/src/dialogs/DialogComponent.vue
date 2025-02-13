<template>
  <q-dialog v-model="showDialog" aria-labelledby="modalTitle" :persistent="persistent">
    <q-card flat :style="{ 'min-width': isMedium ? '50%' : '30%' }">
      <q-form @submit="$emit('emitSubmit')">
        <q-card-section class="bg-primary text-white q-mb-md">
          <div class="text-h6 row justify-between">
            <slot name="title" />
            <q-toggle
              v-if="showHistoryToggle"
              v-model="history"
              color="orange"
              left-label
              label="View History"
              class="text-body2"
            />
          </div>
        </q-card-section>
        <q-card-section>
          <slot />
        </q-card-section>
        <q-separator />
        <q-card-actions align="right" class="text-primary">
          <q-btn
            v-if="!hideDraftBtn"
            color="secondary"
            label="Save Draft"
            @click="$emit('emitSaveDraft')"
            v-close-popup
          />
          <q-space />
          <q-btn color="negative" class="text-white" label="Cancel" @click="$emit('emitCancel')" v-close-popup />
          <q-btn color="primary" label="Confirm" type="submit" :disable="disableConfirm" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
  import { inject } from 'vue'
  const showDialog = defineModel('showDialog')
  defineEmits(['emitSubmit', 'emitCancel', 'emitSaveDraft'])
  const props = defineProps(['hideDraftBtn', 'persistent', 'showHistoryToggle', 'disableConfirm'])

  const history = defineModel('history')

  const isMedium = inject('isMedium')

</script>