<template>
  <PageTitle :title="`${title} Files`" />
  <TableComponent 
    :rows="files"
    :columns="fileColumns"
    title="Plugin Files"
    v-model:selected="selected"
    @edit="router.push(`/plugins/${route.params.id}/files/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    @request="getFiles"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push(`/plugins/${route.params.id}/files/new`)"
  >
    <template #body-cell-functionTasks="props">
      {{ props.row.tasks.functions.length }}
    </template>
    <template #body-cell-artifactTasks="props">
      {{ props.row.tasks.artifacts.length }}
    </template>
  </TableComponent>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteFile"
    type="Plugin File"
    :name="selected.length ? selected[0].filename : ''"
  />

  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="files"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { useRoute, useRouter } from 'vue-router'
  import { ref, computed } from 'vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

  const route = useRoute()
  const router = useRouter()

  const selected = ref([])
  const showDeleteDialog = ref(false)
  const showTagsDialog = ref(false)
  const editObjTags = ref({})

  const tableRef = ref(null)

  const fileColumns = [
    { name: 'filename', label: 'Filename', align: 'left', field: 'filename', sortable: true, },
    { name: 'description', label: 'Description', field: 'description', align: 'left', sortable: true },
    { name: 'functionTasks', label: 'Function Tasks', align: 'left', sortable: false, },
    { name: 'artifactTasks', label: 'Artifact Tasks', align: 'left', sortable: false, },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
  ]

  const files = ref([])

  const title = ref('')

  getPluginName()
  async function getPluginName() {
    try {
      const res = await api.getItem('plugins', route.params.id)
      title.value = res.data.name
    } catch(err) {
      console.log(err)
    } 
  }


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
      notify.success(`Successfully deleted '${selected.value[0].filename}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }
  

</script>