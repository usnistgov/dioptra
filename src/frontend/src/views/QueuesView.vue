<template>
  <PageTitle title="Queues" />
  <TableComponent 
    :rows="queues"
    :columns="showDrafts ? columns.slice(0, -2) : columns"
    title="Queues"
    @delete="showDeleteDialog = true"
    @edit="editing = true; showQueueDialog = true"
    v-model:selected="selected"
    v-model:showDrafts="showDrafts"
    @request="getQueues"
    ref="tableRef"
    :showToggleDraft="true"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
  >
    <template #body-cell-hasDraft="props">
      <q-btn
        round
        size="sm"
        :icon="props.row.hasDraft ? 'edit' : 'add'"
        :color="props.row.hasDraft ? 'primary' : 'grey-5'"
        @click.stop="queueToDraft = props.row; showDraftDialog = true"
      />
    </template>
  </TableComponent>
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    @click="showQueueDialog = true"
  >
    <span class="sr-only">Register a new Queue</span>
    <q-tooltip>
      Register a new Queue
    </q-tooltip>
  </q-btn>
  <QueueDialog 
    v-model="showQueueDialog"
    @addQueue="addQueue"
    @updateQueue="updateQueue"
    @saveDraft="saveDraft"
    :editQueue="selected.length && editing ? selected[0] : ''"
  />
  <QueueDraftDialog 
    v-model="showDraftDialog"
    @addQueue="addQueue"
    @updateDraftLinkedToQueue="updateDraftLinkedToQueue"
    :queueToDraft="queueToDraft"
  />
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
  import { ref, watch } from 'vue'
  import * as notify from '../notify'
  import TableComponent from '@/components/TableComponent.vue'
  import QueueDialog from '@/dialogs/QueueDialog.vue'
  import QueueDraftDialog from '@/dialogs/QueueDraftDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'

  const store = useLoginStore()

  const showQueueDialog = ref(false)
  const showDraftDialog = ref(false)
  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)

  const queues = ref([])
  const queueToDraft = ref(false)

  const tableRef = ref(null)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    // { name: 'id', label: 'Queue ID', align: 'left', field: 'id', sortable: true },
    // { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', format: val => `${formatDate(val)}`, sortable: true },
    // { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', format: val => `${formatDate(val)}`, sortable: true },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true },
    { name: 'hasDraft', label: 'hasDraft', align: 'left', field: 'hasDraft', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
  ]

  const selected = ref([])
  const showDrafts = ref(false)

  async function getQueues(pagination, showDrafts) {
    try {
      const res = await api.getData('queues', pagination, showDrafts);
      queues.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

  async function addQueue(name, description, id) {
    console.log(name, description,id)
    let params = {
      name,
      description,
    }
    if(!id) {
      params.group = store.loggedInGroup.id
    }
    try {
      if(id) await api.addDraft('queues', params, id)
      else await api.addItem('queues', params)
      notify.success(`Successfully created '${name}'`)
      showQueueDialog.value = false
      showDraftDialog.value = false
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function saveDraft(name, description, id) {
    let params = {
      name: name,
      description: description,
    }
    if(!id) {
      params.group = store.loggedInGroup.id
    }
    try {
      await api.addDraft('queues', params, id)
      notify.success(`Successfully created draft '${name}'`)
      showQueueDialog.value = false
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function updateQueue(name, id, description, draft = false) {
    try {
      if(draft) {
        await api.updateDraft('queues', id, { name, description })
      } else {
        await api.updateItem('queues', id, { name, description })
      }
      notify.success(`Successfully updated Queue '${name}'`)
      showQueueDialog.value = false
      showDraftDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function updateDraftLinkedToQueue(queueId, name, description) {
    try {
      await api.updateDraftLinkedtoQueue(queueId, name, description)
      notify.success(`Successfully updated '${name}'`)
      showDraftDialog.value = false
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  function formatDate(dateString) {
    const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true }
    return new Date(dateString).toLocaleString('en-US', options)
  }



  const editing = ref(false)

  watch(showQueueDialog, (newVal) => {
    if(!newVal) editing.value = false
  })

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

</script>
