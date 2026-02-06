<template>
  <div class="column" style="min-height: calc(100vh - 100px)">
    <div class="row items-center justify-between">
      <PageTitle
        title="Jobs"
        :subtitle="`Job ${$route.params.id} Dashboard`"
        conceptType="job"
      />
      <q-btn
        color="negative"
        icon="sym_o_delete"
        label="Delete Job"
        outline
        @click="showDeleteDialog = true"
      />
    </div>

    <div class="q-my-lg">
      <q-tabs
        v-model="tab"
        indicator-color="primary"
        dense
        no-caps
        align="left"
        class="text-grey-8"
        active-color="primary"
      >
        <q-tab name="overview" label="Overview" />
        <q-tab
          name="logs"
          :label="`Logs ${logTotalNumber ? `(${logTotalNumber})` : ''}`"
        />
        <q-tab
          name="metrics"
          :label="`Metrics ${metrics.length ? `(${metrics.length})` : ''}`"
        />
        <q-tab
          name="artifacts"
          :label="`Output Artifacts ${job?.artifacts.length ? `(${job?.artifacts.length})` : ''}`"
        />
      </q-tabs>
      <q-separator />
    </div>

    <div v-if="tab === 'overview'" class="row q-col-gutter-lg">
      <div class="col-12 col-md-6">
        <h2 class="text-h6 q-mt-none">Details</h2>

        <KeyValueTable :rows="overviewRows">
          <template #id>
            <ResourceName
              :text="job?.id"
              conceptType="job"
              :includeIcon="true"
            />
          </template>

          <template #description>
            <CellLongText :text="job?.description" :maxLength="100" />
          </template>

          <template #status>
            <JobStatus :status="job?.status" />
          </template>

          <template #experiment>
            <RouterLink
              v-if="job?.experiment"
              :to="`/experiments/${job.experiment.id}?snapshotId=${job.experiment.snapshotId}`"
              style="text-decoration: none"
            >
              <BadgeIcon
                type="experiment"
                :label="job.experiment.name"
                :showIcon="true"
              />
            </RouterLink>
            <span v-else>-</span>
          </template>

          <template #entrypoint>
            <RouterLink
              v-if="job?.entrypoint"
              :to="`/entrypoints/${job.entrypoint.id}?snapshotId=${job.entrypoint.snapshotId}`"
              style="text-decoration: none"
            >
              <BadgeIcon
                type="entrypoint"
                :label="job.entrypoint.name"
                :showIcon="true"
              />
            </RouterLink>
            <span v-else>-</span>
          </template>

          <template #queue>
            <BadgeIcon
              v-if="job?.queue"
              type="queue"
              :label="job.queue.name"
              :showIcon="true"
            />
            <span v-else>-</span>
          </template>

          <template #tags>
            <TagList
              :tags="job?.tags"
              :row="job"
              @add="showTagsDialog = true"
            />
          </template>
        </KeyValueTable>

        <q-btn
          color="primary"
          icon="replay"
          label="Re-Run Job"
          class="q-mt-lg"
          @click="reRunJob()"
        />
      </div>

      <div class="col-12 col-md-6 column q-gutter-y-lg">
        <div>
          <h2 class="text-h6 q-mt-none">Entrypoint Parameters</h2>
          <TableComponent
            :columns="parametersColumns"
            :rows="paramRows"
            rowKey="parameter"
            :hideCreateBtn="true"
            :hideDeleteBtn="true"
            :hideSearch="true"
            :hideBottom="true"
            class="q-mt-none"
          />
        </div>

        <div>
          <h2 class="text-h6 q-mt-none">Artifact Parameters</h2>
          <TableComponent
            :columns="artifactsUsedColumns"
            :rows="artifactsUsed"
            rowKey="id"
            :hideCreateBtn="true"
            :hideDeleteBtn="true"
            :hideSearch="true"
            :hideBottom="true"
            class="q-mt-none"
            @edit="
              (row) =>
                router.push(`/artifacts/${row.id}?snapshotId=${row.snapshotId}`)
            "
          >
            <template #body-cell-id="props">
              <RouterLink
                :to="`/artifacts/${props.row.id}`"
                style="text-decoration: none"
              >
                <BadgeIcon
                  type="artifact"
                  :label="props.row.id"
                  :showIcon="true"
                />
              </RouterLink>
            </template>
          </TableComponent>
        </div>
      </div>
    </div>

    <div v-if="tab === 'logs'">
      <TableComponent
        title="Job Logs"
        :columns="logColumns"
        :rows="jobLogs"
        @request="getLogs"
        :hideDeleteBtn="true"
        :disableSelect="true"
        :hideCreateBtn="true"
        ref="tableRef"
        :loading="isLoading"
      >
        <template #body-cell-message="props">
          <CodeEditor
            v-model="props.row.message"
            :readOnly="true"
            language="text"
            maxHeight="215px"
            class="code-cell"
          />
        </template>

        <template #jobLogSlot>
          <div class="row items-center q-gutter-x-md">
            <q-select
              v-if="job?.status !== 'finished' && job?.status !== 'failed'"
              v-model="selectedFrequency"
              label="Refresh"
              :options="refreshOptions"
              emit-value
              map-options
              dense
              outlined
              style="width: 140px"
            />

            <q-select
              label="Severity"
              v-model="selectedSeverity"
              :options="['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']"
              multiple
              outlined
              dense
              use-chips
              style="min-width: 250px; max-width: 400px"
            />
          </div>
        </template>
      </TableComponent>
    </div>

    <div v-if="tab === 'metrics'" class="row q-col-gutter-lg">
      <div class="col-12">
        <TableComponent
          title="Job Metrics (Latest)"
          :columns="metricColumns"
          :rows="metrics"
          rowKey="name"
          :hideCreateBtn="true"
          :hideDeleteBtn="true"
          v-model:filter="filter"
        />

        <div class="row items-center q-mt-md justify-between">
          <q-input
            v-model="filter"
            debounce="300"
            dense
            outlined
            placeholder="Search metric charts..."
            class="col-grow"
            clearable
            style="max-width: 400px"
          >
            <template #prepend><q-icon name="search" /></template>
          </q-input>

          <q-btn
            label="Refresh Charts"
            color="primary"
            icon="refresh"
            outline
            @click="loadAllMetricHistories"
          />
        </div>
      </div>

      <div
        :class="graphClass"
        v-for="metric in filteredMetrics"
        :key="metric.name"
      >
        <PlotlyGraph
          :data="metric.data"
          :title="metric.name"
          :graphClass="graphClass"
        />
      </div>

      <div
        v-if="filteredMetrics.length === 0"
        class="col-12 row justify-center q-mt-xl text-grey"
      >
        <div class="column items-center">
          <q-icon name="bar_chart" size="4em" color="grey-4" />
          <div class="text-h6 text-grey-5 q-mt-sm">No metrics available</div>
        </div>
      </div>
    </div>

    <div v-if="tab === 'artifacts'">
      <JobArtifactsTable
        v-if="job?.artifacts"
        :artifactIds="job.artifacts.map((a) => a.id)"
        style="margin-top: 0px"
      />
    </div>

    <q-space />

    <div class="row justify-end q-mt-lg">
      <q-btn
        outline
        label="Return to Jobs"
        @click="router.back()"
        color="primary"
      />
    </div>
  </div>

  <AssignTagsDialog
    v-model="showTagsDialog"
    :editObj="job"
    type="jobs"
    @refreshTable="getJob"
  />
  <DeleteDialog
    v-model="showDeleteDialog"
    @submit="deleteJob"
    type="Job"
    :name="job?.description || `Job ID ${job?.id}`"
  />
</template>

<script setup>
import { ref, computed, inject, watch, nextTick, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import * as api from "@/services/dataApi";
import * as notify from "../notify";

// Components
import PageTitle from "@/components/PageTitle.vue";
import KeyValueTable from "@/components/KeyValueTable.vue";
import TableComponent from "@/components/table/TableComponent.vue";
import JobStatus from "@/components/JobStatus.vue";
import CodeEditor from "@/components/CodeEditor.vue";
import PlotlyGraph from "@/components/PlotlyGraph.vue";
import JobArtifactsTable from "@/components/JobArtifactsTable.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import AssignTagsDialog from "@/dialogs/AssignTagsDialog.vue";

// Table Cell Subcomponents
import ResourceName from "@/components/table/cells/ResourceName.vue";
import BadgeIcon from "@/components/table/cells/BadgeIcon.vue";
import CellLongText from "@/components/table/cells/CellLongText.vue";
import TagList from "@/components/table/cells/TagList.vue";
import ParameterList from "@/components/table/cells/ParameterList.vue";

const route = useRoute();
const router = useRouter();
const isMedium = inject("isMedium");
const isMobile = inject("isMobile");

const tab = ref("overview");
const job = ref(null); 
const showTagsDialog = ref(false);
const showDeleteDialog = ref(false);
const isLoading = ref(false);
const metrics = ref([]);
const metricsData = ref([]);
const jobLogs = ref([]);
const logTotalNumber = ref(0);
const tableRef = ref(null);
const filter = ref("");

// Columns 
const parametersColumns = [
  {
    name: "parameter",
    label: "Parameter",
    align: "left",
    field: "parameter",
    sortable: true,
  },
  {
    name: "value",
    label: "Value",
    align: "left",
    field: "value",
    sortable: false,
  },
];

const artifactsUsedColumns = [
  {
    name: "id",
    label: "ID",
    align: "left",
    field: "id",
    styleType: "icon-badge",
    conceptType: "artifact",
    showIcon: true,
    sortable: true,
  },
  {
    name: "snapshotId",
    label: "Snapshot ID",
    align: "left",
    field: "snapshotId",
    sortable: false,
  },
  {
    name: "artifactParamName",
    label: "Parameter Name",
    align: "left",
    field: "artifactParamName",
    sortable: true,
  },
];

const metricColumns = [
  {
    name: "metric",
    label: "Metric",
    align: "left",
    field: "name",
    sortable: true,
  },
  {
    name: "value",
    label: "Value",
    align: "left",
    field: "value",
    sortable: false,
  },
];

const logColumns = [
  {
    name: "severity",
    label: "Severity",
    align: "left",
    field: "severity",
    sortable: true,
    classes: "vertical-top",
    style: "width: 100px",
  },
  {
    name: "logger_name",
    label: "Logger Name",
    align: "left",
    field: "loggerName",
    sortable: true,
    classes: "vertical-top",
    style: "width: 150px",
  },
  {
    name: "created_on",
    label: "Time",
    align: "left",
    field: "createdOn",
    styleType: "date",
    sortable: true,
    classes: "vertical-top",
    style: "width: 180px",
  },
  {
    name: "message",
    label: "Message",
    align: "left",
    field: "message",
    sortable: false,
  },
];

// --- Computed Rows for Overview ---
const overviewRows = computed(() => [
  { label: "ID", slot: "id" },
  { label: "Description", slot: "description" },
  { label: "Status", slot: "status" },
  { label: "Created On", value: formatDate(job.value?.createdOn) },
  { label: "Created By", value: job.value?.user?.username || "System" },
  { label: "Experiment", slot: "experiment" },
  { label: "Entrypoint", slot: "entrypoint" },
  { label: "Queue", slot: "queue" },
  {
    label: "Timeout",
    value: job.value?.timeout ? `${job.value.timeout}s` : "-",
  },
  { label: "Tags", slot: "tags" },
]);

const paramRows = computed(() => {
  if (!job.value?.values) return [];
  return Object.entries(job.value?.values).map(([key, value]) => ({
    parameter: key,
    value: value,
  }));
});

const artifactsUsed = computed(() => {
  return Object.entries(job.value?.artifactValues ?? {}).map(
    ([key, value]) => ({
      artifactParamName: key,
      id: value.id,
      snapshotId: value.snapshotId,
    }),
  );
});

const filteredMetrics = computed(() => {
  if (!filter.value) return metricsData.value;
  return metricsData.value.filter((metric) =>
    metric.name.toLowerCase().includes(filter.value.toLowerCase()),
  );
});

const graphClass = computed(() => {
  if (filteredMetrics.value.length <= 1 || isMobile.value) return "col-12";
  else if (filteredMetrics.value.length === 2 || isMedium.value) return "col-6";
  return "col-4";
});

// --- Data Fetching ---
onMounted(async () => {
  await getJob();
  getLogNumber();
  getJobMetrics();
});

async function getJob() {
  try {
    const res = await api.getItem("jobs", route.params.id);
    job.value = res.data;
  } catch (err) {
    console.error(err);
  }
}

async function getLogs(pagination) {
  isLoading.value = true;
  if (!tableRef.value) return;

  try {
    const minLoadTimePromise = new Promise((resolve) =>
      setTimeout(resolve, 300),
    );
    const [res] = await Promise.all([
      api.getJobLogs(job.value.id, pagination, selectedSeverity.value),
      minLoadTimePromise,
    ]);

    jobLogs.value = res.data.data;
    logTotalNumber.value = res.data.totalNumResults;
    tableRef.value.updateTotalRows(res.data.totalNumResults);
  } catch (err) {
    console.warn(err);
    notify.error("Failed to fetch logs");
  } finally {
    isLoading.value = false;
  }
}

async function getLogNumber() {
  try {
    const res = await api.getJobLogs(route.params.id, {
      index: 0,
      pageLength: 1,
      search: "",
    });
    logTotalNumber.value = res.data.totalNumResults;
  } catch (err) {
    console.warn(err);
  }
}

async function getJobMetrics() {
  try {
    const res = await api.getJobMetrics(route.params.id);
    metrics.value = res.data;
  } catch (err) {
    console.warn(err);
  }
}

async function loadAllMetricHistories() {
  metricsData.value = [];
  await getJobMetrics();
  const metricNames = metrics.value.map((metric) => metric.name);
  const promises = metricNames.map((name) =>
    getJobMetricHistory(route.params.id, name),
  );
  const results = await Promise.all(promises);
  metricsData.value = results;
}

async function getJobMetricHistory(id, name) {
  const res = await api.getJobMetricHistory(id, name);
  return {
    name,
    type: "scatter",
    data: [
      {
        x: res.data.data.map((obj) => obj.step),
        y: res.data.data.map((obj) => obj.value),
      },
    ],
  };
}

// --- Log Polling Logic ---
const selectedSeverity = ref(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]);
const selectedFrequency = ref(5);
const refreshOptions = [
  { label: "5s", value: 5 },
  { label: "10s", value: 10 },
  { label: "15s", value: 15 },
  { label: "30s", value: 30 },
];
let logsIntervalId = null;

function clearLogsInterval() {
  if (logsIntervalId) {
    clearInterval(logsIntervalId);
    logsIntervalId = null;
  }
}

async function setupLogsPolling() {
  clearLogsInterval();
  if (tab.value !== "logs") return;

  if (!job.value) await getJob();
  if (job.value?.status === "finished" || job.value?.status === "failed")
    return;

  await nextTick();
  if (!tableRef.value?.refreshTable) return;

  logsIntervalId = setInterval(async () => {
    await getJob();
    if (job.value.status === "finished" || job.value.status === "failed") {
      clearLogsInterval();
      return;
    }
    tableRef.value?.refreshTable();
  }, selectedFrequency.value * 1000);
}

// Watchers
watch([tab, selectedFrequency], setupLogsPolling, { immediate: true });
watch(selectedSeverity, () => {
  if (selectedSeverity.value.length === 0)
    selectedSeverity.value = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];
  tableRef.value?.refreshTable();
});
watch(
  () => tab.value,
  async (newVal) => {
    if (newVal === "metrics") await loadAllMetricHistories();
  },
);

// --- Actions ---
function reRunJob() {
  router.push({
    path: "/jobs/new",
    state: { oldJobId: route.params.id, jobSnapshotId: job.value.snapshot },
  });
}

async function deleteJob() {
  try {
    await api.deleteItem("jobs", route.params.id);
    notify.success(`Deleted job ${route.params.id}`);
    showDeleteDialog.value = false;
    router.back();
  } catch (err) {
    notify.error(err.response?.data?.message || "Delete failed");
  }
}

function formatDate(dateString) {
  if (!dateString) return "-";
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
</script>

<style scoped>
:deep(.q-table .code-cell .cm-editor),
:deep(.q-table .code-cell .cm-content) {
  cursor: text !important;
}
</style>
