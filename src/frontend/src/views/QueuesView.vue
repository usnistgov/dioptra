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

  <q-dialog v-model="showAddDialog">
    <q-card style="width: 95%" flat >
      <q-form @submit="submit">
        <q-card-section class="bg-primary text-white q-mb-md">
          <div class="text-h6">Register Queue</div>
        </q-card-section>
        <q-card-section class="">
          <div class="row items-center">
            <div class="col-3 q-mb-lg">
              Queue Name:
            </div>
            <q-input class="col" outlined dense v-model="name" autofocus :rules="[rules.requiredRule]" >
            </q-input>
          </div>
        </q-card-section>
        <q-card-actions align="right" class="text-primary">
          <q-btn flat label="Cancel" @click="showAddDialog = false" outline />
          <q-btn flat label="Confirm" type="submit" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>

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
  import * as rules from '@/services/validationRules'
  import { onMounted, ref, reactive } from 'vue'
  import * as notify from '../notify';
  import TableComponent from '@/components/TableComponent.vue'

  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)

  const name = ref('')

  const queues = ref([])


  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'id', label: 'Queue ID', align: 'left', field: 'queueId', sortable: true },
    { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', format: val => `${formatDate(val)}`, sortable: true },
    { name: 'lastModified', label: 'Last Modified', align: 'left', field: 'lastModified', format: val => `${formatDate(val)}`, sortable: true },
  ]

  // onMounted(async () => {
  //   try {
  //     const res = await api.getQueues();
  //     console.log('queues res = ', res)
  //     queues.value = res.data
  //   } catch(err) {
  //     console.log('queues err = ', err)
  //   } finally {
  //     // $q.loading.hide();
  //   }
  // })

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

  async function submit() {
    try {
      console.log('submitted!!!!!!!!!!!')
      await api.registerQueue(name.value)
      notify.success(`Sucessfully created '${name.value}'`)
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