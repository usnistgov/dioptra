<template>
  <PageTitle :title="title" />
  <TableComponent 
    :rows="jobs"
    :columns="columns"
    title="Jobs"
    v-model:selected="selected"
    @request="getJobs"
    @delete="showDeleteDialog = true"
    ref="tableRef"
    :showExpand="true"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="pushToJobRoute"
    :hideOpenBtn="true"
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
      <q-chip
        v-if="statusStyles[props.row.status]"
        :label="props.row.status"
        :icon-right="statusStyles[props.row.status].icon"
        :color="statusStyles[props.row.status].color"
        :text-color="statusStyles[props.row.status].textColor"
        class="text-capitalize"
        :ripple="false"
        :style="statusStyles[props.row.status].style"
      />

    </template>
    <template #expandedSlot="{ row }">
      <q-btn
        label="Create Artifact"
        color="primary"
        class="q-ml-md q-my-sm"
        @click="jobId = row.id; showArtifactsDialog = true"
      />
      <BasicTable
        :columns="artifactColumns"
        :rows="row.artifacts"
        :hideSearch="true"
        :hideEditTable="true"
        class="q-mx-md"
        :title="`Job Artifacts`"
      />
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
  import BasicTable from '@/components/BasicTable.vue'
  import ArtifactsDialog from '@/dialogs/ArtifactsDialog.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

  const route = useRoute()
  const router = useRouter()

  const columns = [
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, },
    { name: 'id', label: 'Job ID', align: 'left', field: 'id', sortable: false, },
    { name: 'entrypoint', label: 'Entrypoint', align: 'left', field: 'entrypoint', sortable: false, },
    { name: 'queue', label: 'Queue', align: 'left', field: 'queue', sortable: false, },
    { name: 'status', label: 'Status', align: 'left', field: 'status', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false, },
  ]

  if(route.name === 'allJobs') {
    columns.splice(2, 0, 
      { name: 'experiment', label: 'Experiment', align: 'left', field: 'experiment', sortable: false, }
    )
  }

  const artifactColumns = [
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, },
    { name: 'uri', label: 'uri', align: 'left', field: 'uri', sortable: true, },
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
      await api.deleteItem('jobs', selected.value[0].id)
      notify.success(`Successfully deleted '${selected.value[0].description}'`)
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

  const statusStyles = {
    finished: {
      icon: "sym_o_check_circle",
      color: "green-2",
      textColor: "green-10",
      style: "cursor: default;"
    },
    queued: {
      icon: "sym_o_hourglass",
      color: "yellow-2",
      textColor: "grey-9",
      style: "min-width: 99px; cursor: default;"
    },
    default: {
      icon: "sym_o_error",
      color: "red-2",
      textColor: "grey-9",
      style: "min-width: 99px; cursor: default;"
    }
  }


</script>