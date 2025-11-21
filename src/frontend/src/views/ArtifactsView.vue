<template>
  <PageTitle title="Artifacts" />
  <TableComponent
    :rows="artifacts"
    :columns="columns"
    title="Artifacts"
    v-model:selected="selected"
    @edit="router.push(`/artifacts/${selected[0].id}`)"
    @delete="showDeleteDialog = true"
    @request="getArtifacts"
    ref="tableRef"
    :hideCreateBtn="true"
    :hideDeleteBtn="true"
    :loading="isLoading"
  >
    <template #body-cell-job="props">
      <q-btn
        color="primary"
        :to="`/jobs/${props.row.job}`"
        :label="`View Job ${props.row.job}`"
      />
    </template>
    <template #body-cell-taskName="props">
      {{ props.row.task.name }}
    </template>
    <template #body-cell-taskOutputParams="props">
      <q-chip
        v-for="param in props.row.task.outputParams"
        color="purple"
        text-color="white"
        dense
      >
        {{ param.name }}: {{ param.parameterType.name }}
      </q-chip>
    </template>
    <template #body-cell-download="props">
      <q-btn
        :href="props.row.fileUrl"
        :download="`artifact-${props.row?.id}`"
        color="primary"
        round
        icon="download"
        size="sm"
        @click.stop
      />
    </template>
  </TableComponent>

  <ArtifactsDialog 
    v-model="showAddEditDialog"
    @addArtifact="addArtifact"
    @updateArtifact="updateArtifact"
    :editArtifact="selected.length && editing ? selected[0] : ''"
  />
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteModel"
    type="Model"
    :name="selected.length ? selected[0].description : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    @submitTags="submitTags"
  />
</template>

<script setup>
import TableComponent from '@/components/TableComponent.vue'
import ArtifactsDialog from '@/dialogs/ArtifactsDialog.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import { ref, watch } from 'vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import PageTitle from '@/components/PageTitle.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const selected = ref([])
const editing = ref(false)

const showAddEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showTagsDialog = ref(false)

watch(showAddEditDialog, (newVal) => {
  if(!newVal) editing.value = false
})

const artifacts = ref([])

const isLoading = ref(false)

async function getArtifacts(pagination) {
  isLoading.value = true
  const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300)); 
  if(!pagination.sortBy) {
    pagination.sortBy = 'job'
    pagination.descending = true
  }
  try {
    const [res] = await Promise.all([
      api.getData('artifacts', pagination),
      minLoadTimePromise
    ]);
    
    artifacts.value = res.data.data
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    console.log('err = ', err);
    notify.error(err.response.data.message);
  } finally {
    isLoading.value = false;
  }
}

const columns = [
  { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false, },
  { name: 'description', label: 'Description', field: 'description', align: 'left', sortable: true },
  { name: 'job', label: 'Job', align: 'left' },
  { name: 'taskName', label: 'Task Name', align: 'left' },
  { name: 'taskOutputParams', label: 'Task Output Params', align: 'left' },
  { name: 'download', label: 'Download', align: 'center' },
]

async function addArtifact(name, group, description) {
  try {
    const res = await api.addItem('models', {
      name,
      description,
      group
    })
    showAddEditDialog.value = false
    notify.success(`Successfully created '${res.data.name}'`)
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

async function deleteModel() {
  try {
    await api.deleteItem('models', selected.value[0].id)
    notify.success(`Successfully deleted '${selected.value[0].description}'`)
    showDeleteDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

const fileColumns = [
  { name: 'versionNumber', label: 'versionNumber', align: 'left', field: 'versionNumber', sortable: true, },
  { name: 'url', label: 'URL', align: 'left', field: 'url', sortable: true, },
]

const tableRef = ref(null)

async function updateArtifact(id, description) {
  try {
    await api.updateItem('artifacts', id, { description })
    notify.success(`Successfully updated artifact`)
    showAddEditDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

const editObjTags = ref({})

function handleTags(obj) {
  editObjTags.value = obj
  showTagsDialog.value = true
}

async function submitTags(selectedTagIDs) {
  showTagsDialog.value = false
  try {
    await api.updateTags('artifacts', editObjTags.value.id, selectedTagIDs)
    notify.success(`Successfully updated Tags for '${editObjTags.value.name}'`)
    tableRef.value.refreshTable()
  } catch(err) {
    console.log('err = ', err)
    notify.error(err.response.data.message);
  }
}

</script>