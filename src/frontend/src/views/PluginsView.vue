<template>
  <PageTitle title="Plugins" />
  <TableComponent
    :rows="plugins"
    :columns="columns"
    title="Plugins"
    v-model:selected="selected"
    @edit="router.push(`/plugins/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    :showExpand="true"
    @request="getPlugins"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
  >
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #expandedSlot="{ row }">
      <q-btn 
        color="primary" 
        icon="folder" 
        :label="`Manage ${row.name} files`" 
        class="q-ma-md" 
        @click="router.push(`/plugins/${row.id}/files`)" 
      />
      <BasicTable
        :columns="fileColumns"
        :rows="row.files"
        :hideSearch="true"
        :hideEditTable="true"
        id="fileTable"
        class="q-mx-md"
        :title="`${row.name} Files`"
      />
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
    <span class="sr-only">Register a new Plugin</span>
    <q-tooltip>
      Register a new Plugin
    </q-tooltip>
  </q-btn>
  <AddPluginDialog 
    v-model="showAddDialog"
    @addPlugin="addPlugin"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deletePlugin"
    type="Plugin"
    :name="selected.length ? selected[0].name : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="plugins"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import BasicTable from '@/components/BasicTable.vue'
  import AddPluginDialog from '@/dialogs/AddPluginDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

  const router = useRouter()

  const selected = ref([])
  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const plugins = ref([])

  async function getPlugins(pagination) {
    try {
      const res = await api.getData('plugins', pagination)
      plugins.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, sort: (a, b) => a - b },
    { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true },
    { name: 'files', label: 'Files', align: 'left', sortable: false },
    { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: false },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
  ]

  async function addPlugin(plugin) {
    try {
      const res = await api.addItem('plugins', {
        name: plugin.name,
        description: plugin.description,
        group: plugin.group
      })
      notify.success(`Successfully created '${res.data.name}'`)
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  async function deletePlugin() {
    try {
      await api.deleteItem('plugins', selected.value[0].id)
      notify.success(`Successfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const fileColumns = [
    // field must be name or else selection doesn't work, possible quasar bug
    { name: 'filename', label: 'Filename', align: 'left', field: 'filename', sortable: true, },
    { name: 'tasks', label: 'Number of Tasks', align: 'left', field: 'tasks', sortable: true, },
  ]

  const tableRef = ref(null)

</script>