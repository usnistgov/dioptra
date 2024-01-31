<template>
  <PageTitle />
  <TableComponent 
    :rows="queues"
    :columns="columns"
    title="Queues"
    @delete="deletePrompt"
    :deleteCount="deleteCount"
  />
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    @click="showAddDialog = true"
  >
    <q-tooltip>
      Register a new Queue
    </q-tooltip>
  </q-btn>
  <AddQueueDialog 
    v-model="showAddDialog"
    @submit="registerQueue"
  />
  <DeleteQueueDialog 
    v-model="showDeleteDialog"
    @submit="deleteQueue"
    :name="selected.name"
  />
</template>

<script setup>
  import PageTitle from '@/components/PageTitle.vue'
  import * as api from '@/services/queuesApi'
  import { ref } from 'vue'
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
  ]

  getQueues()
  async function getQueues() {
    try {
      const res = await api.getQueues();
      console.log('queues res = ', res)
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

  function formatDate(dateString) {
    const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true };
    return new Date(dateString).toLocaleString('en-US', options);
  }

  const selected = ref({})

  function deletePrompt(queue) {
    selected.value = queue
    showDeleteDialog.value = true
  }

  const deleteCount = ref(0)

  async function deleteQueue() {
    try {
      await api.deleteQueue(selected.value.name)
      notify.success(`Sucessfully deleted '${selected.value.name}'`)
      showDeleteDialog.value = false
      deleteCount.value ++
      getQueues()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

</script>

<style>
  .fixedButton {
      position: fixed;
      bottom: 80px;
      right: 80px; 
  }

</style>