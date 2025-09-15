<template>
  <div class="column" style="min-height: calc(100vh - 100px);">
    <div class="row items-center justify-between">
      <PageTitle :title="`Job ${$route.params.id} Dashboard`" />
      <q-btn 
        color="negative" 
        icon="sym_o_delete" 
        label="Delete Job" 
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
        >
          <q-tab name="overview" label="Overview" />
          <q-tab name="logs" :label="`Logs ${logTotalNumber ? `(${logTotalNumber})` : ''}`" />
          <q-tab name="metrics" :label="`Metrics ${metrics.length ? `(${metrics.length})` : ''}`" />
          <q-tab name="artifacts" :label="`Artifacts Created ${job?.artifacts.length ? `(${job?.artifacts.length})` : ''}`" />
        </q-tabs>
        <q-separator />
    </div>
    <div 
      v-if="tab === 'overview'"
      class="row q-gutter-lg"
    >
      <div class="col" :class="`${isMedium ? 'col-12' : 'col'}`">
        <h2>Details</h2>
        <KeyValueTable :rows="overviewRows">
          <template #tags="{ tags = [] }">
            <div style="margin-top: -5px; margin-bottom: -5px;">
              <q-chip
                v-for="(tag, i) in tags"
                :key="i"
                color="primary" 
                text-color="white"
                class="q-my-none"
              >
                {{ tag.name.length <= 18 ? tag.name : tag.name.replace(/(.{17})..+/, "$1…") }}
                <q-tooltip v-if="tag.name.length > 18" max-width="30vw" style="overflow-wrap: break-word">
                  {{ tag.name }}
                </q-tooltip>
              </q-chip>
              <q-btn
                round
                size="xs"
                icon="add"
                @click="showTagsDialog = true"
                color="grey-5"
                text-color="black"
                class="q-ml-xs"
              />
            </div>
          </template>
          <template #experiment="{ name = '', id, snapshotId }">
            <RouterLink :to="`/experiments/${id}?snapshotId=${snapshotId}`">
              {{ name.length < 18 ? name : name.replace(/(.{18})..+/, "$1…") }}
              <q-tooltip v-if="name.length > 18" max-width="30vw" style="overflow-wrap: break-word">
                {{ name }}
              </q-tooltip>
            </RouterLink>
          </template>
          <template #entrypoint="{ name = '', id, snapshotId }">
            <RouterLink :to="`/entrypoints/${id}?snapshotId=${snapshotId}`">
              {{ name.length < 18 ? name : name.replace(/(.{18})..+/, "$1…") }}
              <q-tooltip v-if="name.length > 18" max-width="30vw" style="overflow-wrap: break-word">
                {{ name }}
              </q-tooltip>
            </RouterLink>
          </template>
          <template #status="{ status = '' }">
            <JobStatus
              :status="status"
            />
          </template>
        </KeyValueTable>
        <q-btn
          color="light-blue" 
          icon="update" 
          label="Re-Run Job" 
          class="q-mt-lg" 
          @click="reRunJob()"
        />
      </div>
      <div class="col">
        <h2>Parameters</h2>
        <TableComponent
          :columns="parametersColumns"
          :rows="paramRows"
          @request="getJob"
          v-model:selected="selectedParam"
          rowKey="parameter"
          :hideCreateBtn="true"
          :hideDeleteBtn="true"
          style="margin-top: 0px;"
        />
      </div>
      <div class="col">
        <h2>Artifacts Used</h2>
        <TableComponent
          label="Artifacts used"
          :columns="artifactsUsedColumns"
          v-model:selected="selectedUsedArtifact"
          :rows="artifactsUsed"
          :hideCreateBtn="true"
          :hideDeleteBtn="true"
          style="margin-top: 0px;"
          @edit="router.push(`/artifacts/${selectedUsedArtifact[0].id}?snapshotId=${selectedUsedArtifact[0].snapshotId}`)"
        />
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
        :hideSearch="true"
        style="margin-top: 0;"
        class="q-mb-lg"
        ref="tableRef"
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
          <q-select
            v-if="job.status !== 'finished' && job.status !== 'failed'"
            v-model="selectedFrequency"
            label="Refresh Frequency"
            :options="refreshOptions"
            option-value="value"
            option-label="label"
            emit-value
            map-options
            dense
            filled
            style="width: 175px"
            class="q-mr-lg"
          />
          <!-- <q-select
            label="Filter Severity"
            v-model="selectedSeverity"
            :options="['INFO', 'WARNING', 'ERROR']"
            multiple
            style="width: 225px;"
            filled
            dense 
            class="q-mr-lg" 
          >
            <template v-slot:option="{ itemProps, opt, selected, toggleOption }">
              <q-item v-bind="itemProps">
                <q-item-section>
                  <q-item-label>
                    {{ opt }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-checkbox
                    v-model="selectedSeverity"
                    :val="opt"
                  />
                </q-item-section>
              </q-item>
            </template>
          </q-select> -->
        </template>
      </TableComponent>
    </div>
    <div v-if="tab === 'metrics'" class="row q-col-gutter-x-lg q-col-gutter-y-lg">
      <div class="col-12">
        <!-- @request="getJobMetrics" is not needed because getJobMetrics is run by loadAllMetricHistories -->
        <TableComponent
          title="Job Metrics Latest Values"
          :columns="metricColumns"
          :rows="metrics"
          v-model:selected="selectedMetric"
          rowKey="name"
          :hideCreateBtn="true"
          :hideDeleteBtn="true"
          style="margin-top: 0px;"
          class="q-mb-lg"
          v-model:filter="filter"
        />
        <div class="row items-center">
          <q-input 
            v-model="filter" 
            debounce="300" 
            dense 
            placeholder="Search metric charts" 
            outlined
            class="col-grow"
            clearable
          >
            <template #prepend>
              <q-icon name="search" />
            </template>
          </q-input>
          <q-btn
            label="Refresh"
            color="primary"
            icon="refresh"
            class="q-ml-lg"
            @click="loadAllMetricHistories"
          />
        </div>
      </div>
      <div
        :class="graphClass" 
        v-for="(metric, i) in filteredMetrics"
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
        class="row items-center q-mt-lg" 
      >
        <q-icon
          name="sym_o_info"
          size="2.5em"
          color="grey-7"
          class="q-mr-sm"
        />
        <div style="opacity: 0.7">No metrics found</div>
      </div>
    </div>
    <div v-if="tab === 'artifacts'">
      <JobArtifactsTable 
        :artifactIds="job.artifacts.map((artifact) => artifact.id)"
        style="margin-top: 0px"
      />
    </div>

    <q-space />
    <div class="row justify-end">
      <q-btn
        outline  
        label="Return to Jobs"
        @click="router.back()"
        class="cancel-btn q-mt-lg"
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
import { ref, computed, inject, watch, nextTick, onMounted } from 'vue'
import PageTitle from '@/components/PageTitle.vue'
import * as api from '@/services/dataApi'
import { useRoute, useRouter } from 'vue-router'
import KeyValueTable from '@/components/KeyValueTable.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
import JobStatus from '@/components/JobStatus.vue'
import TableComponent from '@/components/TableComponent.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import * as notify from '../notify'
import PlotlyGraph from '@/components/PlotlyGraph.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import JobArtifactsTable from '@/components/JobArtifactsTable.vue'

const route = useRoute()
const router = useRouter()

const tab = ref('overview')
const isMedium = inject('isMedium')
const isMobile = inject('isMobile')

const job = ref()
const showTagsDialog = ref(false)
const showDeleteDialog = ref(false)
const selectedParam = ref([])
const selectedUsedArtifact = ref([])
const selectedMetric = ref([])
const metrics = ref([])

async function getJob() {
  try {
    const res = await api.getItem('jobs', route.params.id)
    job.value = res.data
  } catch(err) {
    console.log(err)
  }
}

onMounted(() => {
  // to get tab counts
  getLogNumber()
  getJobMetrics()
})

const metricNames = computed(() => {
  return metrics.value.map(metric => metric.name)
})

watch(tab, async (newVal) => {
  if(newVal === 'metrics') {
    await loadAllMetricHistories()
  }
})

async function loadAllMetricHistories() {
  metricsData.value = []
  await getJobMetrics()
  const promises = metricNames.value.map(name =>
    getJobMetricHistory(route.params.id, name)
  )
  const results = await Promise.all(promises)
  metricsData.value = results
}

const jobLogs = ref([])
const filteredJobLogs = computed(() => {
  return jobLogs.value.filter((log) => selectedSeverity.value.includes(log.severity))
})
const selectedSeverity = ref(['INFO', 'WARNING', 'ERROR'])
watch(selectedSeverity, () => {
  tableRef.value.refreshTable()
})

const tableRef = ref(null)

async function getLogs(pagination) {
  try {
    const res = await api.getJobLogs(job.value.id, pagination)
    console.log('logs = ', res.data)
    jobLogs.value = res.data.data.filter(log =>
      selectedSeverity.value.includes(log.severity)
    )
    logTotalNumber.value = res.data.totalNumResults
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    console.log('err = ', err)
    notify.error(err.response.data.message);
  }
}

const logTotalNumber = ref()

async function getLogNumber() {
  try {
    const res = await api.getJobLogs(route.params.id, {
      index: 0,
      pageLength: 1,
      search: ''
    })
    logTotalNumber.value = res.data.totalNumResults
  } catch(err) {
    console.warn(err)
  }
}

const selectedFrequency = ref(5)
const refreshOptions = [
  {label: '5 Seconds', value: 5},
  {label: '10 Seconds', value: 10},
  {label: '15 Seconds', value: 15},
  {label: '30 Seconds', value: 30}
]

let logsIntervalId = null

function clearLogsInterval() {
  if (logsIntervalId) {
    clearInterval(logsIntervalId)
    logsIntervalId = null
  }
}

async function setupLogsPolling() {
  clearLogsInterval()

  if (tab.value !== 'logs') return

  await getJob()
  if(job.value.status === 'finished' || job.value.status === 'failed') return

  // Ensure the table is rendered so tableRef is non-null
  await nextTick()

  // Guard if the ref/method isn't ready yet
  if (!tableRef.value?.refreshTable) return

  // Then start interval
  logsIntervalId = setInterval(async() => {
    await getJob()
    if(job.value.status === 'finished' || job.value.status === 'failed') {
      clearLogsInterval()
      return
    }
    tableRef.value?.refreshTable()
  }, selectedFrequency.value * 1000)
}

// React to BOTH tab changes and frequency changes
watch([tab, selectedFrequency], setupLogsPolling, { immediate: true })

async function getJobMetrics() {
  try {
    const res = await api.getJobMetrics(route.params.id)
    metrics.value = res.data
  } catch(err) {
    console.log(err)
  }
}

const metricsData = ref([])

async function getJobMetricHistory(id, name) {
  const res = await api.getJobMetricHistory(id, name)
  
  return {
    name,
    type: 'scatter',
    data: [
      {
        x: res.data.data.map(obj => obj.step),
        y: res.data.data.map(obj => obj.value)
      }
    ]
  }
}

const filter = ref('')

const filteredMetrics = computed(() => {
  if (!filter.value) return metricsData.value
  return metricsData.value.filter(metric =>
    metric.name.toLowerCase().includes(filter.value.toLowerCase())
  )
})

const graphClass = computed(() => {
  if(filteredMetrics.value.length <= 1 || isMobile.value) return 'col-12'
  else if(filteredMetrics.value.length === 2 || isMedium.value) return 'col-6'
  return 'col-4'
})

function formatDate(dateString) {
  const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true }
  return new Date(dateString).toLocaleString('en-US', options)
}

const overviewRows = computed(() => [
  { label: 'ID', value: job.value?.id },
  { label: 'Description', value: job.value?.description },
  { label: 'Status', slot: 'status', props: { status: job.value?.status} },
  { label: 'Created On', value: formatDate(job.value?.createdOn) },
  { label: 'Created by', value: job.value?.user.username },
  { label: 'Experiment', slot: 'experiment', 
    props: { name: job.value?.experiment.name, id: job.value?.experiment.id, snapshotId: job.value?.experiment.snapshotId }
  },
  { label: 'Entrypoint', slot: 'entrypoint',
    props: { name: job.value?.entrypoint.name, id: job.value?.entrypoint.id, snapshotId: job.value?.entrypoint.snapshotId }
  },
  { label: 'Queue', value: job.value?.queue.name },
  { label: 'Timeout', value: job.value?.timeout },
  { label: 'Tags', slot: 'tags', props: { tags: job.value?.tags }  },
])

const parametersColumns = [
  { name: 'parameter', label: 'Parameter', align: 'left', field: 'parameter', sortable: true, },
  { name: 'value', label: 'Value', align: 'left', field: 'value', sortable: false, },
]

const artifactsUsedColumns = [
  { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: true, },
  { name: 'snapshotId', label: 'Snapshot Id', align: 'left', field: 'snapshotId', sortable: false, },
  { name: 'artifactParamName', label: 'Param Name', align: 'left', field: 'artifactParamName', sortable: true, },
]

const metricColumns = [
  { name: 'metric', label: 'Metric', align: 'left', field: 'name', sortable: true, },
  { name: 'value', label: 'Value', align: 'left', field: 'value', sortable: false, },
]

const logColumns = [
  { name: 'severity', label: 'Severity', align: 'left', field: 'severity', sortable: false, classes: 'vertical-top' },
  { name: 'loggerName', label: 'Logger Name', align: 'left', field: 'loggerName', sortable: false, classes: 'vertical-top', },
  { name: 'createdOn', label: 'Received On', align: 'left', field: 'createdOn', sortable: false, classes: 'vertical-top', },
  { name: 'message', label: 'Message', align: 'left', field: 'message', sortable: false, },
]

const paramRows = computed(() => {
  if(!job.value?.values) return []
  return Object.entries(job.value?.values).map(([key, value]) => ({
    parameter: key,
    value: value,
  }))
})

async function deleteJob() {
  try {
    await api.deleteItem('jobs', route.params.id)
    notify.success(`Successfully deleted job ID: ${route.params.id}`)
    showDeleteDialog.value = false
    router.back()
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

function reRunJob() {
  router.push({
    path: '/jobs/new',
    state: { oldJobId: route.params.id, jobSnapshotId: job.value.snapshot } 
  })
}

const artifactsUsed = computed(() => {
  return Object.entries(job.value?.artifactValues ?? {}).map(([key, value]) => ({
    artifactParamName: key,
    id: value.id,
    snapshotId: value.snapshotId,
  }))
})

</script>

<style scoped>
  :deep(.q-table .code-cell .cm-editor),
  :deep(.q-table .code-cell .cm-content),
  :deep(.q-table .code-cell .cm-scroller),
  :deep(.q-table .code-cell .cm-line) {
    cursor: text !important;
  }

  :deep(.q-table .code-cell .cm-gutters) {
    cursor: default !important;
  }
</style>