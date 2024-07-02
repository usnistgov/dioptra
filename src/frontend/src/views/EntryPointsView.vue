<template>
  <PageTitle 
    title="Entry Points"
  />
  <TableComponent 
    :rows="entrypoints"
    :columns="columns"
    :showExpand="true"
    title="Entry Points"
    v-model:selected="selected"
    :pagination="{sortBy: 'draft', descending: true}"
    @edit="store.editEntryPoint = selected[0]; router.push(`/entrypoints/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    @request="getEntrypoints"
    ref="tableRef"
  >
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #body-cell-taskGraph="props">
      <q-btn
        v-if="props.row.taskGraph.length"
        label="View YAML"
        color="primary"
        @click.stop="displayYaml = props.row.taskGraph; showTaskGraphDialog = true;"
      />
      <span v-else class="text-negative">
        EMPTY
      </span>
    </template>
    <template #body-cell-parameterNames="props">
      <label v-for="(param, i) in props.row.parameters" :key="i">
        {{ param.name }} <br>
      </label>
    </template>
    <template #body-cell-parameterTypes="props">
      <label v-for="(param, i) in props.row.parameters" :key="i">
        {{ param.parameterType }} <br>
      </label>
    </template>
    <template #body-cell-defaultValues="props">
      <label v-for="(param, i) in props.row.parameters" :key="i">
        {{ param.defaultValue }} <br>
      </label>
    </template>
    <template #expandedSlot="{ row }">
      <CodeEditor v-model="row.taskGraph" language="yaml" />
    </template>
  </TableComponent>

  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    to="/entrypoints/new"
  >
    <span class="sr-only">Register new Entry Point</span>
    <q-tooltip>
      Register new Entry Point
    </q-tooltip>
  </q-btn>

  <InfoPopupDialog
    v-model="showTaskGraphDialog"
  >
    <template #title>
      <label id="modalTitle">
        Task Graph YAML
      </label>
    </template>
    <CodeEditor v-model="displayYaml" style="height: auto;" />
  </InfoPopupDialog>
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteEntryPoint"
    type="Entry Point"
    :name="selected.length ? selected[0].name : ''"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRouter } from 'vue-router'
  import CodeEditor from '@/components/CodeEditor.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'


  
  const router = useRouter()

  const store = useDataStore()

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true, },
    { name: 'taskGraph', label: 'Task Graph', align: 'left', field: 'taskGraph',sortable: true, },
    { name: 'parameterNames', label: 'Parameter Name(s)', align: 'left', sortable: true },
    { name: 'parameterTypes', label: 'Parameter Type(s)', align: 'left', field: 'parameterTypes', sortable: true },
    { name: 'defaultValues', label: 'Default Values', align: 'left', field: 'defaultValues', sortable: true },
  ]

  const selected = ref([])

  const showTaskGraphDialog = ref(false)
  const displayYaml = ref('')

  const tableRef = ref(null)
  
  const entrypoints = ref([])

  const showDeleteDialog = ref(false)

  async function getEntrypoints(pagination, showDrafts) {
    try {
      const res = await api.getData('entrypoints', pagination, showDrafts)
      entrypoints.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  async function deleteEntryPoint() {
    try {
      await api.deleteItem('entrypoints', selected.value[0].id)
      notify.success(`Sucessfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

</script>