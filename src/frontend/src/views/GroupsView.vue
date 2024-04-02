<template>
  <TableComponent 
    :rows="store.groups"
    :columns="columns"
    title="Groups"
    @delete="showDeleteDialog = true"
    @edit="dataStore.editMode = true; router.push('/groups/admin')"
    v-model="selected"
  >
    <template #body-cell="props">
      <q-td :props="props">
        <q-badge color="blue" :label="props.value" />
      </q-td>
    </template>
  </TableComponent>
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    to="/groups/admin"
  >
    <span class="sr-only">Create a new Group</span>
    <q-tooltip>
      Create a new Group
    </q-tooltip>
  </q-btn>
  <AddQueueDialog 
    v-model="showAddDialog"
    @addQueue="registerQueue"
    @updateQueue="updateQueue"
    :editQueue="selected.length && editing ? selected[0] : ''"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteQueue"
    type="Queue"
    :name="selected.length ? selected[0].name : ''"
  />
</template>

<script setup>
  import * as api from '@/services/queuesApi'
  import { ref, watch } from 'vue'
  import * as notify from '../notify';
  import TableComponent from '@/components/TableComponent.vue'
  import AddQueueDialog from '@/dialogs/AddQueueDialog.vue'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import { useDataStore } from '@/stores/DataStore'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const store = useLoginStore()
  const dataStore = useDataStore()

  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)

  const queues = ref([])

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'read', label: 'Read', align: 'left', field: 'read', sortable: true },
    { name: 'write', label: 'Write', align: 'left', field: 'write', sortable: true },
    { name: 'shareRead', label: 'Share Read', align: 'left', field: 'shareRead', sortable: true, style: 'width: 200px' },
    { name: 'shareWrite', label: 'Share Write', align: 'left', field: 'shareWrite', sortable: true, style: 'width: 200px' },
    { name: 'admin', label: 'Admin', align: 'left', field: 'admin', sortable: true },
    { name: 'owner', label: 'Owner', align: 'left', field: 'owner', sortable: true },
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
