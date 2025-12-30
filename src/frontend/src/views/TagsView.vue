<template>
  <PageTitle title="Tags" />
  
  <TableComponent 
    ref="tableRef"
    :rows="tags"
    :columns="computedColumns"
    title="Tags"
    v-model:selected="selected"
    :loading="isLoading"
    :hideToggleDraft="true"
    
    @request="getTags"
    @create="showAddDialog = true"
    @edit="editing = true; showAddDialog = true"
    @delete="(row) => { selected = [row]; showDeleteDialog = true }"
  />

  <AddTagsDialog 
    v-model="showAddDialog"
    @addTag="addTag"
    @updateTag="updateTag"
    :editTag="selected.length && editing ? selected[0] : ''"
  />

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteTag"
    type="Tag"
    :name="selected[0]?.name || ''"
  />
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'

// Components
import TableComponent from '@/components/table/TableComponent.vue'
import PageTitle from '@/components/PageTitle.vue'
import AddTagsDialog from '@/dialogs/AddTagsDialog.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'

const tableRef = ref(null)
const tags = ref([])
const isLoading = ref(false)
const selected = ref([])
const editing = ref(false)
const showAddDialog = ref(false)
const showDeleteDialog = ref(false)

// Logic to reset editing state
watch(showAddDialog, (newVal) => {
  if (!newVal) editing.value = false
})

// Column Definitions
const computedColumns = computed(() => [
  { 
    name: 'id', 
    label: 'ID', 
    field: 'id', 
    align: 'left', 
    styleType: 'icon-badge', 
    conceptType: 'tag',
    includeIcon: true,
    formatLabel: '{label}',
  },
  { 
    name: 'name', 
    label: 'Tag Name', 
    field: 'name', 
    align: 'left', 
    styleType: 'resource-name', 
    conceptType: 'tag',
    sortable: true 
  },
  { 
    name: 'createdOn', 
    label: 'Created On', 
    field: 'createdOn', 
    align: 'left', 
    styleType: 'date',
    textColor: 'text-grey-10',
    sortable: true 
  },
  { 
    name: 'lastModifiedOn', 
    label: 'Last Modified', 
    field: 'lastModifiedOn', 
    align: 'left', 
    styleType: 'date',
    textColor: 'text-grey-10',
    sortable: true 
  }
])

// --- API ACTIONS ---

async function getTags(pagination) {
  isLoading.value = true
  try {
    const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300))
    const [res] = await Promise.all([
      api.getData('tags', pagination),
      minLoadTimePromise
    ])
    
    tags.value = res.data.data
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    notify.error(err.response?.data?.message || 'Failed to fetch tags')
  } finally {
    isLoading.value = false
  }
}

async function addTag(name, group) {
  try {
    await api.addItem('tags', { name, group })
    notify.success(`Successfully created tag '${name}'`)
    showAddDialog.value = false
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response?.data?.message)
  }
}

async function updateTag(name, id) {
  try {
    await api.updateItem('tags', id, { name })
    notify.success(`Successfully edited Tag '${name}'`)
    showAddDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response?.data?.message)
  }
}

async function deleteTag() {
  try {
    const id = selected.value[0].id
    await api.deleteItem('tags', id)
    notify.success(`Successfully deleted Tag '${selected.value[0].name}'`)
    showDeleteDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response?.data?.message)
  }
}
</script>