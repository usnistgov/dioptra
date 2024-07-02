<template>
  <PageTitle title="Jobs" />
  <TableComponent 
    :rows="experiments"
    :columns="columns"
    title="Experiments"
    v-model:selected="selected"
    @edit="store.savedExperimentForm = selected[0]; store.editMode = true; router.push(`/experiments/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    @request="getJobs"
    ref="tableRef"
    :hideEditBtn="true"
  >
    <template #body-cell-entrypoint="props">
      {{ props.row.entrypoint.name }}
    </template>
    <template #body-cell-queue="props">
      {{ props.row.queue.name }}
    </template>
    <template #body-cell-group="props">
      {{ props.row.group.name }}
    </template>
  </TableComponent>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteJob"
    type="Experiment"
    :name="selected.length ? selected[0].description : ''"
  />
</template>

<script setup>

  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRouter } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  
  const router = useRouter()

  const store = useDataStore()

  const showDeleteDialog = ref(false)

  const experiments = ref([])

  const columns = [
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, },
    { name: 'entrypoint', label: 'Entrypoint', align: 'left', field: 'entrypoint', sortable: true, },
    { name: 'queue', label: 'Queue', align: 'left', field: 'queue', sortable: true, },
    { name: 'status', label: 'Status', align: 'left', field: 'status', sortable: true },
  ]

  const selected = ref([])

  async function getJobs(pagination) {
    try {
      const res = await api.getData('jobs', pagination, false)
      experiments.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  const tableRef = ref(null)

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