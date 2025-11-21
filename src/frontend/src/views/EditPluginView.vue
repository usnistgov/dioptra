<template>
  <div class="row items-center justify-between">
    <PageTitle :title="ORIGINAL_PLUGIN?.name"/>
    <q-btn 
      color="negative"
      icon="sym_o_delete" 
      label="Delete Plugin" 
      @click="showDeletePluginDialog = true"
    />
  </div>

    <q-expansion-item
    v-model="showMetadata"
    class="shadow-1 overflow-hidden q-mt-lg"
    style="border-radius: 10px; width: 40%"
    header-style="font-size: 22px"
    header-class="bg-primary text-white"
    expand-icon-class="text-white"
    :label="`${showMetadata ? 'Hide' : 'Edit'} Plugin Metadata`"
  >
    <q-card class="q-pa-md">
      <KeyValueTable :rows="pluginRows" :secondColumnFullWidth="true">
        <template #name="{ }">
          {{ name }}
          <q-btn icon="edit" round size="sm" color="primary" flat />
          <q-popup-edit
            v-model="name" 
            auto-save 
            v-slot="scope"
            :validate="requiredRule"
          >
            <q-input 
              v-model.trim="scope.value"
              dense
              autofocus
              counter
              @keyup.enter="scope.set"
              :error="invalidName"
              :error-message="nameError"
              @update:model-value="checkName"
            />
          </q-popup-edit>
        </template>
        <template #description="{ }">
          <div class="row items-center no-wrap">
            <div style="white-space: pre-line; overflow-wrap: break-word; ">
              {{ description }}
            </div>
            <q-btn icon="edit" round size="sm" color="primary" flat class="q-ml-xs" />
          </div>
          <q-popup-edit v-model.trim="description" auto-save v-slot="scope" buttons>
            <q-input
              v-model="scope.value"
              dense
              autofocus
              counter
              type="textarea"
              @keyup.enter.stop
            />
          </q-popup-edit>
        </template>
      </KeyValueTable>
      <div class="float-right q-my-sm">
        <q-btn
          outline  
          color="primary" 
          label="Revert"
          class="q-mr-lg cancel-btn"
          @click="revertValues"
          :disable="!valuesChanged"
        />
        <q-btn
          label="Save"
          color="primary"
          @click="updatePlugin"
          :disable="!valuesChanged"
        >
          <q-tooltip v-if="!valuesChanged">
            No changes detected — nothing to save
          </q-tooltip>
        </q-btn>
      </div>
    </q-card>
  </q-expansion-item>

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
  <DeleteDialog
    v-model="showDeletePluginDialog"
    @submit="deletePlugin"
    type="Plugin"
    :name="name"
  />

  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="files"
    @refreshTable="tableRef.refreshTable()"
  />
</template>

<script setup>
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import { useRoute, useRouter } from 'vue-router'
import PageTitle from '@/components/PageTitle.vue'
import { ref, computed, onMounted } from 'vue'
import KeyValueTable from '@/components/KeyValueTable.vue'
import TableComponent from '@/components/TableComponent.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'

const route = useRoute()
const router = useRouter()

const plugin = ref()

const name = ref('')
const description = ref('')

onMounted(() => {
  getPlugin()
})

const ORIGINAL_PLUGIN = ref()

async function getPlugin() {
  try {
    const res = await api.getItem('plugins', route.params.id)
    plugin.value = res.data
    name.value = res.data.name
    description.value = res.data.description
    ORIGINAL_PLUGIN.value = JSON.parse(JSON.stringify(plugin.value))
  } catch(err) {
    console.warn(err)
  }
}

const pluginRows = computed(() => [
  { label: 'Name', slot: 'name' },
  { label: 'Description', slot: 'description' },
])

const invalidName = ref(false)
const nameError = ref('')

function requiredRule(val) {
  if(!val || val.length === 0) {
    invalidName.value = true
    nameError.value = 'Name is required'
    return false
  }
  invalidName.value = false
  nameError.value = ''
  return true
}

function checkName(val) {
  if(val.length === 0) {
    invalidName.value = true
    nameError.value = 'Name is required'
  } else {
    invalidName.value = false
    nameError.value = ''
  }
}

function revertValues() {
  name.value = JSON.parse(JSON.stringify(ORIGINAL_PLUGIN.value.name))
  description.value = JSON.parse(JSON.stringify(ORIGINAL_PLUGIN.value.description))
}

async function updatePlugin() {
  try {
    const res = await api.updateItem('plugins', route.params.id, {
      name: name.value,
      description: description.value,
    })
    getPlugin()
    notify.success(`Successfully updated '${res.data.name}'`)
  } catch(err) {
    notify.error(err.response.data.message)
  }  
}

const valuesChanged = computed(() => {
  if(name.value !== ORIGINAL_PLUGIN.value?.name || description.value !== ORIGINAL_PLUGIN.value?.description) {
    return true
  }
  return false
})

/*
  Plugin Files Table 
*/
const files = ref([])
const selected = ref([])
const showDeleteDialog = ref(false)
const showTagsDialog = ref(false)
const editObjTags = ref({})
const tableRef = ref(null)

const fileColumns = [
  { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false, },
  { name: 'filename', label: 'Filename', align: 'left', field: 'filename', sortable: true, },
  { name: 'description', label: 'Description', field: 'description', align: 'left', sortable: true },
  { name: 'functionTasks', label: 'Function Tasks', align: 'left', sortable: false, },
  { name: 'artifactTasks', label: 'Artifact Tasks', align: 'left', sortable: false, },
  { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
]

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

const showDeletePluginDialog = ref(false)

async function deletePlugin() {
  try {
    await api.deleteItem('plugins', route.params.id)
    notify.success(`Successfully deleted '${name}'`)
    router.push(`/plugins`)
  } catch(err) {
    notify.error(err.response.data.message);
  }
}

const showMetadata = ref(false)

</script>