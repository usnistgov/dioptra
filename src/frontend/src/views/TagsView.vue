<template>
  <PageTitle 
    title="Tags"
    resourceType="tag"
    subtitle="Keywords for organizing resources"
  />
  <TableComponent 
    :rows="rows"
    :columns="columns"
    title="Tags"
    @delete="showDeleteDialog = true"
    @open="editing = true; showAddDialog = true"
    v-model:selected="selected"
    @request="getData"
    ref="tableRef"
    @create="showAddDialog = true"
    :loading="isLoading"
  >
    <template #body-cell-name="props">
      <q-chip color="primary" text-color="white">
        {{ props.row.name }}
      </q-chip>
    </template>
  </TableComponent>

  <AddTagsDialog 
    v-model="showAddDialog"
    @addTag="addTag"
    @updateTag="updateTag"
    :editTag="selected.length && editing ? selected[0] : ''"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteRow"
    type="Tag"
    :name="selected.length ? selected[0].name : ''"
  />
</template>

<script setup>
  import * as api from '@/services/dataApi'
  import { ref, watch } from 'vue'
  import * as notify from '../notify'
  import TableComponent from '@/components/TableComponent.vue'
  import AddTagsDialog from '@/dialogs/AddTagsDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import { useTableUtils } from '@/services/useTableUtils'

  const showAddDialog = ref(false)

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
  ]

  const {
    rows,
    isLoading,
    showDeleted,
    tableRef,
    selected,
    showDeleteDialog,
    getData,
    deleteRow,
  } = useTableUtils('tags')

  async function addTag(name, group) {
    try {
      await api.addItem('tags', {
        name,
        group
      })
      notify.success(`Successfully created tag '${name}'`)
      showAddDialog.value = false
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function updateTag(name, id) {
    try {
      await api.updateItem('tags', id, { name })
      notify.success(`Successfully edited Tag '${name}'`)
      showAddDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  const editing = ref(false)

  watch(showAddDialog, (newVal) => {
    if(!newVal) editing.value = false
  })

</script>
