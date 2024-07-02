<template>
  <PageTitle :title="title" />
  <TableComponent 
    :rows="[]"
    :columns="columns"
    title="Jobs"
    v-model:selected="selected"
    @request="getJobs"
    ref="tableRef"
  />

  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    @click="showJobsDialog = true"
  >
    <span class="sr-only">Create a new Job</span>
    <q-tooltip>
      Create a new Job
    </q-tooltip>
  </q-btn>

</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useRoute } from 'vue-router'
  import PageTitle from '@/components/PageTitle.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'

  const route = useRoute()

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: true, },
    { name: 'status', label: 'Status', align: 'left', field: 'status', sortable: true },
  ]

  const selected = ref([])

  const title = ref('')
  getExperiment()
  async function getExperiment() {
    try {
      const res = await api.getItem('experiments', route.params.id)
      title.value = `${res.data.name} Jobs`
    } catch(err) {
      console.log('err = ', err)
    } 
  }

  const jobs = ref([])
  const showJobsDialog = ref(false)

  const tableRef = ref(null)

  async function getJobs(pagination, showDrafts) {
    try {
      const res = await api.getJobs(route.params.id, pagination, showDrafts)
      console.log('jobs res = ', res)
      jobs.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      console.log('err = ', err)
      notify.error(err.response.data.message)
    } 
  }

</script>