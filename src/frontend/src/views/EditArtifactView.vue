<template>
  <div class="row items-center">
    <PageTitle
      :subtitle="`Artifact ${route.params.id}`"
      conceptType="artifact"
    />
    <q-chip
      v-if="route.params.id !== 'new'"
      class="q-ml-lg"
      :color="`${darkMode ? 'grey-9' : 'grey-3'}`"
      label="View History"
      icon="history"
      @click="store.showRightDrawer = !store.showRightDrawer"
      clickable
    >
      <q-toggle v-model="store.showRightDrawer" left-label color="orange" />
    </q-chip>
  </div>

  <h2 class="q-mt-lg text-h6">Details</h2>

  <KeyValueTable :rows="rows" :disabled="showHistory">
    <template #id>
      <ResourceName
        conceptType="artifact"
        :text="artifact.id"
        ,
        includeIcon="true"
      />
    </template>

    <template #description>
      <div class="row items-center justify-start">
        <CellLongText
          :text="artifact.description"
          max-width="800px"
          class="col-auto"
        />

        <q-btn icon="edit" round size="sm" color="primary" flat class="q-ml-sm">
          <q-tooltip>Edit Description</q-tooltip>
        </q-btn>

        <q-popup-edit v-model="artifact.description" auto-save v-slot="scope">
          <q-input
            v-model="scope.value"
            dense
            autofocus
            counter
            @keyup.enter="scope.set"
            label="Description"
          />
        </q-popup-edit>
      </div>
    </template>

    <template #fileUrl="{ fileUrl }">
      <q-btn
        :href="fileUrl"
        :download="`artifact-${artifact?.id}`"
        label="Download Artifact"
        color="primary"
        icon="download"
        size="sm"
        class="q-my-sm q-py-sm"
      />
    </template>

    <template #job>
      <RouterLink :to="`/jobs/${artifact?.job}`" style="text-decoration: none">
        <BadgeIcon type="job" :label="artifact.job" :showIcon="true" />
      </RouterLink>
    </template>

    <template #plugin="{ plugin = {} }">
      <div class="column">
        <div
          v-if="Object.keys(plugin).length === 0 && !isLoading"
          class="text-red q-mb-xs"
        >
          <q-icon name="sym_o_warning" size="1.5em" class="q-mr-xs" />
          The attached plugin has been deleted.
        </div>

        <q-select
          label="Attached Plugin"
          v-model="artifact.plugin"
          @filter="getPlugins"
          :options="plugins"
          option-label="name"
          input-debounce="100"
          outlined
          use-input
          class="col"
          style="max-width: 400px"
        >
          <template v-slot:option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section avatar>
                <q-icon
                  :name="getConceptStyle('plugin').icon"
                  :color="getConceptStyle('plugin').color"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ scope.opt.name }}</q-item-label>
                <q-item-label caption
                  >Files: {{ scope.opt.files.length }} | Tasks:
                  {{ countTasks(scope.opt) }}</q-item-label
                >
              </q-item-section>
            </q-item>
          </template>

          <template v-slot:selected-item="scope">
            <div class="q-py-xs">
              <div
                class="row items-center q-px-sm no-wrap bg-white shadow-1"
                style="
                  border-radius: 4px;
                  border: 1px solid #eeeeee;
                  width: fit-content;
                "
              >
                <q-icon
                  :name="getConceptStyle('plugin').icon"
                  :color="getConceptStyle('plugin').color"
                  size="xs"
                />

                <q-chip
                  :color="getConceptStyle('plugin').color"
                  text-color="white"
                  size="sm"
                  outline
                  square
                  clickable
                  class="text-weight-bold no-border q-mx-none"
                >
                  <span
                    class="font-mono ellipsis"
                    style="font-size: 14px; font-weight: 500"
                  >
                    {{ scope.opt.name }}
                  </span>

                  <template v-if="!scope.opt.latestSnapshot">
                    <div
                      style="
                        height: 12px;
                        width: 1px;
                        background-color: #ddd;
                        margin: 0 6px;
                      "
                    ></div>

                    <q-badge
                      rounded
                      color="warning"
                      class="q-mr-xs"
                      style="padding: 2px"
                    >
                      <q-icon name="warning" color="white" size="10px" />
                    </q-badge>

                    <q-btn
                      flat
                      round
                      dense
                      size="xs"
                      color="red"
                      icon="sync"
                      @click.stop="syncPlugin(scope.opt.id)"
                    >
                      <q-tooltip>Sync to latest</q-tooltip>
                    </q-btn>
                  </template>
                </q-chip>
              </div>
            </div>
          </template>
        </q-select>
      </div>
      <q-select
        dense
        outlined
        v-model="selectedArtifactTask"
        :options="artifactTaskOptions"
        option-label="name"
        label="Artifact Task"
        class="q-mt-sm"
        style="width: fit-content"
        :disable="artifactTaskOptions.length === 0"
      >
        <template #before>
          <q-icon name="subdirectory_arrow_right" color="grey-7" />
        </template>

        <template v-slot:option="scope">
          <q-item v-bind="scope.itemProps">
            <q-item-section>
              <q-item-label class="text-weight-bold">{{
                scope.opt.name
              }}</q-item-label>

              <q-item-label caption v-if="scope.opt.outputParams?.length">
                <div class="row wrap q-mt-xs text-caption">
                  <span class="text-grey-12 text-weight-medium">Outputs:</span>
                  <div
                    v-for="(param, i) in scope.opt.outputParams"
                    :key="param.name"
                    class="row items-baseline no-wrap q-gutter-x-xs"
                  >
                    <span
                      class="text-grey-9"
                      style="border-bottom: 2px solid #ab47bc; line-height: 1.1"
                    >
                      {{ param.name }}
                    </span>
                    <span class="text-grey-7">:</span>
                    <span
                      class="text-grey-6 font-mono"
                      style="font-size: 0.9em"
                    >
                      {{ param.parameterType.name }}
                    </span>
                    <span
                      v-if="i < scope.opt.outputParams.length - 1"
                      class="text-grey-5 q-mr-xs"
                      >,</span
                    >
                  </div>
                </div>
              </q-item-label>
            </q-item-section>
          </q-item>
        </template>

        <template v-slot:selected-item="scope">
          <div v-if="scope.opt" class="column q-py-xs q-mt-xs">
            <BadgeIcon
              :label="scope.opt.name"
              :uppercase="false"
              type="task"
              :includeIcon="true"
              class="q-mb-sm q-pr-lg"
              ,
              style="width: fit-content"
              ;
            />

            <div
              class="row wrap items-center text-caption q-gutter-sm"
              style="line-height: 1.4"
            >
              <span class="text-grey-8 text-weight-bold">Outputs:</span>

              <template
                v-if="
                  scope.opt.outputParams && scope.opt.outputParams.length > 0
                "
              >
                <div
                  v-for="(p, i) in scope.opt.outputParams"
                  :key="p.name"
                  class="row items-baseline q-gutter-x-xs-mr-sm"
                >
                  <span
                    class="text-grey-9"
                    style="border-bottom: 2px solid #ab47bc; line-height: 1.2"
                  >
                    {{ p.name }}
                  </span>

                  <span class="text-grey-7 font-mono" style="font-size: 0.9em">
                    ({{ p.parameterType.name }})
                  </span>
                </div>
              </template>
              <span v-else class="text-grey-5 text-italic">None</span>
            </div>
          </div>
        </template>
      </q-select>

      <div
        v-if="artifactTaskOptions.length === 0 && !isLoading"
        class="text-caption text-negative q-mt-xs q-ml-lg"
      >
        The selected plugin has no files with artifact tasks. Please select
        another plugin.
      </div>
    </template>
  </KeyValueTable>

  <div class="row justify-end q-my-lg q-gutter-x-md">
    <q-btn outline color="primary" label="Cancel" @click="router.back()" />
    <q-btn @click="submit()" color="primary" label="Save Artifact" />
  </div>
</template>

<script setup>
import { onMounted, computed, ref, inject, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useLoginStore } from "@/stores/LoginStore.ts";
import * as api from "@/services/dataApi";
import * as notify from "../notify";

// Components
import PageTitle from "@/components/PageTitle.vue";
import KeyValueTable from "@/components/KeyValueTable.vue";
import ResourceName from "@/components/table/cells/ResourceName.vue";
import ParameterList from "@/components/table/cells/ParameterList.vue";
import BadgeIcon from "@/components/table/cells/BadgeIcon.vue"; 
import CellLongText from "@/components/table/cells/CellLongText.vue"; 
import { getConceptStyle } from "@/constants/tableStyles";

const store = useLoginStore();

const route = useRoute();
const router = useRouter();

const darkMode = inject("darkMode");

const isLoading = ref(true);

const showHistory = computed(() => {
  return store.showRightDrawer;
});

onMounted(async () => {
  await getArtifact();
  await getPluginSnapshot();
  await getPlugins("", (fn) => fn());
  if (route.query.snapshotId && !showHistory.value) {
    store.showRightDrawer = true;
  }
  isLoading.value = false;
});

const artifact = ref({
  id: "",
  description: "",
  createdOn: "",
  lastModifiedOn: "",
  snapshotCreatedOn: "",
  fileUrl: "",
  fileSize: 0,
  job: "",
  isDir: false,
  plugin: {},
  task: { outputParams: [] },
});

async function getArtifact() {
  try {
    const res = await api.getItem("artifacts", route.params.id);
    artifact.value = res.data;
  } catch (err) {
    console.warn(err);
  }
}

let ORIGINAL_PLUGIN_SNAPSHOT;

async function getPluginSnapshot() {
  try {
    const res = await api.getSnapshot(
      "plugins",
      artifact.value.task.pluginResourceId,
      artifact.value.task.pluginResourceSnapshotId,
    );
    console.log("plugin snap = ", res.data);
    artifact.value.plugin = res.data;
    ORIGINAL_PLUGIN_SNAPSHOT = JSON.parse(
      JSON.stringify(artifact.value.plugin),
    );
    const pluginFile = artifact.value.plugin.files.find(
      (file) => file.id === artifact.value.task.pluginFileResourceId,
    );
    pluginFile.tasks.artifacts.forEach((task) => {
      artifactTaskOptions.value.push(task);
    });
    selectedArtifactTask.value = artifactTaskOptions.value.find(
      (task) => task.id === artifact.value.task.id,
    );
  } catch (err) {
    console.warn(err);
  }
}

const artifactTaskOptions = ref([]);
const selectedArtifactTask = ref();

const plugins = ref([]);

async function getPlugins(val = "", update) {
  update(async () => {
    try {
      let res = await api.getData("plugins", {
        search: val,
        rowsPerPage: 0, 
        index: 0,
      });
      const originalPluginIndex = res.data.data.findIndex(
        (plugin) => plugin.id === ORIGINAL_PLUGIN_SNAPSHOT.id,
      );
      // replace latest plugin snapshot with original plugin snapshot from artifact
      res.data.data[originalPluginIndex] = ORIGINAL_PLUGIN_SNAPSHOT;
      plugins.value = res.data.data;
    } catch (err) {
      notify.error(err.response.data.message);
    }
  });
}

watch(
  () => artifact.value.plugin,
  (newVal, oldVal) => {
    // execute on plugin change, not on page load or turning off history
    if (!oldVal || !newVal) {
      return;
    }
    if (!showHistory.value) {
      // reset task dropdown
      selectedArtifactTask.value = "";
      artifactTaskOptions.value = [];
      newVal.files.forEach((file) => {
        file.tasks.artifacts.forEach((task) => {
          artifactTaskOptions.value.push(task);
        });
      });
    }
  },
);

function countTasks(plugin) {
  let numberOfTasks = 0;
  plugin.files.forEach((file) => {
    numberOfTasks += file.tasks.artifacts.length;
  });
  return numberOfTasks;
}

async function syncPlugin(pluginID) {
  try {
    const res = await api.getItem("plugins", pluginID);
    const latestPlugin = res.data;
    console.log("latest plugin = ", latestPlugin);
    // check if latest plugin still has artifact pluginFileResourceId
    const pluginHasFile = latestPlugin?.files?.find(
      (file) => file.id === artifact.value.task.pluginFileResourceId,
    );
    if (!pluginHasFile) {
      notify.error(
        `Latest plugin does not contain a file with id: ${artifact.value.task.pluginFileResourceId}.  Plugin cannot be synced.`,
      );
      return;
    }
    artifact.value.plugin = latestPlugin;
    notify.success(
      `Updated to latest snapshot of plugin: ${artifact.value.plugin.name}`,
    );

    const resFile = await api.getFile(
      pluginID,
      artifact.value.task.pluginFileResourceId,
    );
    artifactTaskOptions.value = [];
    selectedArtifactTask.value = "";
    let originalTaskFound = false;
    resFile.data.tasks.artifacts.forEach((task) => {
      artifactTaskOptions.value.push(task);
      if (task.id === artifact.value.task.id) {
        selectedArtifactTask.value = task;
        originalTaskFound = true;
      }
    });
    if (!originalTaskFound) {
      notify.info(
        `Task "${artifact.value.task.name}" not found in latest file, please select a new artifact task.`,
      );
    }
  } catch (err) {
    console.warn(err);
  }
}

const rows = computed(() => [
  { label: "ID", slot: "id" }, // Changed to slot
  { label: "Description", slot: "description" },
  {
    label: "Resource Created On",
    value: formatDate(artifact.value?.createdOn),
  },
  {
    label: "Resource Last Modified On",
    value: formatDate(artifact.value?.lastModifiedOn),
  },
  {
    label: "Snapshot Timestamp",
    value: formatDate(artifact.value?.snapshotCreatedOn),
  },
  {
    label: "Download",
    slot: "fileUrl",
    props: { fileUrl: artifact.value?.fileUrl },
  },
  { label: "File Size", value: prettyBytes(artifact.value?.fileSize) }, // Simple value is fine here
  { label: "Job ID", slot: "job" },
  { label: "Is Directory", value: artifact.value?.isDir ? "Yes" : "No" },
  {
    label: "Plugin",
    slot: "plugin",
    props: { plugin: artifact.value?.plugin },
  },
]);

function formatDate(dateString) {
  const options = {
    year: "2-digit",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  };
  return new Date(dateString).toLocaleString("en-US", options);
}

async function submit() {
  try {
    const res = await api.updateItem("artifacts", route.params.id, {
      description: artifact.value.description,
      pluginSnapshotId: artifact.value.plugin.snapshot,
      taskId: selectedArtifactTask.value.id,
    });
    notify.success(`Successfully updated artifact '${route.params.id}'`);
    router.push(`/artifacts`);
  } catch (err) {
    notify.error(err.response.data.message);
  }
}

watch(
  () => store.selectedSnapshot,
  async (newVal) => {
    isLoading.value = true;
    if (newVal) {
      artifact.value = newVal;
      await getPluginSnapshot();
    } else {
      await getArtifact();
      await getPluginSnapshot();
      await getPlugins("", (fn) => fn());
    }
    isLoading.value = false;
  },
);

function prettyBytes(num) {
  if (typeof num !== "number" || isNaN(num)) {
    return "N/A";
  }
  const neg = num < 0;
  num = Math.abs(num);
  const units = ["Bytes", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
  if (num < 1) return (neg ? "-" : "") + num + " B";

  const exponent = Math.min(Math.floor(Math.log10(num) / 3), units.length - 1);

  const value = (num / Math.pow(1000, exponent)).toFixed(2);
  return (neg ? "-" : "") + value + " " + units[exponent];
}
</script>
