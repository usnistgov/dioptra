<template>
  <PageTitle :title="`${title} Files`" />
  <TableComponent 
    :rows="files"
    :columns="fileColumns"
    title="Plugin Files"
    v-model:selected="selected"
    @edit="loadFormPage()"
    @delete="showDeleteDialog = true"
    @request="getFiles"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push(`/plugins/${route.params.id}/files/new`)"
    :showToggleDraft="true"
    v-model:showDrafts="showDrafts"
  >
    <template #body-cell-tasks="props">
      {{ props.row.tasks.length }}
    </template>
    <template #body-cell-hasDraft="props">
      <q-btn
        round
        size="sm"
        :icon="props.row.hasDraft ? 'edit' : 'add'"
        :color="props.row.hasDraft ? 'primary' : 'grey-5'"
        @click.stop="router.push(
          `/plugins/${route.params.id}/files/${props.row.id}/${props.row.hasDraft ? 
          'resourceDraft' : 'newResourceDraft'}`
        )"
      />
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
    { name: 'hasDraft', label: 'Resource Draft', align: 'left', field: 'hasDraft', sortable: false },
    { name: 'tasks', label: 'Tasks', align: 'left', field: 'tasks', sortable: false, },
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


  async function getFiles(pagination, showDrafts) {
    try {
      const res = await api.getFiles(route.params.id, pagination, showDrafts)
      console.log('getFiles = ', res)
      files.value = res.data.data
      tableRef.value.updateTotalRows(res.data.totalNumResults)
    } catch(err) {
      notify.error(err.response.data.message)
    } 
  }

  async function deleteFile() {
    try {
      if(Object.hasOwn(selected.value[0], 'hasDraft')) {
        await api.deleteFile(route.params.id, selected.value[0].id)
      } else if(!showDrafts.value && !Object.hasOwn(selected.value[0], 'hasDraft')) {
        await api.deleteFile(route.params.id, selected.value[0].id, 'resourceDraft')
      } else if(showDrafts.value) {
        await api.deleteFile(route.params.id, selected.value[0].id, 'draft')
      }
      notify.success(`Successfully deleted '${selected.value[0].filename}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const showDrafts = ref(false)

  function loadFormPage() {
    if(showDrafts.value) {
      router.push(`/plugins/${route.params.id}/files/${selected.value[0].id}/draft`)
    } else {
      router.push(`/plugins/${route.params.id}/files/${selected.value[0].id}`)
    }
  }
  

</script>