<template>
  <PageTitle v-if="route.name !== 'experimentJobs'" :title="title" />

  <TableComponent 
    ref="tableRef"
    :rows="jobs"
    :columns="computedColumns"
    title="Jobs"
    v-model:selected="selected"
    :loading="isLoading"
    @request="getJobs"
    @create="pushToJobRoute"
    @delete="(row) => { selected = [row]; showDeleteDialog = true }"
    @edit="(row) => router.push(`/jobs/${row.id}`)"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
  >
    <template #body-cell-status="props">
       <JobStatus :status="props.row.status" />
    </template>
  </TableComponent>

  <DeleteDialog v-model="showDeleteDialog" @submit="deleteJob" type="Job" :name="selected[0]?.description || `Job ID: ${selected[0]?.id}`" />
  <AssignTagsDialog v-model="showTagsDialog" :editObj="editObjTags" type="jobs" @refreshTable="tableRef.refreshTable()" />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue' // Added ref and onMounted
import { useRoute, useRouter } from 'vue-router'
import TableComponent from '@/components/table/TableComponent.vue' 
import PageTitle from '@/components/PageTitle.vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
import JobStatus from '@/components/JobStatus.vue'

const route = useRoute()
const router = useRouter()

// --- MISSING STATE VARIABLES ADDED HERE ---
const title = ref('Jobs')
const jobs = ref([])
const isLoading = ref(false)
const selected = ref([]) // This fixes the 'reading 0' error
const showDeleteDialog = ref(false)
const showTagsDialog = ref(false)
const editObjTags = ref({})
const tableRef = ref(null)

const computedColumns = computed(() => {
  const baseCols = [
  { 
    name: 'id', 
    label: 'Job ID', 
    field: 'id', 
    align: 'left', 
    styleType: 'icon-badge', 
    conceptType: 'job',
    includeIcon: true,
    size:'md',
    uppercase:false,
    formatLabel: 'Job #{label}'
  },
    { 
      name: 'description', 
      label: 'Description', 
      field: 'description', 
      align: 'left',
      styleType: 'long-text', 
      maxLength: 150,
      maxWidth: '300px',
      align: 'left',
      useQuotes: true, 
      textType: 'capitalize'
    },
    { 
      name: 'entrypoint', 
      label: 'Entrypoint', 
      field: 'entrypoint', 
      styleType: 'icon-badge', 
      conceptType: 'entrypoint' , 
      align: 'left'
    },
    { 
      name: 'queue', 
      label: 'Queue', 
      field: 'queue', 
      styleType: 'icon-badge',
      conceptType: 'queue', 
      align: 'left'
    },

    { name: 'status', label: 'Status', field: 'status' ,align: 'left'}, 
    { 
      name: 'tags', 
      label: 'Tags', 
      field: 'tags', 
      styleType: 'tag-list', // Activates the new component
      align: 'left'
    }

  ]

  if(route.name === 'allJobs') {
    baseCols.splice(3, 0, { 
      name: 'experiment', 
      label: 'Experiment', 
      field: 'experiment', 
      styleType: 'icon-badge',
      conceptType: 'experiment', 
      align: 'left'
    })
  }
  return baseCols
})

// --- API FUNCTIONS ---
async function getJobs(pagination, showDrafts) {
  isLoading.value = true
  try {
    let res
    if(route.name === 'experimentJobs') {
      res = await api.getJobs(route.params.id, pagination, showDrafts)
    } else {
      res = await api.getData('jobs', pagination, false)
    }
    jobs.value = res.data.data
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    notify.error(err.response?.data?.message || 'Failed to fetch jobs')
  } finally {
    isLoading.value = false
  }
}

async function deleteJob() {
  try {
    const id = selected.value[0].id
    await api.deleteItem('jobs', id)
    notify.success(`Deleted job ${id}`)
    showDeleteDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response?.data?.message)
  }
}

function pushToJobRoute() {
  const path = route.name === 'experimentJobs' 
    ? `/experiments/${route.params.id}/jobs/new` 
    : '/jobs/new'
  router.push(path)
}
</script>