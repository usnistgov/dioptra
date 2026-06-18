<template>
  <PageTitle 
    title="Queues" 
    resourceType="queue"
    subtitle="Manage Job execution for specific worker environments"
  />
  <TableComponent 
    :rows="rows"
    :columns="showDrafts ? draftColumns : columns"
    title="Queues"
    @delete="showDeleteDialog = true"
    @open="openQueue($event)"
    v-model:selected="selected"
    v-model:showDrafts="showDrafts"
    v-model:showDeleted="showDeleted"
    @request="getData"
    ref="tableRef"
    :showToggleDraft="true"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/queues/new')"
    :loading="isLoading"
    :showDeletedToggle="!showDrafts"
  >
    <template #body-cell-hasDraft="props">
      <q-btn
        v-show="!props.row.deleted"
        round
        size="sm"
        :icon="props.row.hasDraft ? 'edit' : 'add'"
        :color="props.row.hasDraft ? 'primary' : 'grey-5'"
        @click.stop="router.push(`/queues/${props.row.id}/resourceDraft/${props.row.hasDraft ? '' : 'new'}`)"
      />
    </template>
  </TableComponent>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteRow(!Object.hasOwn(selected[0], 'hasDraft'))"
    type="Queue"
    :name="selected.length ? selected[0].name : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="queues"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
  import { ref } from 'vue'
  import TableComponent from '@/components/TableComponent.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import { useRouter } from 'vue-router'
  import { useTableUtils } from '@/services/useTableUtils'

  const router = useRouter()

  const showTagsDialog = ref(false)

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true },
    { name: 'hasDraft', label: 'hasDraft', align: 'left', field: 'hasDraft', sortable: false },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
  ]

  const draftColumns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
  ]

  const showDrafts = ref(false)

  const {
    rows,
    isLoading,
    showDeleted,
    tableRef,
    selected,
    showDeleteDialog,
    getData,
    deleteRow,
  } = useTableUtils('queues')

  const editObjTags = ref({})

  function openQueue(openTab) {
    const url = selected.value[0].payload
      ? `/queues/${selected.value[0].id}/draft`
      : `/queues/${selected.value[0].id}`

    if(openTab) window.open(url, '_blank', 'noopener,noreferrer')
    else router.push(url)
  }

</script>
