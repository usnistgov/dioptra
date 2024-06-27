<template>
  <TableComponent 
    :rows="files"
    :columns="fileColumns"
    title="Plugin Files"
    v-model:selected="selected"
    @edit="store.editMode = true; router.push(`/plugins/${route.params.id}/files/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    :showExpand="true"
    @request="getFiles"
    ref="tableRef"
  >
    <template #body-cell-tasks="props">
      {{ props.row.tasks.length }}
    </template>
  </TableComponent>
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

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteFile"
    type="Plugin File"
    :name="selected.length ? selected[0].filename : ''"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRoute, useRouter } from 'vue-router'
  import { ref, computed } from 'vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
    import DeleteDialog from '@/dialogs/DeleteDialog.vue'

  const route = useRoute()
  const router = useRouter()

  const store = useDataStore()

  const selected = ref([])
  const showDeleteDialog = ref(false)

  const tableRef = ref(null)

  const fileColumns = [
    // field must be name or else selection doesn't work, possible quasar bug
    { name: 'filename', label: 'Filename', align: 'left', field: 'filename', sortable: true, },
    { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: false },
    { name: 'tasks', label: 'Tasks', align: 'left', field: 'tasks', sortable: true, },
  ]

  const files = ref([])

  async function getFiles(pagination) {
    try {
      const res = await api.getFiles(route.params.id, pagination)
      console.log('getFiles = ', res)
      files.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  async function deleteFile() {
    try {
      await api.deleteFile(route.params.id, selected.value[0].id)
      notify.success(`Sucessfully deleted '${selected.value[0].filename}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }
  

</script>