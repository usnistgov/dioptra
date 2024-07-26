<template>
  <PageTitle title="Artifacts" />
  <TableComponent
    :rows="artifacts"
    :columns="columns"
    title="Artifacts"
    v-model:selected="selected"
    @edit="editing = true; showAddEditDialog = true"
    @delete="showDeleteDialog = true"
    :showExpand="true"
    @request="getArtifacts"
    ref="tableRef"
    :hideDeleteBtn="true"
  >
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #expandedSlot="{ row }">
      <!-- <BasicTable
        :columns="fileColumns"
        :rows="row?.versions || []"
        :hideSearch="true"
        :hideEditTable="true"
        class="q-mx-md"
        :title="`${row.name} Versions`"
      /> -->
    </template>
  </TableComponent>
  <!-- <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    @click="showAddEditDialog = true"
  >
    <span class="sr-only">Register a new Artifact</span>
    <q-tooltip>
      Register a new Artifact
    </q-tooltip>
  </q-btn> -->
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
    :name="selected.length ? selected[0].name : ''"
  />
  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    @submitTags="submitTags"
  />
</template>

<script setup>
import TableComponent from '@/components/TableComponent.vue'
import BasicTable from '@/components/BasicTable.vue'
import ArtifactsDialog from '@/dialogs/ArtifactsDialog.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import { ref, watch } from 'vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import PageTitle from '@/components/PageTitle.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

const selected = ref([])
const editing = ref(false)

const showAddEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showTagsDialog = ref(false)

watch(showAddEditDialog, (newVal) => {
  if(!newVal) editing.value = false
})

const artifacts = ref([])

async function getArtifacts(pagination) {
  try {
    const res = await api.getData('artifacts', pagination)
    artifacts.value = res.data.data
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    console.log('err = ', err)
    notify.error(err.response.data.message)
  } 
}

const columns = [
  { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: false },
  { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true },
  { name: 'uri', label: 'uri', align: 'left', field: 'uri', sortable: true },
  // { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
]

async function addArtifact(name, group, description) {
  try {
    const res = await api.addItem('models', {
      name,
      description,
      group
    })
    showAddEditDialog.value = false
    notify.success(`Sucessfully created '${res.data.name}'`)
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response.data.message)
  } 
}

async function deleteModel() {
  try {
    await api.deleteItem('models', selected.value[0].id)
    notify.success(`Sucessfully deleted '${selected.value[0].name}'`)
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
    notify.success(`Sucessfully updated artifact`)
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
    notify.success(`Sucessfully updated Tags for '${editObjTags.value.name}'`)
    tableRef.value.refreshTable()
  } catch(err) {
    console.log('err = ', err)
    notify.error(err.response.data.message);
  }
}

</script>