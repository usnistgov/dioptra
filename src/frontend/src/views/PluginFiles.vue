<template>
  <TableComponent 
    :rows="files"
    :columns="fileColumns"
    title="Plugin Files"
    v-model="selected"
    :pagination="{sortBy: 'draft', descending: true}"
    @edit="store.editMode = true; router.push(`/plugins/${route.params.id}/files/${selected[0].id}`)"
    :showExpand="true"
  />
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    :to="`/plugins/${route.params.id}/files/new`"
  >
    <span class="sr-only">Create New Plugin File</span>
    <q-tooltip>
      Create New Plugin File
    </q-tooltip>
  </q-btn>
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRoute, useRouter } from 'vue-router'
  import { ref, computed } from 'vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'

  const route = useRoute()
  const router = useRouter()

  const store = useDataStore()

  const selected = ref([])

  const fileColumns = [
    // field must be name or else selection doesn't work, possible quasar bug
    { name: 'filename', label: 'Filename', align: 'left', field: 'name', sortable: true, },
    { name: 'tasks', label: 'Number of Tasks', align: 'left', field: 'tasks', sortable: true, },
  ]

  const files = ref([])

  getFiles()
  async function getFiles() {
    try {
      const res = await api.getFiles(route.params.id)
      files.value = res.data
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  

</script>