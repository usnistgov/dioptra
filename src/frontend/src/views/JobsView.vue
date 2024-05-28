<template>
  <TableComponent 
    :rows="[]"
    :columns="columns"
    title="Jobs"
    v-model="selected"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRouter } from 'vue-router'
  
  const router = useRouter()

  const store = useDataStore()

  const experiments = store.experiments

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: true, },
    { name: 'status', label: 'Status', align: 'left', field: 'status', sortable: true },
  ]

  const selected = ref([])
</script>