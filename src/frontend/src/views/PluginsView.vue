<template>
  <PageTitle 
    title="Plugins" 
    resourceType="plugin" 
    subtitle="Units of code that define Tasks" 
  />

  <TableComponent
    :rows="rows"
    :columns="columns"
    title="Plugins"
    v-model:selected="selected"  
    @open="openTab => (openTab
      ? openWindow.open(`/plugins/${selected[0].id}`, '_blank')
      : router.push(`/plugins/${selected[0].id}`)
    )"
    @delete="showDeleteDialog = true"
    @request="getData"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/plugins/new')"
    :loading="isLoading"
  >

    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #body-cell-files="props">
      {{ props.row.files?.length }}
    </template>
  </TableComponent>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteRow"
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
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import { useTableUtils } from '@/services/useTableUtils'

  const openWindow = window

  const router = useRouter()

  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const {
    rows,
    isLoading,
    showDeleted,
    tableRef,
    selected,
    showDeleteDialog,
    getData,
    deleteRow,
  } = useTableUtils('plugins')

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false, },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: true },
    { name: 'files', label: 'Number of Files', align: 'left', field: 'files', sortable: false },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
  ]

</script>
