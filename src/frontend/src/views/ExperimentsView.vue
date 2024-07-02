<template>
  <PageTitle title="Experiments" />
  <TableComponent 
    :rows="experiments"
    :columns="columns"
    title="Experiments"
    v-model:selected="selected"
    @edit="store.savedExperimentForm = selected[0]; store.editMode = true; router.push(`/experiments/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    @request="getExperiments"
    ref="tableRef"
  >
    <template #body-cell-name="props">
        <RouterLink :to="`/experiments/${props.row.id}/jobs`">
          {{props.row.name}}
        </RouterLink>
      </template>
    <template #body-cell-draft="props">
      <q-chip v-if="props.row.draft" outline color="red" text-color="white" class="q-ml-none">
        DRAFT
      </q-chip>
      <span v-else></span>
    </template>
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #body-cell-tags="props">
      <q-chip v-for="(tag, i) in props.row.tags" :key="i" color="primary" text-color="white">
        {{ tag }}
      </q-chip>
    </template>
  </TableComponent>

  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
  >
    <span class="sr-only">Create a new Experiment</span>
    <q-tooltip>
      Create a new Experiment
    </q-tooltip>
    <q-menu>
      <q-list>
        <q-item clickable to="/experiments/new">
          <q-item-section>Create Experiment</q-item-section>
        </q-item>
        <q-separator />
        <q-item clickable>
          <q-item-section>Create Job</q-item-section>
        </q-item>
        <q-separator />
        <q-item clickable>
          <q-item-section>Create Entry Point</q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteExperiment"
    type="Experiment"
    :name="selected.length ? selected[0].name : ''"
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
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, sort: (a, b) => a - b },
    { name: 'draft', label: 'Draft', align: 'left', field: 'draft', sortable: true },
    { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true },
    { name: 'entryPoints', label: 'Entry Points', align: 'left', field: 'entryPoints', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: false },
  ]

  const selected = ref([])

  async function getExperiments(pagination) {
    try {
      const res = await api.getData('experiments', pagination, false)
      experiments.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  const tableRef = ref(null)

  async function deleteExperiment() {
    try {
      await api.deleteItem('experiments', selected.value[0].id)
      notify.success(`Sucessfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }


</script>