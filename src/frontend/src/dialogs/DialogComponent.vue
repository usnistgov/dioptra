<template>
  <q-dialog
    v-model="showDialog"
    aria-labelledby="modalTitle"
    :persistent="persistent"
  >
    <q-card
      flat
      :style="{ 'min-width': isExtraSmall ? '95%' : isMobile ? '60%' : isMedium ? '40%' : '30%' }"
    >
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
        <q-card-actions
          align="right"
          class="text-primary"
        >
          <q-btn
            v-if="!hideDraftBtn"
            v-close-popup
            color="secondary"
            label="Save Draft"
            @click="$emit('emitSaveDraft')"
          />
          <q-space />
          <q-btn
            v-close-popup
            outline
            color="primary cancel-btn"
            label="Cancel"
            class="q-mr-xs"
            @click="$emit('emitCancel')"
          />
          <q-btn
            color="primary"
            label="Confirm"
            type="submit"
            :disable="disableConfirm"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { inject } from "vue";
const showDialog = defineModel("showDialog");
defineEmits(["emitSubmit", "emitCancel", "emitSaveDraft"]);
defineProps(["hideDraftBtn", "persistent", "showHistoryToggle", "disableConfirm"]);

const history = defineModel("history");

const isMedium = inject("isMedium");
const isMobile = inject("isMobile");
const isExtraSmall = inject("isExtraSmall");
</script>
