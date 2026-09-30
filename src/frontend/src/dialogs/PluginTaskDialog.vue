<template>
  <q-dialog
    v-model="showDialog"
    :persistent="true"
  >
    <q-card style="width: 760px; max-width: 95vw">
      <q-card-section class="bg-primary text-white text-h6 q-px-lg">
        <div class="text-h6">Create {{ taskType === "functions" ? "Function" : "Artifact" }} Task</div>
      </q-card-section>
      <q-card-section
        class="q-pa-lg"
        style="overflow-y: auto; max-height: 80vh"
      >
        <q-form
          id="taskForm"
          ref="taskForm"
          greedy
          @submit.prevent="addTask"
        >
          <q-input
            v-model.trim="task.name"
            outlined
            dense
            :rules="[requiredRule]"
            class="q-mt-sm"
          >
            <template #before>
              <label class="field-label">Task Name:</label>
            </template>
          </q-input>
          <q-card
            v-for="section in parameterSections"
            :key="section.kind"
            tag="section"
            flat
            bordered
            :aria-label="`${section.label} parameters`"
            class="q-pa-md q-mt-md"
          >
            <div class="text-subtitle1 text-weight-medium q-mb-md">{{ section.label }} Parameters</div>
            <div
              v-for="(param, index) in section.params"
              :key="param.rowId"
              class="row q-col-gutter-sm"
            >
              <div class="col-12 col-sm">
                <q-input
                  v-model.trim="param.name"
                  label="Name"
                  :aria-label="`${section.label} parameter ${index + 1} name`"
                  :rules="[(value) => isBlankParam(param) || requiredRule(value)]"
                  reactive-rules
                  dense
                  outlined
                />
              </div>
              <div class="col-12 col-sm">
                <q-select
                  v-model="param.parameterType"
                  emit-value
                  option-value="id"
                  option-label="name"
                  map-options
                  label="Type"
                  :aria-label="`${section.label} parameter ${index + 1} type`"
                  :options="pluginParameterTypes"
                  :rules="[(value) => isBlankParam(param) || requiredRule(value)]"
                  reactive-rules
                  outlined
                  dense
                />
              </div>
              <div
                v-if="section.kind === 'input'"
                class="col-auto"
              >
                <q-checkbox
                  v-model="param.required"
                  label="Required"
                  :aria-label="`${section.label} parameter ${index + 1} required`"
                />
              </div>
              <div class="col-auto">
                <q-btn
                  flat
                  round
                  icon="sym_o_delete"
                  color="negative"
                  :aria-label="`Remove ${section.kind} parameter ${index + 1}`"
                  @click="section.params.splice(index, 1)"
                >
                  <q-tooltip>Remove parameter</q-tooltip>
                </q-btn>
              </div>
            </div>
            <q-btn
              flat
              dense
              :color="$q.dark.isActive ? 'blue-3' : 'primary'"
              icon="add"
              :label="`Add another ${section.kind}`"
              @click="section.params.push(createParam())"
            />
          </q-card>
        </q-form>
      </q-card-section>
      <q-separator />
      <q-card-actions
        align="right"
        class="q-px-lg q-py-md"
      >
        <q-btn
          v-close-popup
          outline
          color="primary cancel-btn"
          label="Cancel"
          class="q-mr-xs"
        />
        <q-btn
          label="Create Task"
          color="primary"
          type="submit"
          form="taskForm"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps(["taskType", "pluginParameterTypes"]);
const emit = defineEmits(["submit"]);
const showDialog = defineModel();

let nextRowId = 0;

function createParam() {
  return { rowId: nextRowId++, name: "", parameterType: "", required: true };
}

const inputParams = ref([createParam()]);
const outputParams = ref([createParam()]);
const task = ref({});
const taskForm = ref(null);

const parameterSections = computed(() => {
  const sections = [{ kind: "output", label: "Output", params: outputParams.value }];
  if (props.taskType === "functions") {
    sections.unshift({ kind: "input", label: "Input", params: inputParams.value });
  }
  return sections;
});

function requiredRule(val) {
  return !!val || "This field is required";
}

function isBlankParam(param) {
  return !param.name && !param.parameterType;
}

function serializeParams(params, includeRequired = false) {
  return params
    .filter((param) => !isBlankParam(param))
    .map((param) => {
      const type = props.pluginParameterTypes.find((paramType) => paramType.id === param.parameterType);
      return {
        name: param.name,
        parameterType: { name: type.name, id: type.id },
        ...(includeRequired ? { required: param.required } : {}),
      };
    });
}

function addTask() {
  emit("submit", {
    name: task.value.name,
    inputParams: props.taskType === "functions" ? serializeParams(inputParams.value, true) : [],
    outputParams: serializeParams(outputParams.value),
  });
  showDialog.value = false;
}

watch(showDialog, (newVal) => {
  if (!newVal) {
    task.value = {};
    inputParams.value = [createParam()];
    outputParams.value = [createParam()];
    taskForm.value?.resetValidation();
  }
});
</script>
