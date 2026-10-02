<template>
  <q-dialog
    v-model="showDialog"
    @show="onDialogShow"
  >
    <q-card style="display: inline-block; width: auto; max-width: 800px">
      <q-card-section class="bg-primary text-white text-h6"> Import Plugin Function Tasks </q-card-section>

      <q-card-section
        style="max-height: 75vh"
        class="scroll"
      >
        <p class="text-body2">
          The plugin tasks below have been inferred from your python code. Select the tasks you would like to import.
          Duplicate tasks will be overwritten.
        </p>
        <p
          v-if="errorMessage"
          class="text-negative"
          style="max-width: 500px"
        >
          Error: {{ errorMessage }}
        </p>
        <TableComponent
          ref="tableRef"
          v-model:selected="selectedTasks"
          :rows="tasks"
          :columns="taskColumns"
          title="Plugin Tasks"
          :hideToggleDraft="true"
          :hideCreateBtn="true"
          :hideSearch="true"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          :enableHighlightRow="true"
          :disabledRowKeys="disabledRowKeys"
          selection="multiple"
          row-key="name"
          :loading="loading"
        >
          <template #body-cell-name="cellProps">
            <div style="font-size: 18px">
              {{ cellProps.row.name }}
              <!-- <p v-if="cellProps.row.missing_types.length > 0" class="text-caption text-negative">
                Missing Types:
                <div v-for="type in cellProps.row.missing_types">
                  {{ type.name }}
                </div>
              </p> -->
            </div>
          </template>
          <template #body-cell-inputParams="cellProps">
            <div class="column items-end">
              <q-chip
                v-for="(param, i) in cellProps.row.inputParams"
                :key="i"
                color="indigo"
                text-color="white"
                dense
              >
                {{ `${param.name}` }}
                <span
                  v-if="param.required"
                  class="text-red"
                  >*</span
                >
                {{ `: ${param.type}` }}
              </q-chip>
              <q-chip
                v-if="cellProps.row.inputParams.length === 0"
                dense
                color="orange"
                text-color="white"
                square
                label="No params listed"
              />
            </div>
          </template>
          <template #body-cell-outputParams="cellProps">
            <div class="column items-end">
              <q-chip
                v-for="(param, i) in cellProps.row.outputParams"
                :key="i"
                color="purple"
                text-color="white"
                dense
                :label="`${param.name}: ${param.type}`"
              />
              <q-chip
                v-if="cellProps.row.outputParams.length === 0"
                dense
                color="orange"
                text-color="white"
                square
                label="No params listed"
              />
            </div>
          </template>
          <template #body-cell-select="cellProps">
            <q-checkbox
              v-model="selectedTasks"
              :val="cellProps.row"
            />
          </template>
          <template #expandedSlot="{ row, rowProps }">
            <div
              style="cursor: pointer"
              @click="rowProps.selected = !rowProps.selected"
            >
              <div
                v-if="Object.hasOwn(dupliateIdenticalTasks, row.name)"
                class="row"
                @vue:mounted="expandRow(row, rowProps)"
              >
                Duplicate task with identical params already exist in your plugin file.
              </div>
              <div
                v-if="Object.hasOwn(dupliateTasksWithDifferentParams, row.name)"
                @vue:mounted="expandRow(row, rowProps)"
              >
                <div class="row">Duplicate task. Importing will overwrite the existing params below.</div>
                <div class="row justify-end">
                  <div class="column items-end">
                    <q-chip
                      v-for="(param, i) in dupliateTasksWithDifferentParams[row.name].inputParams"
                      :key="i"
                      color="indigo"
                      text-color="white"
                      dense
                    >
                      {{ `${param.name}` }}
                      <span
                        v-if="param.required"
                        class="text-red"
                        >*</span
                      >
                      {{ `: ${param.type}` }}
                    </q-chip>
                    <q-chip
                      v-if="dupliateTasksWithDifferentParams[row.name].inputParams.length === 0"
                      dense
                      color="orange"
                      text-color="white"
                      square
                      label="No params listed"
                    />
                  </div>
                  <div
                    class="column items-end"
                    :style="{ width: outputParamsWidth ? outputParamsWidth + 'px' : '172px' }"
                  >
                    <q-chip
                      v-for="(param, i) in dupliateTasksWithDifferentParams[row.name].outputParams"
                      :key="i"
                      color="purple"
                      text-color="white"
                      dense
                      :label="`${param.name}: ${param.type}`"
                    />
                    <q-chip
                      v-if="dupliateTasksWithDifferentParams[row.name].outputParams.length === 0"
                      dense
                      color="orange"
                      text-color="white"
                      square
                      label="No params listed"
                    />
                  </div>
                </div>
              </div>
            </div>
          </template>
        </TableComponent>
      </q-card-section>

      <q-separator />

      <q-card-actions
        align="right"
        class="text-primary"
      >
        <q-form @submit="submit()">
          <q-btn
            v-close-popup
            outline
            color="primary cancel-btn"
            label="Cancel"
            class="q-mr-md"
          />
          <q-btn
            color="primary"
            type="submit"
          >
            Import
          </q-btn>
        </q-form>
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import * as api from "@/services/dataApi";
import TableComponent from "@/components/TableComponent.vue";
import * as notify from "../notify";

const props = defineProps(["pythonCode", "pluginParameterTypes", "existingTasks"]);
const emit = defineEmits(["importTasks"]);

const showDialog = defineModel();

const existingTasksCopy = ref([]);

const tableRef = ref();
const outputParamsWidth = ref(0);
const loading = ref(true);

watch(
  () => showDialog.value,
  (newVal) => {
    if (newVal) {
      tasks.value = [];
      errorMessage.value = "";
      disabledRowKeys.value = [];
      existingTasksCopy.value = JSON.parse(JSON.stringify(props.existingTasks));
      suggestPluginTasks();
    }
  },
);

function getColumnWidthPxByLabel(label) {
  const tableEl = (tableRef.value && tableRef.value.$el) || null;
  if (!tableEl) return 0;
  const spans = tableEl.querySelectorAll(".header-label");
  for (let i = 0; i < spans.length; i++) {
    const s = spans[i];
    if ((s.textContent || "").trim() === label) {
      const th = s.closest("th");
      if (th && th.getClientRects().length > 0 && th.offsetParent !== null) {
        // minus 8 to account for the left padding in the table headers
        return th.getBoundingClientRect().width - 8;
      }
    }
  }
  return 0;
}

function onDialogShow() {
  // Let QDialog/QTable finish layout in the next frame
  requestAnimationFrame(() => {
    outputParamsWidth.value = getColumnWidthPxByLabel("Output Parameters");
  });
}

const tasks = ref([]);
const selectedTasks = ref([]);
const errorMessage = ref("");

async function suggestPluginTasks() {
  try {
    const res = await api.suggestPluginTasks(props.pythonCode);
    /*
      endpoint task:
        inputs: [{ name: "name", required: true, type: "string" }],
        outputs: [{ name: "output", type: "string" }],
        missing_types: []
      existing task:
        inputParams: [{ name: "name", required: true, parameterType: {id, name} }],
        outputParams: [{ name: "output", parameterType: {id, name} }],
    */

    // endpoint tasks, change inputs/outputs keys to inputParams/outputParams
    tasks.value = res.data.tasks.map(({ inputs, outputs, ...rest }) => ({
      ...rest,
      inputParams: inputs,
      outputParams: outputs,
    }));
    console.log("infered tasks = ", tasks.value);
    console.log("existing tasks = ", existingTasksCopy.value);

    // endpoint tasks, add parameterType id
    tasks.value.forEach((task) => {
      [...task.inputParams, ...task.outputParams].forEach((param) => {
        param.parameterType = props.pluginParameterTypes.find((type) => type.name === param.type)?.id;
      });
    });

    // existing tasks, add type string
    existingTasksCopy.value.forEach((task) => {
      [...task.inputParams, ...task.outputParams].forEach((param) => {
        param.parameterType = param.parameterType.id;
        param.type = props.pluginParameterTypes.find((type) => type.id === param.parameterType)?.name;
      });
    });

    // auto select all tasks except for exact duplicates
    selectedTasks.value = tasks.value.filter((task) => !Object.keys(dupliateIdenticalTasks.value).includes(task.name));
    loading.value = false;
  } catch (err) {
    console.warn(err);
    notify.error(err.response.data.message);
    errorMessage.value = err.response.data.message;
  }
}

const taskColumns = [
  { name: "select", label: "Select", align: "center" },
  { name: "name", label: "Name", align: "left", field: "name", sortable: false },
  {
    name: "inputParams",
    label: "Input Parameters",
    field: "inputParams",
    align: "right",
    sortable: false,
    style: "width: 175px",
  },
  {
    name: "outputParams",
    label: "Output Parameters",
    field: "outputParams",
    align: "right",
    sortable: false,
    style: "width: 175px",
  },
];

async function submit() {
  selectedTasks.value.forEach((task) => {
    delete task.missing_types;
    [...task.inputParams, ...task.outputParams].forEach((param) => {
      param.parameterType = {
        id: param.parameterType,
        name: param.type,
      };
      delete param.type;
    });
  });
  emit("importTasks", selectedTasks.value);
  showDialog.value = false;
}

const dupliateTasksWithDifferentParams = computed(() => {
  const returnObject = {};
  if (tasks.value.length === 0 || existingTasksCopy.value.length === 0) return returnObject;
  tasks.value.forEach((task) => {
    const duplicate = existingTasksCopy.value.find((existingTask) => existingTask.name === task.name);
    if (!duplicate) return;
    const areEqual = deepEqual(task, duplicate, ["missing_types", "id"]);
    if (areEqual) return;
    else {
      returnObject[`${task.name}`] = {
        inputParams: duplicate.inputParams,
        outputParams: duplicate.outputParams,
      };
    }
  });
  return returnObject;
});

const dupliateIdenticalTasks = computed(() => {
  const returnObject = {};
  if (tasks.value.length === 0 || existingTasksCopy.value.length === 0) return returnObject;
  tasks.value.forEach((task) => {
    const duplicate = existingTasksCopy.value.find((existingTask) => existingTask.name === task.name);
    if (!duplicate) return;
    const areEqual = deepEqual(task, duplicate, ["missing_types", "id"]);
    if (!areEqual) return;
    else {
      returnObject[`${task.name}`] = {
        inputParams: duplicate.inputParams,
        outputParams: duplicate.outputParams,
      };
    }
  });
  return returnObject;
});

const disabledRowKeys = ref([]);

// expand row only if duplicate with different param exists
function expandRow(row, rowProps) {
  const duplicate = existingTasksCopy.value.find((task) => task.name === row.name);
  if (!duplicate) return null;
  rowProps.expand = true;
  if (row.name in dupliateIdenticalTasks.value) {
    disabledRowKeys.value.push(row.name);
  }
}

function deepEqual(obj1, obj2, ignoreKeys = []) {
  const isObject = (obj) => obj && typeof obj === "object";

  if (!isObject(obj1) || !isObject(obj2)) return obj1 === obj2;

  const keys1 = Object.keys(obj1).filter((k) => !ignoreKeys.includes(k));
  const keys2 = Object.keys(obj2).filter((k) => !ignoreKeys.includes(k));

  if (keys1.length !== keys2.length) return false;

  return keys1.every((key) => keys2.includes(key) && deepEqual(obj1[key], obj2[key], ignoreKeys));
}
</script>

<style scoped>
/* make inputParams and outputParams cells top-aligned */
:deep(.q-table tbody td:nth-child(3)),
:deep(.q-table tbody td:nth-child(4)) {
  vertical-align: top;
}
</style>
