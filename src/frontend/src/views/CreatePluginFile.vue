<template>
  <div class="row items-center justify-between">
    <PageTitle :subtitle="title" conceptType="file" />
    <q-btn
      v-if="route.params.fileId !== 'new'"
      color="negative"
      icon="sym_o_delete"
      label="Delete Plugin File"
      @click="showDeleteFileDialog = true"
    />
  </div>
  <div class="row q-my-lg">
    <fieldset :class="`${isMobile ? 'col-12 q-mb-lg' : 'col q-mr-md'}`">
      <legend>Basic Info</legend>
      <div class="q-px-lg column full-height">
        <q-form @submit.prevent="submit" ref="basicInfoForm" greedy>
          <q-input
            outlined
            dense
            v-model.trim="pluginFile.filename"
            :rules="[requiredRule, pythonFilenameRule]"
            class="q-mb-sm q-mt-md"
            aria-required="true"
          >
            <template v-slot:before>
              <label :class="`field-label`">Filename:</label>
            </template>
          </q-input>

          <q-input
            outlined
            dense
            v-model.trim="pluginFile.description"
            class="q-mb-lg"
            type="textarea"
            autogrow
          >
            <template v-slot:before>
              <label :class="`field-label`">Description:</label>
            </template>
          </q-input>
        </q-form>

        <div class="row q-mb-sm justify-between">
          <q-file
            v-model="uploadedFile"
            label="Upload Python File"
            outlined
            use-chips
            dense
            accept=".py, text/x-python"
            @update:model-value="processFile"
            class="col q-mr-lg"
          >
            <template v-slot:before>
              <label :class="`field-label`">File Contents:</label>
            </template>
            <template v-slot:prepend>
              <q-icon name="attach_file" />
            </template>
          </q-file>
          <q-btn
            label="Import Function Tasks"
            color="primary"
            @click="showImportTasksDialog = true"
          />
        </div>

        <CodeEditor
          v-model="pluginFile.contents"
          language="python"
          :placeholder="'#Enter plugin file code here...'"
          style="margin-bottom: 15px"
          :showError="contentsError"
        />
      </div>
    </fieldset>
    <fieldset :class="`${isMobile ? 'col-12' : 'col q-ml-md'}`">
      <legend>Plugin Tasks</legend>

      <TableComponent
        :rows="pluginFile.tasks.functions"
        :columns="computedFunctionTaskColumns"
        title="Plugin Function Tasks"
        :hideToggleDraft="true"
        :hideSearch="true"
        :disableSelect="true"
        :hideOpenBtn="true"
        :hideDeleteBtn="true"
        rightCaption="*Click parameter to edit, or X to delete"
        @create="
          showTaskDialog = true;
          taskType = 'functions';
        "
      >
        <template #body-cell-name="props">
          <div class="row items-center cursor-pointer group">
            <span class="text-indigo-10 text-weight-bold text-subtitle2">
              {{ props.row.name }}
            </span>
            <q-icon
              name="edit"
              size="xs"
              color="primary"
              class="q-ml-sm invisible group-hover:visible"
            />

            <q-popup-edit v-model="props.row.name" v-slot="scope">
              <q-input
                v-model="scope.value"
                dense
                autofocus
                counter
                @keyup.enter="scope.set"
              />
            </q-popup-edit>
          </div>
        </template>

        <template #body-cell-inputParams="props">
          <div class="row justify-end q-gutter-xs">
            <template v-for="(param, i) in props.row.inputParams" :key="i">
              <q-chip
                color="indigo"
                text-color="white"
                size="sm"
                outline
                square
                clickable
                removable
                @remove="
                  pluginFile.tasks.functions[props.rowIndex].inputParams.splice(
                    i,
                    1,
                  )
                "
                @click="
                  handleSelectedParam(
                    'edit',
                    props,
                    i,
                    'inputParams',
                    'functions',
                  );
                  showEditParamDialog = true;
                "
              >
                <span class="text-weight-bold">{{ param.name }}</span>
                <span v-if="param.required" class="text-red q-ml-xs">*</span>
                <span class="q-ml-xs text-grey-6" style="font-size: 10px">
                  :
                  {{
                    pluginParameterTypes.find(
                      (t) => t.id === param.parameterType.id,
                    )?.name || "?"
                  }}
                </span>
              </q-chip>

              <q-chip
                v-if="
                  !pluginParameterTypes.find(
                    (t) => t.id === param.parameterType.id,
                  )?.name
                "
                color="negative"
                text-color="white"
                size="xs"
                square
                dense
                icon="warning"
              >
                <q-tooltip>Resolve missing type</q-tooltip>
              </q-chip>
            </template>

            <q-btn
              round
              size="xs"
              icon="add"
              color="indigo-1"
              text-color="indigo"
              unelevated
              @click="
                handleSelectedParam(
                  'create',
                  props,
                  i,
                  'inputParams',
                  'functions',
                );
                showEditParamDialog = true;
              "
            />
          </div>
        </template>

        <template #body-cell-outputParams="props">
          <div class="row justify-end q-gutter-xs">
            <div v-for="(param, i) in props.row.outputParams" :key="i">
              <q-chip
                color="purple"
                text-color="white"
                size="sm"
                outline
                square
                clickable
                removable
                @click="
                  handleSelectedParam(
                    'edit',
                    props,
                    i,
                    'outputParams',
                    'functions',
                  );
                  showEditParamDialog = true;
                "
                @remove="
                  pluginFile.tasks.functions[
                    props.rowIndex
                  ].outputParams.splice(i, 1)
                "
              >
                <span class="text-weight-bold">{{ param.name }}</span>
                <span class="q-ml-xs text-grey-6" style="font-size: 10px">
                  : {{ param.parameterType.name }}
                </span>
              </q-chip>
            </div>
            <q-btn
              round
              size="xs"
              icon="add"
              color="purple-1"
              text-color="purple"
              unelevated
              @click="
                handleSelectedParam(
                  'create',
                  props,
                  i,
                  'outputParams',
                  'functions',
                );
                showEditParamDialog = true;
              "
            />
          </div>
        </template>

        <template #body-cell-actions="props">
          <q-btn
            icon="sym_o_delete"
            round
            size="sm"
            color="negative"
            flat
            @click="
              selectedTaskProps = props;
              selectedTaskProps.taskType = 'functions';
              showDeleteDialog = true;
            "
          />
        </template>
      </TableComponent>

      <TableComponent
        :rows="pluginFile.tasks.artifacts"
        :columns="computedArtifactTaskColumns"
        title="Plugin Artifact Tasks"
        :hideToggleDraft="true"
        :hideSearch="true"
        :disableSelect="true"
        :hideOpenBtn="true"
        :hideDeleteBtn="true"
        rightCaption="*Click parameter to edit, or X to delete"
        class="q-mt-md"
        @create="
          showTaskDialog = true;
          taskType = 'artifacts';
        "
      >
        <template #body-cell-name="props">
          <div class="row items-center cursor-pointer group">
            <span class="text-indigo-10 text-weight-bold text-subtitle2">
              {{ props.row.name }}
            </span>
            <q-icon
              name="edit"
              size="xs"
              color="primary"
              class="q-ml-sm invisible group-hover:visible"
            />
            <q-popup-edit v-model="props.row.name" v-slot="scope">
              <q-input
                v-model="scope.value"
                dense
                autofocus
                counter
                @keyup.enter="scope.set"
              />
            </q-popup-edit>
          </div>
        </template>

        <template #body-cell-outputParams="props">
          <div class="row justify-end q-gutter-xs">
            <template v-for="(param, i) in props.row.outputParams" :key="i">
              <q-chip
                color="purple"
                text-color="white"
                size="sm"
                outline
                square
                clickable
                removable
                @click="
                  handleSelectedParam(
                    'edit',
                    props,
                    i,
                    'outputParams',
                    'artifacts',
                  );
                  showEditParamDialog = true;
                "
                @remove="
                  pluginFile.tasks.artifacts[
                    props.rowIndex
                  ].outputParams.splice(i, 1)
                "
              >
                <span class="text-weight-bold">{{ param.name }}</span>
                <span class="q-ml-xs text-grey-6" style="font-size: 10px">
                  : {{ param.parameterType.name }}
                </span>
              </q-chip>
            </template>
            <q-btn
              round
              size="xs"
              icon="add"
              color="purple-1"
              text-color="purple"
              unelevated
              @click="
                handleSelectedParam(
                  'create',
                  props,
                  i,
                  'outputParams',
                  'artifacts',
                );
                showEditParamDialog = true;
              "
            />
          </div>
        </template>

        <template #body-cell-actions="props">
          <q-btn
            icon="sym_o_delete"
            round
            size="sm"
            color="negative"
            flat
            @click="
              selectedTaskProps = props;
              selectedTaskProps.taskType = 'artifacts';
              showDeleteDialog = true;
            "
          />
        </template>
      </TableComponent>

      <q-expansion-item
        :label="`${showParamTypes ? 'Hide' : 'Show'} Plugin Parameter Types`"
        v-model="showParamTypes"
        header-class="text-bold shadow-2 bg-grey-2"
        class="q-mb-md q-mt-lg"
        ref="expansionItem"
        @after-show="scroll"
      >
        <TableComponent
          :rows="pluginParameterTypes"
          :columns="computedParamTypeColumns"
          title="Plugin Parameter Types"
          @request="getPluginParameterTypes"
          :hideToggleDraft="true"
          :hideCreateBtn="true"
          :disableSelect="true"
          style="margin-top: 0"
          :hideOpenBtn="true"
          :hideDeleteBtn="true"
          ref="tableRef"
        >
          <template #body-cell-view="props">
            <q-btn
              flat
              dense
              round
              icon="data_object"
              color="primary"
              @click.stop="
                structure = JSON.stringify(props.row.structure, null, 2);
                displayStructure = true;
              "
            >
              <q-tooltip>View Structure</q-tooltip>
            </q-btn>
          </template>
        </TableComponent>
      </q-expansion-item>
    </fieldset>
  </div>

  <div :class="`${isMobile ? '' : ''} float-right q-mb-lg`">
    <q-btn
      outline
      color="primary"
      label="Cancel"
      class="q-mr-lg cancel-btn"
      @click="confirmLeave = true; store.initialPage ? router.push(`/plugins/${route.params.id}`) : router.back()"
    />
    <q-btn
      @click="submit()"
      color="primary"
      label="Submit File"
      type="submit"
      :disable="!enableSubmit"
    >
      <q-tooltip v-if="!enableSubmit">
        No changes detected — nothing to save
      </q-tooltip>
    </q-btn>
  </div>

  <InfoPopupDialog v-model="displayStructure">
    <template #title>
      <label id="modalTitle"> Plugin Param Structure </label>
    </template>
    <CodeEditor v-model="structure" style="height: auto" :readOnly="true" />
  </InfoPopupDialog>
  <DeleteDialog
    v-model="showDeleteFileDialog"
    @submit="deleteFile()"
    type="Plugin File"
    :name="pluginFile.filename"
  />
  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="
      pluginFile.tasks[selectedTaskProps.taskType].splice(
        selectedTaskProps.rowIndex,
        1,
      );
      showDeleteDialog = false;
    "
    type="Plugin Task"
    :name="selectedTaskProps?.row?.name"
  />
  <EditPluginTaskParamDialog
    v-model="showEditParamDialog"
    :editParam="selectedParam"
    :pluginParameterTypes="pluginParameterTypes"
    :inputOrOutputParams="selectedTaskProps?.inputOrOutputParams"
    @updateParam="updateParam"
    @addParam="addParam"
  />
  <LeaveFormDialog
    v-model="showLeaveDialog"
    type="plugin file"
    @leaveForm="leaveForm"
  />
  <ReturnToFormDialog v-model="showReturnDialog" @cancel="clearForm" />
  <ImportPluginTasksDialog
    v-model="showImportTasksDialog"
    :pythonCode="pluginFile.contents"
    :pluginParameterTypes="pluginParameterTypes"
    :existingTasks="JSON.parse(JSON.stringify(pluginFile.tasks.functions))"
    @importTasks="addInferedTasks"
  />
  <PluginTaskDialog
    v-model="showTaskDialog"
    :taskType="taskType"
    :pluginParameterTypes="pluginParameterTypes"
    @submit="(task) => pluginFile.tasks[taskType].push(task)"
  />

  <!-- pluginFile.value.tasks[taskType.value].push(task) -->
</template>

<script setup>
import { ref, inject, watch, onMounted, computed } from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import CodeEditor from "@/components/CodeEditor.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import TableComponent from "@/components/table/TableComponent.vue";
import InfoPopupDialog from "@/dialogs/InfoPopupDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import EditPluginTaskParamDialog from "@/dialogs/EditPluginTaskParamDialog.vue";
import LeaveFormDialog from "@/dialogs/LeaveFormDialog.vue";
import ReturnToFormDialog from "@/dialogs/ReturnToFormDialog.vue";
import { useLoginStore } from "@/stores/LoginStore";
import ImportPluginTasksDialog from "@/dialogs/ImportPluginTasksDialog.vue";
import PluginTaskDialog from "@/dialogs/PluginTaskDialog.vue";

const store = useLoginStore();

const route = useRoute();
const router = useRouter();

const isMobile = inject("isMobile");

const pluginFile = ref({
  filename: "",
  description: "",
  contents: "",
  tasks: {
    functions: [],
    artifacts: [],
  },
});
const ORIGINAL_COPY = {
  filename: "",
  description: "",
  contents: "",
  tasks: {
    functions: [],
    artifacts: [],
  },
};

const valuesChangedFromOriginal = computed(() => {
  for (const key in ORIGINAL_COPY) {
    if (
      JSON.stringify(ORIGINAL_COPY[key]) !==
      JSON.stringify(pluginFile.value[key])
    ) {
      return true;
    }
  }
  return false;
});

const copyAtEditStart = ref();

const valuesChangedFromEditStart = computed(() => {
  for (const key in copyAtEditStart.value) {
    if (
      JSON.stringify(copyAtEditStart.value[key]) !==
      JSON.stringify(pluginFile.value[key])
    ) {
      return true;
    }
  }
  return false;
});

const enableSubmit = computed(() => {
  if (route.params.fileId === "new" && valuesChangedFromOriginal.value) {
    return true;
  } else if (
    route.params.fileId !== "new" &&
    valuesChangedFromEditStart.value
  ) {
    return true;
  } else {
    return false;
  }
});

const uploadedFile = ref(null);

const selectedTaskProps = ref();
const showDeleteFileDialog = ref(false);
const showDeleteDialog = ref(false);
const showEditParamDialog = ref(false);

const expansionItem = ref(null);
const showParamTypes = ref(false);

function scroll() {
  expansionItem.value.$el.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

const title = ref("");

onMounted(async () => {
  if (route.params.fileId === "new") {
    title.value = "Create File";
    if (store.savedForms.files[route.params.id]) {
      pluginFile.value = JSON.parse(
        JSON.stringify(store.savedForms.files[route.params.id]),
      );
      copyAtEditStart.value = JSON.parse(
        JSON.stringify(store.savedForms.files[route.params.id]),
      );
      showReturnDialog.value = true;
    }
    copyAtEditStart.value = JSON.parse(JSON.stringify(pluginFile.value));
    return;
  }
  try {
    const res = await api.getFile(route.params.id, route.params.fileId);
    console.log("getFile = ", res);
    pluginFile.value = {
      filename: res.data.filename,
      contents: res.data.contents,
      tasks: res.data.tasks,
      description: res.data.description,
    };
    title.value = `Edit ${res.data.filename}`;
    copyAtEditStart.value = JSON.parse(JSON.stringify(pluginFile.value));
  } catch (err) {
    notify.error(err.response.data.message);
  }
});

function requiredRule(val) {
  return !!val || "This field is required";
}

function pythonFilenameRule(val) {
  const regex = /^[a-zA-Z_][a-zA-Z0-9_]*\.py$/;
  if (!regex.test(val)) {
    return "Invalid Python filename";
  }
  if (val === "_.py") {
    return "_.py is not a valid Python filename";
  }
  return true;
}

const contentsError = ref("");

watch(
  () => pluginFile.value.contents,
  (newVal) => {
    if (clearFormExecuted.value) {
      clearFormExecuted.value = false;
    } else {
      contentsError.value = newVal.length > 0 ? "" : "This field is required";
    }
  },
);

async function submit() {
  basicInfoForm.value.validate().then((success) => {
    contentsError.value =
      pluginFile.value.contents?.length > 0 ? "" : "This field is required";
    const missingTypes = pluginFile.value.tasks.functions.some((task) =>
      [...task.inputParams, ...task.outputParams].some(
        (param) => !param.parameterType.id,
      ),
    );
    if (missingTypes) {
      notify.error(
        "Please resolve the missing types in the plugin task parameters",
      );
    }
    if (success && contentsError.value === "" && !missingTypes) {
      addOrModifyFile();
    } else {
      // error
    }
  });
}

async function addOrModifyFile() {
  try {
    let res;
    const submitFile = JSON.parse(JSON.stringify(pluginFile.value));
    submitFile.tasks.functions.forEach((fTask) => {
      delete fTask.id;
      fTask.inputParams.forEach((param) => {
        param.parameterType = param.parameterType.id;
      });
      fTask.outputParams.forEach((param) => {
        param.parameterType = param.parameterType.id;
      });
    });
    submitFile.tasks.artifacts.forEach((artifact) => {
      delete artifact.id;
      delete artifact.inputParams;
      artifact.outputParams.forEach((outputParam) => {
        outputParam.parameterType = outputParam.parameterType.id;
      });
    });
    console.log("submitting file = ", submitFile);
    if (route.params.fileId === "new") {
      res = await api.addFile(route.params.id, submitFile);
    } else {
      res = await api.updateFile(
        route.params.id,
        route.params.fileId,
        submitFile,
      );
    }
    store.savedForms.files[route.params.id] = null;
    notify.success(
      `Successfully ${route.params.fileId === "new" ? "created" : "updated"} '${res.data.filename}'`,
    );
    confirmLeave.value = true;
    router.push(`/plugins/${route.params.id}`);
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

function processFile() {
  const file = uploadedFile.value;
  if (!file) {
    pluginFile.value.contents = "";
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    pluginFile.value.contents = e.target.result;
  };
  reader.onerror = (e) => {
    console.log("error = ", e);
  };
  reader.readAsText(file); // Reads the file as text
}

const tableRef = ref(null);
const pluginParameterTypes = ref([]);
const displayStructure = ref(false);
const structure = ref("");

const columns = [
  { name: "name", label: "Name", align: "left", field: "name", sortable: true },
  {
    name: "description",
    label: "Description",
    field: "description",
    align: "left",
    sortable: true,
  },
  { name: "view", label: "Structure", align: "left", sortable: false },
];

const basicInfoForm = ref(null);

const computedParamTypeColumns = computed(() => [
  {
    name: "name",
    label: "Name",
    align: "left",
    field: "name",
    styleType: "resource-name",
    conceptType: "parameter-type",
    textType: "capitalize",
  },
  {
    name: "description",
    label: "Description",
    field: "description",
    align: "left",
    styleType: "long-text",
    maxWidth: "350px",
  },
  {
    name: "view",
    label: "Structure",
    align: "center",
    headerStyle: "width: 100px",
  },
]);


const computedFunctionTaskColumns = computed(() => [
  {
    name: "name",
    label: "Name",
    align: "left",
    field: "name",
    classes: "vertical-top",
    style: "width: 200px",
  },
  {
    name: "inputParams",
    label: "Input Parameters",
    field: "inputParams",
    align: "right",
    classes: "vertical-top",
    style: "white-space: normal; min-width: 250px",
  },
  {
    name: "outputParams",
    label: "Output Parameters",
    field: "outputParams",
    align: "right",
    classes: "vertical-top",
    style: "white-space: normal; min-width: 250px",
  },
  {
    name: "actions",
    label: "Actions",
    align: "center",
    style: "width: 50px",
  },
]);


const computedArtifactTaskColumns = computed(() => [
  {
    name: "name",
    label: "Name",
    align: "left",
    field: "name",
    classes: "vertical-top",
    style: "width: 200px",
  },
  {
    name: "outputParams",
    label: "Output Parameters",
    field: "outputParams",
    align: "right",
    classes: "vertical-top",
    style: "white-space: normal; min-width: 250px",
  },
  {
    name: "actions",
    label: "Actions",
    align: "center",
    style: "width: 50px",
  },
]);

async function getPluginParameterTypes(pagination) {
  pagination.rowsPerPage = 0; 
  try {
    const res = await api.getData("pluginParameterTypes", pagination);
    pluginParameterTypes.value = res.data.data;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

function addInferedTasks(tasks) {
  console.log("tasks = ", tasks);
  tasks.forEach((newTask) => {
    const index = pluginFile.value.tasks.functions.findIndex(
      (existingTask) => existingTask.name === newTask.name,
    );
    if (index !== -1) {
      pluginFile.value.tasks.functions.splice(index, 1, newTask);
    } else {
      pluginFile.value.tasks.functions.push(newTask);
    }
  });
  notify.success(
    `Successfully imported ${tasks.length} ${tasks.length === 1 ? "task" : "tasks"}`,
  );
}

const selectedParam = ref();

function handleSelectedParam(
  action,
  paramProps,
  paramIndex,
  inputOrOutputParams,
  functionsOrArtifacts,
) {
  selectedTaskProps.value = paramProps;
  selectedTaskProps.value.paramIndex = paramIndex;
  selectedTaskProps.value.inputOrOutputParams = inputOrOutputParams;
  selectedTaskProps.value.functionsOrArtifacts = functionsOrArtifacts;
  if (action === "create") {
    selectedParam.value = "";
    return;
  }
  selectedParam.value =
    selectedTaskProps.value.row[selectedTaskProps.value.inputOrOutputParams][
      selectedTaskProps.value.paramIndex
    ];
}

function updateParam(updatedParam) {
  pluginFile.value.tasks[selectedTaskProps.value.functionsOrArtifacts][
    selectedTaskProps.value.rowIndex
  ][selectedTaskProps.value.inputOrOutputParams][
    selectedTaskProps.value.paramIndex
  ] = updatedParam;
}

function addParam(newParam) {
  pluginFile.value.tasks[selectedTaskProps.value.functionsOrArtifacts][
    selectedTaskProps.value.rowIndex
  ][selectedTaskProps.value.inputOrOutputParams].push(newParam);
}

onBeforeRouteLeave((to, from, next) => {
  toPath.value = to.path;
  if (confirmLeave.value || !valuesChangedFromEditStart.value) {
    next(true);
  } else if (route.params.fileId === "new") {
    leaveForm();
  } else {
    showLeaveDialog.value = true;
  }
});

const showLeaveDialog = ref(false);
const showReturnDialog = ref(false);
const confirmLeave = ref(false);
const toPath = ref();

const isEmptyValues = computed(() => {
  return Object.values(pluginFile.value).every(
    (value) =>
      (typeof value === "string" && value === "") ||
      (Array.isArray(value) && value.length === 0),
  );
});

function leaveForm() {
  if (route.params.fileId === "new" && valuesChangedFromOriginal.value) {
    console.log("saving form...");
    store.savedForms.files[route.params.id] = pluginFile.value;
  } else {
    store.savedForms.files[route.params.id] = null;
  }
  confirmLeave.value = true;
  router.push(toPath.value);
}

const clearFormExecuted = ref(false);

function clearForm() {
  pluginFile.value = {
    filename: "",
    description: "",
    contents: "",
    tasks: {
      functions: [],
      artifacts: [],
    },
  };
  basicInfoForm.value.reset();
  clearFormExecuted.value = true;
  store.savedForms.files[route.params.id] = null;
}

async function deleteFile() {
  try {
    await api.deleteFile(route.params.id, route.params.fileId);
    showDeleteFileDialog.value = false;
    notify.success(`Successfully deleted '${pluginFile.value.filename}'`);
    router.push(`/plugins/${route.params.id}/files`);
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

const showImportTasksDialog = ref(false);
const showTaskDialog = ref(false);
const taskType = ref("functions");
</script>
