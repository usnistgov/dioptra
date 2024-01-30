<template>
  <PageTitle />
  <TableComponent 
    :rows="queues"
    :columns="columns"
    title="Queues"
    @delete="deletePrompt"
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
    :showAddDialog="showAddDialog"
    @submit="registerQueue"
    @update:modelValue="(val) => showAddDialog = val"
  />

  <q-dialog v-model="showDeleteDialog">
    <q-card style="width: 95%">
      <q-card-section>
        <div class="text-h6">Confirm Delete</div>
      </q-card-section>
      <q-card-section class="q-pt-none">
        Are you sure you want to delete this Queue? <br>
        Name: <span class="text-bold">{{ selected.name }}</span>
      </q-card-section>
      <q-card-actions align="right" class="text-primary">
          <q-btn flat label="Cancel" @click="showDeleteDialog = false" outline />
          <q-btn flat label="Confirm" type="submit" @click="deleteQueue" />
        </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
  import PageTitle from '@/components/PageTitle.vue'
  import * as api from '@/services/queuesApi'
  import { ref } from 'vue'
  import * as notify from '../notify';
  import TableComponent from '@/components/TableComponent.vue'
  import AddQueueDialog from '@/dialogs/AddQueueDialog.vue'

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
      console.log('queues err = ', err)
    } 
  }

  async function registerQueue(name) {
    try {
      console.log('submitted!!!!!!!!!!!')
      await api.registerQueue(name)
      notify.success(`Sucessfully created '${name}'`)
      showAddDialog.value = false
      getQueues()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  function formatDate(dateString) {
    const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true };
    return new Date(dateString).toLocaleString('en-US', options);
  }

  const selected = ref({})
  function deletePrompt(queue) {
    console.log('delete queue? ', queue)
    selected.value = queue
    showDeleteDialog.value = true
  }

  async function deleteQueue() {
    try {
      const res = await api.deleteQueue(selected.value.name)
      console.log('delete res = ', res)
      notify.success(`Sucessfully deleted '${selected.value.name}'`)
      showDeleteDialog.value = false
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