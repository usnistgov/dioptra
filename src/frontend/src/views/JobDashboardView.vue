<template>
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
        <q-tab name="model metrics" label="Model metrics" />
        <q-tab name="system metrics" label="System metrics" />
        <q-tab name="artifacts" label="Artifacts" />
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
        <template #experiment="{ name = '', id }">
          <RouterLink :to="`/experiments/${id}`">
            {{ name.length < 18 ? name : name.replace(/(.{18})..+/, "$1…") }}
            <q-tooltip v-if="name.length > 18" max-width="30vw" style="overflow-wrap: break-word">
              {{ name }}
            </q-tooltip>
          </RouterLink>
        </template>
        <template #entrypoint="{ name = '', id }">
          <RouterLink :to="`/entrypoints/${id}`">
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
      <h2>Metrics</h2>
      <TableComponent
        :columns="metricColumns"
        :rows="metrics"
        @request="getJobMetrics"
        v-model:selected="selectedMetric"
        rowKey="name"
        :hideCreateBtn="true"
        :hideDeleteBtn="true"
        style="margin-top: 0px;"
      />
      <q-btn
        v-if="metrics.length === 0"
        label="Add example Metrics"
        color="primary"
        class="q-mt-lg"
        @click="addExampleMetrics"
      />
    </div>
  </div>
  <div v-if="tab === 'model metrics'" class="row q-col-gutter-x-lg q-col-gutter-y-lg">
    <div class="col-12">
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
      :key="i"
    >
      <PlotlyGraph
        :data="metric.data"
        :title="metric.name"
        :graphClass="graphClass"
      />
      <q-btn
        label="Add Data"
        @click="addData(i)"
        color="primary"
        class="q-mt-sm"
      />
    </div>
    <div class="row items-center q-mt-lg" v-if="filteredMetrics.length === 0">
      <q-icon
        name="sym_o_info"
        size="2.5em"
        color="grey"
        class="q-mr-sm"
      />
      <caption>No metrics found</caption>
    </div>
  </div>

  <div style="display: flex; justify-content: flex-end; margin-top: 2rem;">
    <q-btn
      outline  
      label="Return to Jobs"
      @click="router.back()"
      class="cancel-btn"
      color="primary"
    />
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
import { ref, computed, inject, watch } from 'vue'
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

const route = useRoute()
const router = useRouter()

const tab = ref('overview')
const isMedium = inject('isMedium')
const isMobile = inject('isMobile')

const job = ref()
const showTagsDialog = ref(false)
const showDeleteDialog = ref(false)
const selectedParam = ref([])
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

const metricNames = computed(() => {
  return metrics.value.map(metric => metric.name)
})

watch(tab, async (newVal) => {
  if (newVal === 'model metrics') {
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

async function addExampleMetrics() {
  try {
    for (let i = 0; i < 10; i++) {
      const accuracy = 1 / (1 + Math.exp(-i))
      const loss = Math.exp(-i)
      const sineWave = Math.sin(i)

      await api.addJobMetric(route.params.id, 'accuracy', accuracy, i)
      await api.addJobMetric(route.params.id, 'loss', loss, i)
      await api.addJobMetric(route.params.id, 'sine_wave', sineWave, i)
    }
    getJobMetrics()
  } catch(err) {
    console.log(err)
  }
}

function addData(index) {
  const yVals = metricsData.value[index].data[0].y
  const max = Math.max(...yVals)
  const min = Math.min(...yVals)

  const randomBetweenMinMax = Math.random() * (max - min) + min
  metricsData.value[index].data[0].x.push(yVals.length)
  metricsData.value[index].data[0].y.push(randomBetweenMinMax)
}


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
  { label: 'Experiment', slot: 'experiment', props: { name: job.value?.experiment.name, id: job.value?.experiment.id } },
  { label: 'Entrypoint', slot: 'entrypoint', props: { name: job.value?.entrypoint.name, id: job.value?.entrypoint.id } },
  { label: 'Queue', value: job.value?.queue.name },
  { label: 'Timeout', value: job.value?.timeout },
  { label: 'Tags', slot: 'tags', props: { tags: job.value?.tags }  },
])

const parametersColumns = [
  { name: 'parameter', label: 'Parameter', align: 'left', field: 'parameter', sortable: true, },
  { name: 'value', label: 'Value', align: 'left', field: 'value', sortable: false, },
]

const metricColumns = [
  { name: 'metric', label: 'Metric', align: 'left', field: 'name', sortable: true, },
  { name: 'value', label: 'Value', align: 'left', field: 'value', sortable: false, },
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

</script>