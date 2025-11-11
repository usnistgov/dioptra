<template>
  <PageTitle
    v-if="route.name !== 'experimentJobs'"
    :title="title" 
  />
  <TableComponent 
    :rows="jobs"
    :columns="columns"
    title="Jobs"
    v-model:selected="selected"
    @request="getJobs"
    @delete="showDeleteDialog = true"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="pushToJobRoute"
    :hideOpenBtn="true"
    @edit="router.push(`/jobs/${selected[0].id}`)"
  >
    <template #body-cell-experiment="props">
      {{ props.row.experiment.name }}
    </template>
    <template #body-cell-entrypoint="props">
      {{ props.row.entrypoint.name }}
    </template>
    <template #body-cell-queue="props">
      {{ props.row.queue.name }}
    </template>
    <template #body-cell-status="props">
      <JobStatus :status="props.row.status" />
    </template>
  </TableComponent>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteJob"
    type="Job"
    :name="selected[0]?.description || `Job ID: ${selected[0]?.id}`"
  />

  <ArtifactsDialog 
    v-model="showArtifactsDialog"
    :editArtifact="''"
    :expId="route.params.id"
    :jobId="jobId"
  />

  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="jobs"
    @refreshTable="tableRef.refreshTable()"
  />

</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import PageTitle from '@/components/PageTitle.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import ArtifactsDialog from '@/dialogs/ArtifactsDialog.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import JobStatus from '@/components/JobStatus.vue'

  const route = useRoute()
  const router = useRouter()

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: true, },
    { name: 'entrypoint', label: 'Entrypoint', align: 'left', field: 'entrypoint', sortable: true, },
    { name: 'queue', label: 'Queue', align: 'left', field: 'queue', sortable: true, },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, style: 'width: 275px',},
    { name: 'status', label: 'Status', align: 'left', field: 'status', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false, },
  ]

  if(route.name === 'allJobs') {
    columns.splice(2, 0, 
      { name: 'experiment', label: 'Experiment', align: 'left', field: 'experiment', sortable: true, }
    )
  }

  const artifactColumns = [
    { name: 'id', label: 'id', align: 'left', field: 'id', sortable: true, },
  ]

  const selected = ref([])

  const title = ref('')

  if(route.name === 'experimentJobs') {
    getExperiment()
  } else if(route.name === 'allJobs') {
    title.value = 'Jobs'
  }

  async function getExperiment() {
    try {
      const res = await api.getItem('experiments', route.params.id)
      title.value = `${res.data.name} Jobs`
    } catch(err) {
      console.log('err = ', err)
    } 
  }

  const jobs = ref([])

  const tableRef = ref(null)

  async function getJobs(pagination, showDrafts) {
    // default sort by id descending
    if(!pagination.sortBy) {
      pagination.sortBy = 'id'
      pagination.descending = true
    }
    try {
      let res
      if(route.name === 'experimentJobs') {
        res = await api.getJobs(route.params.id, pagination, showDrafts)
      } else if(route.name === 'allJobs') {
        res = await api.getData('jobs', pagination, false)
      }
      console.log('jobs res = ', res)
      jobs.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  const showDeleteDialog = ref(false)
  const showArtifactsDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const jobId = ref('')

  async function deleteJob() {
    try {
      const jobId = JSON.parse(JSON.stringify(selected.value[0].id))
      await api.deleteItem('jobs', selected.value[0].id)
      notify.success(`Successfully deleted job ${jobId}`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  function pushToJobRoute() {
    if(route.name === 'experimentJobs') {
      router.push(`/experiments/${route.params.id}/jobs/new`)
    } else if(route.name === 'allJobs') {
      router.push('/jobs/new')
    }
  }

</script>