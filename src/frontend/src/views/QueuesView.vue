<template>
  <PageTitle 
    title="Queues" 
    resourceType="queue"
    subtitle="Manage Job execution for specific worker environments"
  />
  <TableComponent 
    :rows="queues"
    :columns="showDrafts ? draftColumns : columns"
    title="Queues"
    @delete="showDeleteDialog = true"
    @open="openQueue($event)"
    v-model:selected="selected"
    v-model:showDrafts="showDrafts"
    v-model:showDeleted="showDeleted"
    @request="getQueues"
    ref="tableRef"
    :showToggleDraft="true"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/queues/new')"
    :loading="isLoading"
    :showDeletedToggle="true"
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
    @submit="deleteQueue"
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
  import * as api from '@/services/dataApi'
  import { ref } from 'vue'
  import * as notify from '../notify'
  import TableComponent from '@/components/TableComponent.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const showDeleteDialog = ref(false)
  const showDeleted = ref(false)
  const showTagsDialog = ref(false)

  const queues = ref([])

  const isLoading = ref(false)

  const tableRef = ref(null)

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

  const selected = ref([])
  const showDrafts = ref(false)

  async function getQueues(pagination, showDrafts) {
    isLoading.value = true
    const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300)); 

    try {
      const [res] = await Promise.all([
        api.getData('queues', pagination, showDrafts, showDeleted.value),
        minLoadTimePromise
      ]);
        
      queues.value = res.data.data;
      tableRef.value.updateTotalRows(res.data.totalNumResults);
    } catch(err) {
      console.log('err = ', err);
      notify.error(err.response.data.message);
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteQueue() {
    try {
      if(Object.hasOwn(selected.value[0], 'hasDraft')) {
        await api.deleteItem('queues', selected.value[0].id)
      } else {
        await api.deleteDraft('queues', selected.value[0].id)
      }
      notify.success(`Successfully deleted Queue '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const editObjTags = ref({})

  function openQueue(openTab) {
    const url = selected.value[0].payload
      ? `/queues/${selected.value[0].id}/draft`
      : `/queues/${selected.value[0].id}`

    if(openTab) window.open(url, '_blank', 'noopener,noreferrer')
    else router.push(url)
  }

</script>
