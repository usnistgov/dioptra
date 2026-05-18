<template>
  <PageTitle 
    title="Plugin Parameters"
    resourceType="parameterType"
    subtitle="Handle type validation in Entrypoints"
  />
  <TableComponent
    :rows="rows"
    :columns="columns"
    title="Plugin Parameter Types"
    v-model:selected="selected"
    v-model:showDeleted="showDeleted"
    :showDeletedToggle="true"
    @open="openTab => (openTab
      ? openWindow.open(`/pluginParams/${selected[0].id}`, '_blank')
      : router.push(`/pluginParams/${selected[0].id}`)
    )"
    @delete="showDeleteDialog = true"
    @request="getData"
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
    @submit="deleteRow"
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
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import { useRouter } from 'vue-router'
  import { useTableUtils } from '@/services/useTableUtils'

  const openWindow = window
  const router = useRouter()

  const showAddDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const editing = ref(false)

  watch(showAddDialog, (newVal) => {
  if(!newVal) editing.value = false
  })

  const {
    rows,
    isLoading,
    showDeleted,
    tableRef,
    selected,
    showDeleteDialog,
    getData,
    deleteRow,
  } = useTableUtils('pluginParameterTypes')

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', field: 'description', align: 'left', sortable: true },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
  ]

</script>
