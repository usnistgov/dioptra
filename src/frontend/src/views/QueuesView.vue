<template>
  <TableComponent 
    :rows="queues"
    :columns="columns"
    title="Queues"
    @delete="showDeleteDialog = true"
    @edit="editing = true; showAddDialog = true"
    v-model="selected"
    @request="getQueues"
    ref="tableRef"
  >
    <template #body-cell-tags="props">
      <q-chip
        v-for="(tag, i) in props.row.tags"
        :key="i"
        color="primary" 
        text-color="white"
      >
        {{ tag.name }}
      </q-chip>
      <q-btn
        round
        size="sm"
        icon="add"
        @click.stop="handleTags(props.row)"
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
    <span class="sr-only">Register a new Queue</span>
    <q-tooltip>
      Register a new Queue
    </q-tooltip>
  </q-btn>
  <AddQueueDialog 
    v-model="showAddDialog"
    @addQueue="registerQueue"
    @updateQueue="updateQueue"
    @saveDraft="saveDraft"
    :editQueue="selected.length && editing ? selected[0] : ''"
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
    @submitTags="submitTags"
  />
</template>

<script setup>
  import * as api from '@/services/dataApi'
  import { ref, watch } from 'vue'
  import * as notify from '../notify'
  import TableComponent from '@/components/TableComponent.vue'
  import AddQueueDialog from '@/dialogs/AddQueueDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

  const store = useLoginStore()

  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)

  const queues = ref([])

  const tableRef = ref(null)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    // { name: 'id', label: 'Queue ID', align: 'left', field: 'id', sortable: true },
    // { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', format: val => `${formatDate(val)}`, sortable: true },
    // { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', format: val => `${formatDate(val)}`, sortable: true },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
  ]

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

  async function registerQueue(name, description) {
    try {
      await api.addItem('queues', {
        name,
        description: description || '',
        group: store.loggedInGroup.id
      })
      notify.success(`Sucessfully created '${name}'`)
      showAddDialog.value = false
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
      await api.addDraft('queues', id, params)
      notify.success(`Sucessfully created draft '${name}'`)
      showAddDialog.value = false
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function updateQueue(name, id, description) {
    try {
      await api.updateItem('queues', id, { name, description })
      notify.success(`Sucessfully edited '${name}'`)
      showAddDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  function formatDate(dateString) {
    const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true };
    return new Date(dateString).toLocaleString('en-US', options);
  }

  const selected = ref([])
  const editing = ref(false)

  watch(showAddDialog, (newVal) => {
    if(!newVal) editing.value = false
  })

  async function deleteQueue() {
    try {
      await api.deleteItem('queues', selected.value[0].id)
      notify.success(`Sucessfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const editObjTags = ref({})

  function handleTags(obj) {
    editObjTags.value = obj
    showTagsDialog.value = true
  }

  async function submitTags(selectedTagIDs) {
    showTagsDialog.value = false
    try {
      await api.updateTags('queues', editObjTags.value.id, selectedTagIDs)
      notify.success(`Sucessfully updated Tags for '${editObjTags.value.name}'`)
      tableRef.value.refreshTable()
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message);
    }
  }

</script>
