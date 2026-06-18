<template>
  <PageTitle 
    title="Experiments" 
    resourceType="experiment" 
    subtitle="Containers for logically organizing Entrypoints and Jobs" 
  />
  <TableComponent 
    :rows="rows"
    :columns="columns"
    title="Experiments"
    v-model:selected="selected"
    v-model:showDeleted="showDeleted"
    :showDeletedToggle="true"
    @open="openTab => (openTab
      ? openWindow.open(`/experiments/${selected[0].id}`, '_blank')
      : router.push(`/experiments/${selected[0].id}`)
    )"
    @delete="showDeleteDialog = true"
    @request="getData"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/experiments/new')"
    :loading="isLoading"
  />

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteRow"
    type="Experiment"
    :name="selected.length ? selected[0].name : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="experiments"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import { useTableUtils } from '@/services/useTableUtils'
  
  const router = useRouter()
  const openWindow = window

  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false, },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true },
    { name: 'entrypoints', label: 'Entrypoints', align: 'left', field: 'entrypoints', sortable: false, resourceType: 'entrypoint' },
    { name: 'tags', label: 'Tags', align: 'left', sortable: false },
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
  } = useTableUtils('experiments')

</script>
