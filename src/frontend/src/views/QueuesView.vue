<template>
  <TableComponent 
    :rows="queues"
    :columns="columns"
    title="Queues"
    @delete="showDeleteDialog = true"
    @edit="editing = true; showAddDialog = true"
    v-model="selected"
  >
    <!-- <template #body-cell-chips="props">
      <q-chip>
        {{ props.row.name }}
      </q-chip>
    </template> -->
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
    :editQueue="selected.length && editing ? selected[0] : ''"
  />
  <DeleteQueueDialog 
    v-model="showDeleteDialog"
    @submit="deleteQueue"
    :name="selected.length ? selected[0].name : ''"
  />
</template>

<script setup>
  import * as api from '@/services/queuesApi'
  import { ref, watch } from 'vue'
  import * as notify from '../notify';
  import TableComponent from '@/components/TableComponent.vue'
  import AddQueueDialog from '@/dialogs/AddQueueDialog.vue'
  import DeleteQueueDialog from '@/dialogs/DeleteQueueDialog.vue'

  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)

  const queues = ref([])

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'id', label: 'Queue ID', align: 'left', field: 'queueId', sortable: true },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', format: val => `${formatDate(val)}`, sortable: true },
    { name: 'lastModified', label: 'Last Modified', align: 'left', field: 'lastModified', format: val => `${formatDate(val)}`, sortable: true },
    // { name: 'chips', label: 'Custom Column Example',align: 'left', sortable: false },
  ]

  getQueues()
  async function getQueues() {
    try {
      const res = await api.getQueues();
      queues.value = res.data
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  async function registerQueue(name) {
    try {
      await api.registerQueue(name)
      notify.success(`Sucessfully created '${name}'`)
      showAddDialog.value = false
      getQueues()
    } catch(err) {
      notify.error(err.response.data.message)
    }
  }

  async function updateQueue(name, queueId) {
    try {
      await api.upadateQueue(name, queueId)
      notify.success(`Sucessfully edited '${name}'`)
      showAddDialog.value = false
      selected.value = []
      getQueues()
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
      await api.deleteQueue(selected.value[0].name)
      notify.success(`Sucessfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      getQueues()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

</script>
