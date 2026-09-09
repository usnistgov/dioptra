<template>
  <q-dialog
    v-model="showDialog"
    aria-labelledby="addSwappableTaskDialogTitle"
    :persistent="true"
  >
    <q-card style="width: 500px; max-width: 90vw">
      <q-card-section class="bg-primary text-white">
        <div
          id="addSwappableTaskDialogTitle"
          class="text-h6"
        >
          Add Swappable Task
        </div>
      </q-card-section>

      <q-card-section>
        <q-form
          id="addSwappableTaskForm"
          @submit.prevent="submit"
        >
          <q-select
            v-model="selectedSwapStep"
            :options="swapStepOptions"
            option-label="label"
            label="Step"
            outlined
            dense
            @update:model-value="$emit('stepChanged')"
          />

          <q-list
            dense
            class="q-mt-md"
          >
            <q-item
              v-if="selectedSwapStep?.createNew"
              tag="label"
            >
              <q-item-section avatar>
                <q-checkbox
                  :model-value="true"
                  disable
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ selectedSwapTask?.name }}</q-item-label>
                <q-item-label caption>{{ selectedSwapTask?.plugin?.name }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item
              v-for="task in selectableSwappableTasks"
              :key="`${task.plugin.id}-${task.id || task.name}`"
              tag="label"
            >
              <q-item-section avatar>
                <q-checkbox
                  v-model="selectedSwappableTasks"
                  :val="task"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ task.name }}</q-item-label>
                <q-item-label caption>{{ task.plugin.name }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item v-if="selectableSwappableTasks.length === 0">
              <q-item-section class="text-grey-7">
                {{
                  selectedSwapStep?.createNew
                    ? "No other tasks with same output parameter types."
                    : "No compatible tasks available to add."
                }}
              </q-item-section>
            </q-item>
          </q-list>
        </q-form>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn
          v-close-popup
          outline
          color="primary cancel-btn"
          label="Cancel"
          class="q-mr-xs"
        />
        <q-btn
          color="primary"
          label="Confirm"
          type="submit"
          form="addSwappableTaskForm"
          :disable="!canSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
defineProps(["selectedSwapTask", "swapStepOptions", "selectableSwappableTasks", "canSubmit"]);

const emit = defineEmits(["stepChanged", "submit"]);

const showDialog = defineModel();
const selectedSwapStep = defineModel("selectedSwapStep");
const selectedSwappableTasks = defineModel("selectedSwappableTasks");

function submit() {
  emit("submit");
  showDialog.value = false;
}
</script>
