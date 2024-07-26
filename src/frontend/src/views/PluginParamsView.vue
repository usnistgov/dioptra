<template>
  <PageTitle title="Plugin Params" />
  <TableComponent
    :rows="pluginParameterTypes"
    :columns="columns"
    title="Plugin Param Types"
    v-model:selected="selected"
    @edit="editing = true; editPluginParamType = selected[0]; showAddDialog = true"
    @delete="showDeleteDialog = true"
    :showExpand="true"
    @request="getPluginParameterTypes"
    ref="tableRef"
    :hideToggleDraft="true"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
  >
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
  </TableComponent>
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    @click="showAddDialog = true"
  >
    <span class="sr-only">Register a new Plugin Param Type</span>
    <q-tooltip>
      Register a new Plugin Param Type
    </q-tooltip>
  </q-btn>
  <PluginParamsDialog 
    v-model="showAddDialog"
    @addPluginParamType="addPluginParamType"
    @updatePluginParamType="updatePluginParamType"
    :editPluginParamType="selected.length && editing ? selected[0] : ''"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deletePlugin"
    type="Plugin Parameter Type"
    :name="selected.length ? selected[0].name : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="pluginParameterTypes"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import PluginParamsDialog from '@/dialogs/PluginParamsDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { ref, watch } from 'vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

  const editPluginParamType = ref({})

  const selected = ref([])
  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const pluginParameterTypes = ref([])

  const editing = ref(false)

  watch(showAddDialog, (newVal) => {
  if(!newVal) editing.value = false
  })

  async function getPluginParameterTypes(pagination) {
    try {
      const res = await api.getData('pluginParameterTypes', pagination)
      pluginParameterTypes.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true },
    { name: 'description', label: 'Description', field: 'description', align: 'left', sortable: false },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
  ]

  async function addPluginParamType(plugin) {
    try {
      console.log('plugin = ', plugin)
      const res = await api.addItem('pluginParameterTypes', plugin)
      notify.success(`Sucessfully created '${res.data.name}'`)
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  async function updatePluginParamType(id, name, description, structure) {
    try {
      const res = await api.updateItem('pluginParameterTypes', id, {name, description, structure})
      notify.success(`Sucessfully updated '${res.data.name}'`)
      tableRef.value.refreshTable()
      selected.value = []
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  async function deletePlugin() {
    try {
      await api.deleteItem('pluginParameterTypes', selected.value[0].id)
      notify.success(`Sucessfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const fileColumns = [
    { name: 'filename', label: 'Filename', align: 'left', field: 'filename', sortable: true, },
    { name: 'tasks', label: 'Number of Tasks', align: 'left', field: 'tasks', sortable: true, },
  ]

  const tableRef = ref(null)

</script>