<template>
  <PageTitle 
    title="Experiments" 
    caption="Containers for Job runs"
    conceptType="experiment" 
  />
  
  <TableComponent 
    ref="tableRef"
    :rows="experiments"
    :columns="computedColumns"
    v-model:selected="selected"
    :loading="isLoading"
    
    @request="getExperiments"
    @create="router.push('/experiments/new')"
    @edit="(row) => router.push(`/experiments/${row.id}`)"
    
    @delete="(row) => { selected = [row]; showDeleteDialog = true }"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
  />

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteExperiment"
    type="Experiment"
    :name="selected[0]?.name || ''"
  />
  
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="experiments"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import TableComponent from '@/components/table/TableComponent.vue'
import PageTitle from '@/components/PageTitle.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'

const router = useRouter()
const tableRef = ref(null)

// State
const experiments = ref([])
const isLoading = ref(false)
const selected = ref([])
const showDeleteDialog = ref(false)
const showTagsDialog = ref(false)
const editObjTags = ref({})

// Column Definitions
const computedColumns = computed(() => [
  { 
    name: 'id', 
    label: 'Experiment ID', 
    field: 'id', 
    align: 'left', 
    styleType: 'icon-id', 
    conceptType: 'experiment',
    includeIcon: true
  },
  { 
  name: 'name', 
  label: 'Experiment Name', 
  field: 'name', 
  align: 'left',
  
  styleType: 'resource-name', 
  conceptType: 'experiment',  
  
  textType: 'capitalize',
  maxWidth: '250px',
  includeIcon: false,
  sortable: true
  },

  { 
    name: 'description', 
    label: 'Description', 
    field: 'description', 
    align: 'left', 
    styleType: 'long-text',
    maxWidth: '300px',
    maxLength: 100,
    useQuotes: true,
  sortable: true
  },
  { 
    name: 'entrypoints', 
    label: 'Entry Points', 
    field: 'entrypoints', 
    align: 'left',
    styleType: 'multi-badge',  
    conceptType: 'entrypoint' 
  },
  { 
    name: 'tags', 
    label: 'Tags', 
    field: 'tags', 
    align: 'left', 
    styleType: 'tag-list' 
  }
])

// API Functions
async function getExperiments(pagination) {
  isLoading.value = true
  try {
    // Artificial delay to prevent flicker
    const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300))
    
    const [res] = await Promise.all([
      api.getData('experiments', pagination, false),
      minLoadTimePromise
    ])
    
    experiments.value = res.data.data
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    notify.error(err.response?.data?.message || 'Failed to fetch experiments')
  } finally {
    isLoading.value = false
  }
}

async function deleteExperiment() {
  try {
    const id = selected.value[0].id
    await api.deleteItem('experiments', id)
    notify.success(`Successfully deleted '${selected.value[0].name}'`)
    showDeleteDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response?.data?.message)
  }
}
</script>