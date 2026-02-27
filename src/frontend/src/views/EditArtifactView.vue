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


  <div class="row q-gutter-xl q-mt-md">
    <div :class="`${isLarge ? 'col-12' : 'col-4'}`">
      <h2 class="q-mt-none text-h6">Details</h2>

      <KeyValueTable 
        :rows="rows" 
        :disabled="showHistory"
        firstColumnMinWidth="205px"
        :secondColumnFullWidth="isLarge || !artifact.isDir ? false : true"
      >
        <template #id>
          <ResourceName conceptType="artifact" :text="'ID: #' + artifact.id" includeIcon="true" />
        </template>

        <template #description>
          <div class="row items-center justify-start">
            <CellLongText :text="artifact.description" max-width="800px" class="col-auto" />
            <q-btn icon="edit" round size="sm" color="primary" flat class="q-ml-sm">
              <q-tooltip>Edit Description</q-tooltip>
            </q-btn>
            <q-popup-edit v-model="artifact.description" auto-save v-slot="scope">
              <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" label="Description" />
            </q-popup-edit>
          </div>
        </template>

        <template #fileUrl="{ fileUrl }">
          <q-btn
            @click="downloadFile(artifact.fileUrl, artifact.artifactUri.split('/').pop(), 'artifact')"
            label="Download Artifact"
            color="primary"
            icon="download"
            size="sm"
            class="q-my-sm q-py-sm"
            :loading="isDownloadingArtifact"
          />
        </template>

        <template #fileSize>
          {{ prettyBytes(artifact.fileSize) }}
        </template>

        <template #job>
          <RouterLink :to="`/jobs/${artifact?.job}`" style="text-decoration: none">
            <BadgeIcon type="job" :label="artifact.job" :showIcon="true", :clickable="true" />
          </RouterLink>
        </template>

        <template #plugin="{ plugin = {} }">
          <div class="column">
            <div v-if="Object.keys(plugin).length === 0 && !isLoading" class="text-red q-mb-xs">
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
                    <q-icon :name="getConceptStyle('plugin').icon" :color="getConceptStyle('plugin').color" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>{{ scope.opt.name }}</q-item-label>
                    <q-item-label caption>Files: {{ scope.opt.files.length }} | Tasks: {{ countTasks(scope.opt) }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>

              <template v-slot:selected-item="scope">
                <div class="q-py-xs">
                  <div class="row items-center q-px-sm no-wrap bg-white shadow-1" style="border-radius: 4px; border: 1px solid #eeeeee; width: fit-content;">
                    <q-icon :name="getConceptStyle('plugin').icon" :color="getConceptStyle('plugin').color" size="xs" />
                    <q-chip :color="getConceptStyle('plugin').color" text-color="white" size="sm" outline square clickable class="text-weight-bold no-border q-mx-none">
                      <span class="font-mono ellipsis" style="font-size: 14px; font-weight: 500">
                        {{ scope.opt.name }}
                      </span>
                      <template v-if="!scope.opt.latestSnapshot">
                        <div style="height: 12px; width: 1px; background-color: #ddd; margin: 0 6px;"></div>
                        <q-badge rounded color="warning" class="q-mr-xs" style="padding: 2px">
                          <q-icon name="warning" color="white" size="10px" />
                        </q-badge>
                        <q-btn flat round dense size="xs" color="red" icon="sync" @click.stop="syncPlugin(scope.opt.id)">
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
                  <q-item-label class="text-weight-bold">{{ scope.opt.name }}</q-item-label>
                  <q-item-label caption v-if="scope.opt.outputParams?.length">
                    <div class="row wrap q-mt-xs text-caption">
                      <span class="text-grey-8 text-weight-medium q-mr-xs">Outputs:</span>
                      <div v-for="(param, i) in scope.opt.outputParams" :key="param.name" class="row items-baseline no-wrap q-gutter-x-xs">
                        <span class="text-grey-9" style="border-bottom: 2px solid #ab47bc; line-height: 1.1">{{ param.name }}</span>
                        <span class="text-grey-7">:</span>
                        <span class="text-grey-6 font-mono" style="font-size: 0.9em">{{ param.parameterType.name }}</span>
                        <span v-if="i < scope.opt.outputParams.length - 1" class="text-grey-5 q-mr-xs">,</span>
                      </div>
                    </div>
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template v-slot:selected-item="scope">
              <div v-if="scope.opt" class="column q-py-xs q-mt-xs">
                <BadgeIcon :label="scope.opt.name" :uppercase="false" type="task" :includeIcon="true" class="q-mb-sm q-pr-lg" style="width: fit-content" />
                <div class="row wrap items-center text-caption q-gutter-sm" style="line-height: 1.4">
                  <span class="text-grey-8 text-weight-bold">Outputs:</span>
                  <template v-if="scope.opt.outputParams && scope.opt.outputParams.length > 0">
                    <div v-for="(p, i) in scope.opt.outputParams" :key="p.name" class="row items-baseline q-gutter-x-xs q-mr-sm">
                      <span class="text-grey-9" style="border-bottom: 2px solid #ab47bc; line-height: 1.2">{{ p.name }}</span>
                      <span class="text-grey-7 font-mono" style="font-size: 0.9em">({{ p.parameterType.name }})</span>
                    </div>
                  </template>
                  <span v-else class="text-grey-5 text-italic">None</span>
                </div>
              </div>
            </template>
          </q-select>

          <div v-if="artifactTaskOptions.length === 0 && !isLoading" class="text-caption text-negative q-mt-xs q-ml-lg">
            The selected plugin has no files with artifact tasks. Please select another plugin.
          </div>
        </template>
      </KeyValueTable>
      
      <div class="row justify-start q-my-lg q-gutter-x-md">
        <q-btn outline color="primary" label="Cancel" @click="store.initialPage ? router.push('/artifacts') : router.back()" />
        <q-btn @click="submit()" color="primary" label="Save Artifact" :disable="store.showRightDrawer" />
      </div>
    </div>

    <div :class="isLarge ? 'col-6' : 'col-3'" class="column" v-if="artifact.isDir">
      <h2 class="q-mt-none text-h6">Directory</h2>
      <q-card flat class="col q-py-sm" style="border: 1px solid #cecece;">
        <q-card-section class="row justify-between q-pt-sm">
          <q-btn @click="downloadFile(selectedNode?.fileUrl, selectedNode?.label)" label="Download File" color="primary" icon="download" :disable="!selectedNode || selectedNode.isDir" :loading="isDownloadingFile" />
          <q-input v-model="filter" debounce="300" dense placeholder="Search" outlined clearable @clear="selectedNode = null">
            <template #append><q-icon name="search" /></template>
          </q-input>
        </q-card-section>
        <q-separator />
        <q-card-section style="max-height: 65vh; overflow-y: auto" class="q-pl-md q-pt-sm">
          <q-tree :nodes="nodes" node-key="relativePath" v-model:expanded="expandedKeys" selected-color="primary" dense :filter="filter" :filter-method="myFilterMethod">
            <template v-slot:default-header="prop">
              <q-item clickable style="width: 100%" dense class="q-pa-none" @click="handleSelect(prop.node)" :active="selectedNode === prop.node" :active-class="`${$q.dark.isActive ? 'bg-deep-purple-10 text-white' : 'bg-grey-4 text-black'}`">
                <q-item-section avatar><q-icon :name="prop.node.icon" /></q-item-section>
                <q-item-section>
                  <q-item-label>
                    {{ prop.node.label }}
                    <span v-if="prop.node.isFile" class="text-caption float-right q-pr-sm">{{ prettyBytes(prop.node.fileSize) }}</span>
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-tree>
        </q-card-section>
      </q-card>
    </div>

    <div class="col column" style="max-width: 100%;">
      <h2 class="q-mt-none text-h6">File Preview</h2>
      <q-card class="col column shadow-1" style="border: 1px solid #cecece; border-radius: 6px;">
        
        <q-card-section 
          class="bg-grey-1 row items-center justify-between q-py-sm" 
          style="border-bottom: 1px solid #cecece; min-height: 60px;"
        >
          <div v-if="!selectedNode || selectedNode.isDir" class="text-grey-6 text-italic flex items-center q-gutter-x-sm">
            <q-icon name="sym_o_visibility_off" size="sm" />
            <span>No preview selected</span>
          </div>
          
          <div v-else class="row items-center q-gutter-x-sm">
            <q-icon name="sym_o_description" color="primary" size="sm"  />
            <span class="text-weight-bold text-blue-grey-9" style="font-size: 1.1rem; letter-spacing: 0.5px;">
              {{ selectedNode.label }}
            </span>
            <q-chip 
              v-if="preview.ext"  
              size="sm" 
              color="blue-grey-2" 
              text-color="blue-grey-9" 
              class="text-weight-bold text-uppercase q-ml-sm"
            >
              {{ preview.ext }}
            </q-chip>
          </div>
          
          <q-toggle 
            v-if="preview.kind === 'image'" 
            color="primary" 
            label="Full Width" 
            v-model="imageFullWidth" 
            left-label 
            dense 
          />
        </q-card-section>

        <q-card-section class="q-pa-none col flex column bg-white" style="max-height: 65vh; overflow-y: auto;">
          
          <div v-if="!selectedNode || selectedNode.isDir" class="flex flex-center column q-pa-xl text-grey-5 col">
            <q-icon name="sym_o_file_present" size="4rem" class="q-mb-md" style="opacity: 0.5" />
            <div class="text-h6 text-weight-regular">Select a file to preview</div>
          </div>

          <div v-else-if="preview.loading" class="flex flex-center column q-pa-xl text-primary col">
            <q-spinner size="3rem" class="q-mb-md" />
            <div class="text-subtitle1">Loading file preview...</div>
          </div>

          <div v-else-if="preview.error" class="flex flex-center column q-pa-xl text-negative col">
            <q-icon name="error_outline" size="3rem" class="q-mb-md" />
            <div class="text-subtitle1 text-center">{{ preview.error }}</div>
          </div>

          <div v-else class="q-pa-md col">
            
            <div v-if="preview.ext === 'json' || preview.ext === 'yaml'" class="shadow-1 rounded-borders overflow-hidden" style="border: 1px solid #e0e0e0;">
              <CodeEditor v-model="preview.text" language="yaml" :readOnly="true" />
            </div>

            <pre 
              v-else-if="preview.kind === 'text'" 
              class="q-pa-md rounded-borders text-body2 font-mono text-blue-grey-9 bg-grey-2" 
              style="white-space: pre-wrap; word-break: break-word; border: 1px solid #e0e0e0; margin: 0;"
            >{{ preview.text }}</pre>

            <div v-else-if="preview.kind === 'image'" class="flex flex-center bg-grey-2 rounded-borders q-pa-sm" style="border: 1px solid #e0e0e0;">
              <img 
                :src="preview.objectUrl" 
                class="rounded-borders shadow-1" 
                style="max-width: 100%; height: auto; transition: width 0.3s ease;" 
                :style="{ width: imageFullWidth ? '100%' : 'auto' }" 
              />
            </div>

            <iframe 
              v-else-if="preview.kind === 'pdf'" 
              :src="preview.objectUrl" 
              class="rounded-borders"
              style="width: 100%; height: 60vh; border: 1px solid #e0e0e0;" 
            />

            <div v-else class="flex flex-center column q-pa-xl text-grey-6 col">
              <q-icon name="sym_o_visibility_off" size="3rem" class="q-mb-md" />
              <div class="text-subtitle1">No preview available for this file type.</div>
              <div class="text-caption">Use the Download Artifact button above to view Artifact.</div>
            </div>
          </div>
          
        </q-card-section>
      </q-card>
    </div>
  </div>
</template>



<script setup>

import { onMounted, computed, ref, inject, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useLoginStore } from "@/stores/LoginStore.ts";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import {useQuasar} from "quasar";

// Components
import PageTitle from "@/components/PageTitle.vue";
import KeyValueTable from "@/components/KeyValueTable.vue";
import ResourceName from "@/components/table/cells/ResourceName.vue";
import ParameterList from "@/components/table/cells/ParameterList.vue";
import BadgeIcon from "@/components/table/cells/BadgeIcon.vue"; 
import CellLongText from "@/components/table/cells/CellLongText.vue"; 
import { getConceptStyle } from "@/constants/tableStyles";
import CodeEditor from '@/components/CodeEditor.vue'

const store = useLoginStore();

const $q = useQuasar();

const isMedium = inject("isMedium");
const isLarge = inject("isLarge");
const isMobile = inject("isMobile");
const darkMode = inject("darkMode");
const route = useRoute();
const router = useRouter();
const isLoading = ref(true);

const showHistory = computed(() => {
  return store.showRightDrawer;
});

onMounted(async () => {
  await getArtifact();
  if (artifact.value.isDir) {
    await getArtifactFiles();
  } else {
    await getSingularFile()
  }
  await getPluginSnapshot();
  await getPlugins("", (fn) => fn());
  if (route.query.snapshotId && !showHistory.value) {
    store.showRightDrawer = true;
  }
  isLoading.value = false;
});

const artifact = ref({
  description: "",
  task: {
    outputParams: [],
  },

  id: '',
  createdOn: '',
  lastModifiedOn: '',
  snapshotCreatedOn: '',
  fileUrl: '',
  fileSize: 0,
  job: "",
  isDir: false,
  plugin: {},
})

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
      artifact.value.task.pluginResourceSnapshotId
    );
    console.log("plugin snap = ", res.data);
    artifact.value.plugin = res.data;
    ORIGINAL_PLUGIN_SNAPSHOT = JSON.parse(
      JSON.stringify(artifact.value.plugin)
    );
    const pluginFile = artifact.value.plugin.files.find(
      (file) => file.id === artifact.value.task.pluginFileResourceId,
    );
    pluginFile.tasks.artifacts.forEach((task) => {
      artifactTaskOptions.value.push(task);
    });
    selectedArtifactTask.value = artifactTaskOptions.value.find(
      (task) => task.id === artifact.value.task.id
    );
  } catch (err) {
    console.warn(err);
  }
}

const artifactTaskOptions = ref([]);
const selectedArtifactTask = ref();

const plugins = ref([]);

async function getPlugins(val = "", update) {
  try {

    let res = await api.getData("plugins", {
      search: val,
      rowsPerPage: 0, // get all
      index: 0,
    });

    update(() => {
      if (res?.data?.data) {
        if (ORIGINAL_PLUGIN_SNAPSHOT) {
          const originalPluginIndex = res.data.data.findIndex(
            (plugin) => plugin.id === ORIGINAL_PLUGIN_SNAPSHOT.id
          );
          
          // Prevent mutating index -1
          if (originalPluginIndex !== -1) {
            res.data.data[originalPluginIndex] = ORIGINAL_PLUGIN_SNAPSHOT;
          }
        }
        plugins.value = res.data.data;
      }
    });
  } catch (err) {
    update(() => {
      plugins.value = [];
    });
    notify.error(err.response?.data?.message || err.message);
  }
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
  }
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
      (file) => file.id === artifact.value.task.pluginFileResourceId
    );
    if (!pluginHasFile) {
      notify.error(
        `Latest plugin does not contain a file with id: ${artifact.value.task.pluginFileResourceId}.  Plugin cannot be synced.`
      );
      return;
    }
    artifact.value.plugin = latestPlugin;
    notify.success(
      `Updated to latest snapshot of plugin: ${artifact.value.plugin.name}`
    );

    // reload task dropdown with tasks from latest file
    const resFile = await api.getFile(
      pluginID,
      artifact.value.task.pluginFileResourceId
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
        `Task "${artifact.value.task.name}" not found in latest file, please select a new artifact task.`
      );
    }
  } catch (err) {
    console.warn(err);
  }
}

const rows = computed(() => [
  { 
    label: "Artifact ID", 
    slot: "id" 
  },
  {
    label: "Description",
    slot: "description",
    props: { description: artifact.value?.description },
  },
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
  { label: "fileSize", slot: "fileSize" },
  { label: "Job ID", slot: "job" },
  { label: "isDir", value: artifact.value?.isDir },
  {
    label: "Plugin for Download",
    slot: "plugin",
    props: { plugin: artifact.value?.plugin },
  },
  {
    label: "Download",
    slot: "fileUrl",
    props: { fileUrl: artifact.value?.fileUrl },
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
  }
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

async function getSingularFile() {
  selectedNode.value = {
    isDir: false,
    fileUrl: artifact.value.fileUrl,
    relativePath: artifact.value.artifactUri,
    label: artifact.value.artifactUri.split('/').pop()
  }
}

async function getArtifactFiles() {
  try {
    const res = await api.getArtifactFiles(route.params.id);
    files.value = res.data;
    console.log("files = ", files.value);
    processFiles();
  } catch (err) {
    console.warn(err);
  }
}

const files = ref([]);
const nodes = ref([]);
const expandedKeys = ref([]);
const selectedNode = ref();
const filter = ref("");

const relativePaths = computed(() => {
  const walk = (items) => {
    return items.flatMap((item) => [
      item.relativePath,
      ...(Array.isArray(item.children) ? walk(item.children) : []),
    ]);
  };
  return walk(nodes.value);
});

function getExpandKeysForFilter(nodes, filter) {
  const f = (filter || "").toLowerCase().trim();
  if (!f) return ["/"];

  const keys = new Set(["/"]);

  const matches = (node) => {
    const label = (node.label || "").toLowerCase();
    const path = (node.relativePath || "").toLowerCase();
    return label.includes(f);
  };

  const walk = (items, ancestorKeys = []) => {
    for (const node of items || []) {
      const nextAncestors = [...ancestorKeys];

      // Only directories should be expanded 
      if (node.isDir && node.relativePath) {
        nextAncestors.push(node.relativePath);
      }

      if (matches(node)) {
        for (const k of ancestorKeys) keys.add(k);
      }

      if (Array.isArray(node.children) && node.children.length) {
        walk(node.children, nextAncestors);
      }
    }
  };

  walk(nodes);
  return Array.from(keys);
}

watch(filter, (newVal) => {
  expandedKeys.value = getExpandKeysForFilter(nodes.value, newVal);
  if (!nodeMatchesFilter(selectedNode.value, newVal) || newVal === "") {
    // clear selectedNode if clearing filter or not in filter results
    selectedNode.value = null;
  }
});

function nodeMatchesFilter(node, filter) {
  if (!filter) return true;
  const f = filter.toLowerCase();
  const labelMatch = (node?.label || "").toLowerCase().includes(f);
  return labelMatch;
}

function processFiles() {
  // Reset root node
  nodes.value = [
    {
      label: "Artifact Directory",
      icon: "sym_o_folder",
      children: [],
      isDir: true,
      relativePath: "/", // root
    },
  ];

  const rootChildren = nodes.value[0].children;

  files.value.forEach((file) => {
    const parts = file.relativePath.split("/"); 

    let currentChildren = rootChildren;
    let currentPath = ""; // will build up like "4958", then "4958/0000.shard", etc.

    parts.forEach((part, index) => {
      const isLast = index === parts.length - 1;

      // Build the path up to this segment
      currentPath = currentPath ? `${currentPath}/${part}` : part;

      // Look for an existing node with this relativePath at the current level
      let existing = currentChildren.find(
        (node) => node.relativePath === currentPath
      );

      if (!existing) {
        if (isLast) {
          // This is a file
          existing = {
            label: part,
            icon: "sym_o_draft",
            isFile: true,
            ...file,
          };
        } else {
          // This is a directory
          existing = {
            label: part,
            icon: "sym_o_folder",
            children: [],
            isDir: true,
            relativePath: currentPath, // e.g. "4958/0000.shard"
          };
        }

        currentChildren.push(existing);
      }

      // If it's not the last part, drill down into this folder's children
      if (!isLast) {
        if (!existing.children) {
          existing.children = [];
        }
        currentChildren = existing.children;
      }
    });
  });

  // auto-expand root
  expandedKeys.value = ["/"];
  console.log("nodes = ", nodes.value);
}

function handleSelect(node) {
  if (selectedNode.value?.relativePath === node.relativePath) {
    selectedNode.value = null;
  } else {
    selectedNode.value = node;
  }
}

function myFilterMethod(node, filter) {
  if (!filter) return true;
  const f = filter.toLowerCase();

  const labelMatch = node.label?.toLowerCase().includes(f);
  const pathMatch = node.relativePath?.toLowerCase().includes(f);

  return labelMatch || pathMatch;
}

const preview = ref({
  loading: false,
  error: "",
  kind: "", // 'text' | 'image' | 'pdf' | 'none'
  ext: "",
  text: "",
  objectUrl: "", // for blob previews
});

function resetPreview() {
  preview.value.loading = false;
  preview.value.error = "";
  preview.value.kind = "";
  preview.value.ext = "";
  preview.value.text = "";
  if (preview.value.objectUrl) {
    URL.revokeObjectURL(preview.value.objectUrl);
    preview.value.objectUrl = "";
  }
}

function getExt(path = "") {
  const name = path.split("?")[0];
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : "";
}

watch(selectedNode, async (node) => {
  resetPreview();
  if (!node || node.isDir) return;
  await loadPreview(node);
});

const MAX_PREVIEW_BYTES = 10 * 1024 * 1024; // 10 MB

async function getRemoteSize(url) {
  if(artifact.value.fileSize) {
    // if single file artifact, use already provided fileSize
    return artifact.value.fileSize
  }
  const head = await fetch(url, { method: "HEAD", credentials: "include" });
  if (!head.ok) return null;

  const len = head.headers.get("content-length");
  return len ? Number(len) : null;
}

async function loadPreview(node) {
  preview.value.loading = true;
  preview.value.error = "";

  try {
    const size = await getRemoteSize(node.fileUrl);

    // If server provides size and it's too big, skip preview
    if(size != null && size > MAX_PREVIEW_BYTES) {
      preview.value.kind = "none";
      preview.value.error = `File is ${(size / (1024 * 1024)).toFixed(1)} MB. Preview limit is 10 MB. Please download instead.`;
      preview.value.loading = false
      return;
    }
  } catch(err) {
    console.warn(err)
  }

  try {
    const ext = getExt(node.relativePath || node.label || "");
    preview.value.ext = ext
    const isText = ["json", "txt", "log", "yaml", "yml", "csv", "md"].includes(
      ext
    );

    const isImage = ["png", "jpg", "jpeg", "gif", "webp", "svg"].includes(ext);

    const isPdf = ext === "pdf";

    if (isText) {
      const res = await fetch(node.fileUrl, { credentials: "include" });
      if (!res.ok)
        throw new Error(`Preview failed: ${res.status} ${res.statusText}`);

      preview.value.text = await res.text();

      // Pretty JSON if possible
      if (ext === "json") {
        try {
          preview.value.text = JSON.stringify(
            JSON.parse(preview.value.text),
            null,
            2
          );
        } catch {
          // keep as-is
        }
      }

      preview.value.kind = "text";
      return;
    }

    if (isImage || isPdf) {
      const res = await fetch(node.fileUrl, { credentials: "include" });
      if (!res.ok)
        throw new Error(`Preview failed: ${res.status} ${res.statusText}`);

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);

      preview.value.objectUrl = url;
      preview.value.kind = isPdf ? "pdf" : "image";
      return;
    }

    preview.value.kind = "none";
  } catch (e) {
    preview.value.error = e?.message ?? String(e);
  } finally {
    preview.value.loading = false;
  }
}

const isDownloadingArtifact = ref(false);
const isDownloadingFile = ref(false);

async function downloadFile(url, filename, type = null) {
  try {
    if (type === "artifact") {
      isDownloadingArtifact.value = true;
    } else {
      isDownloadingFile.value = true;
    }
    await api.downloadFile(url, filename);
    notify.success(`Successfully downloaded file: ${filename}`);
  } catch (err) {
    console.warn(err);
    notify.error(`Error downloading file ${filename}`);
  } finally {
    if (type === "artifact") {
      isDownloadingArtifact.value = false;
    } else {
      isDownloadingFile.value = false;
    }
  }
}

const imageFullWidth = ref(false)

</script>
