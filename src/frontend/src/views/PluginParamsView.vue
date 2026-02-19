<template>
  <PageTitle title="Plugin Parameters" />
  <TableComponent
    :rows="pluginParameterTypes"
    :columns="columns"
    title="Plugin Parameter Types"
    v-model:selected="selected"
    @open="openTab => (openTab
      ? openWindow.open(`/pluginParams/${selected[0].id}`, '_blank')
      : router.push(`/pluginParams/${selected[0].id}`)
    )"
    @delete="showDeleteDialog = true"
    @request="getPluginParameterTypes"
    ref="tableRef"
    :hideToggleDraft="true"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/pluginParams/new')"
    :loading="isLoading"
  >
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
  </TableComponent>

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
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { ref, watch } from 'vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import { useRouter } from 'vue-router'

  const openWindow = window
  const router = useRouter()

  const selected = ref([])
  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const pluginParameterTypes = ref([])

  const isLoading = ref(false)

  const editing = ref(false)

  watch(showAddDialog, (newVal) => {
  if(!newVal) editing.value = false
  })

  async function getPluginParameterTypes(pagination) {
    isLoading.value = true
    const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300)); 

    try {
      const [res] = await Promise.all([
        api.getData('pluginParameterTypes', pagination),
        minLoadTimePromise
      ]);
        
      pluginParameterTypes.value = res.data.data;
      tableRef.value.updateTotalRows(res.data.totalNumResults);
    } catch(err) {
      console.log('err = ', err);
      notify.error(err.response.data.message);
    } finally {
      isLoading.value = false;
    }
  }

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', field: 'description', align: 'left', sortable: true },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
  ]

  async function deletePlugin() {
    try {
      await api.deleteItem('pluginParameterTypes', selected.value[0].id)
      notify.success(`Successfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const tableRef = ref(null)

</script>