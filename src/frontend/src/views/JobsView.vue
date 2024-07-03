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
    :hideEditBtn="true"
  >
    <template #body-cell-entrypoint="props">
      {{ props.row.entrypoint.name }}
    </template>
    <template #body-cell-queue="props">
      {{ props.row.queue.name }}
    </template>
  </TableComponent>
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    :to="`/experiments/${route.params.id}/jobs/new`"
  >
    <span class="sr-only">Create a new Job</span>
    <q-tooltip>
      Create a new Job
    </q-tooltip>
  </q-btn>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteJob"
    type="Job"
    :name="selected.length ? selected[0].description : ''"
  />

</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useRoute } from 'vue-router'
  import PageTitle from '@/components/PageTitle.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'

  const route = useRoute()

  const columns = [
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, },
    { name: 'entrypoint', label: 'Entrypoint', align: 'left', field: 'entrypoint', sortable: true, },
    { name: 'queue', label: 'Queue', align: 'left', field: 'queue', sortable: true, },
    { name: 'status', label: 'Status', align: 'left', field: 'status', sortable: true },
  ]

  const selected = ref([])

  const title = ref('')
  getExperiment()
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
      const res = await api.getJobs(route.params.id, pagination, showDrafts)
      console.log('jobs res = ', res)
      jobs.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  const showDeleteDialog = ref(false)

  async function deleteJob() {
    try {
      if(Object.hasOwn(selected.value[0], 'hasDraft')) {
        await api.deleteItem('jobs', selected.value[0].id)
      } else {
        // await api.deleteDraft('queues', selected.value[0].id)
      }
      notify.success(`Sucessfully deleted '${selected.value[0].description}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

</script>