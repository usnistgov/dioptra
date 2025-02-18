<template>
  <PageTitle title="Models" />
  <TableComponent
    :rows="models"
    :columns="columns"
    title="Models"
    v-model:selected="selected"
    @edit="editing = true; showAddEditDialog = true"
    @delete="showDeleteDialog = true"
    :showExpand="true"
    @request="getModels"
    ref="tableRef"
    @expand="getVersions"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="showAddEditDialog = true"
  >
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #expandedSlot="{ row }">
      <TableComponent
        :columns="versionColumns"
        :rows="row?.versionsData || []"
        :hideSearch="true"
        :hideEditTable="true"
        class="q-mx-md q-mb-lg"
        :title="`${row.name} Versions`"
        :disableSelect="true"
        :hideCreateBtn="true"
        :hideOpenBtn="true"
      >
        <template #body-cell-createdOn="props">
          <div>{{ formatDate(props.row.createdOn) }}</div>
        </template>
      </TableComponent>
    </template>
  </TableComponent>

  <ModelsDialog 
    v-model="showAddEditDialog"
    @addModel="addModel"
    @updateModel="updateModel"
    :editModel="selected.length && editing ? selected[0] : ''"
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
    type="models"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
import TableComponent from '@/components/TableComponent.vue'
import ModelsDialog from '@/dialogs/ModelsDialog.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import { ref, watch } from 'vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import PageTitle from '@/components/PageTitle.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
import { useLoginStore } from '@/stores/LoginStore'

const store = useLoginStore()

const selected = ref([])
const editing = ref(false)

const showAddEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showTagsDialog = ref(false)
const editObjTags = ref({})

watch(showAddEditDialog, (newVal) => {
  if(!newVal) editing.value = false
})

const models = ref([])

async function getModels(pagination) {
  try {
    const res = await api.getData('models', pagination)
    models.value = res.data.data
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    console.log('err = ', err)
    notify.error(err.response.data.message)
  } 
}

const columns = [
  { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true,  },
  { name: 'description', label: 'Description', field: 'description',align: 'left', sortable: true },
  { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true },
  { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
  { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
]

async function addModel(name, group, description) {
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
    notify.success(`Successfully deleted '${selected.value[0].name}'`)
    showDeleteDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

const versionColumns = [
  { name: 'versionNumber', label: 'Version', align: 'left', field: 'versionNumber', sortable: true, },
  { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, },
  { name: 'artifactURI', label: 'Artifact URI', align: 'left', field: row => row.artifact.artifactUri, sortable: true, },
  { name: 'artifactURL', label: 'Artifact URL', align: 'left', field: row => row.artifact.url, sortable: true, },
  { name: 'createdOn', label: 'Created On', align: 'left', field: 'createdOn', sortable: true, },
]

const tableRef = ref(null)

async function updateModel(name, id, description) {
  try {
    await api.updateItem('models', id, { name, description })
    notify.success(`Successfully updated '${name}'`)
    showAddEditDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response.data.message)
  }
}

async function getVersions(row) {
  try {
    const res = await api.getVersions(row.id)
    models.value.find((model) => model.id === row.id).versionsData = res.data.data
  } catch(err) {
    console.warn(err)
  }
}

function formatDate(dateString) {
  const options = { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true }
  return new Date(dateString).toLocaleString('en-US', options)
}

watch(() => store.triggerPopup, (newVal) => {
  if(newVal) {
    showAddEditDialog.value = true
    store.triggerPopup = false
  }
})

</script>