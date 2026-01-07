<template>
  <PageTitle 
    title="Entrypoints" 
    caption="Reusable workflows composed of Tasks"
    conceptType="entrypoint" 
  />
  
  <TableComponent 
    ref="tableRef"
    :rows="entrypoints"
    :columns="computedColumns"
    title="Entrypoints"
    v-model:selected="selected"
    :loading="isLoading"
    
    @request="getEntrypoints"
    @create="router.push('/entrypoints/new')"
    @edit="(row) => router.push(`/entrypoints/${row.id}`)"
    
    @delete="(row) => { selected = [row]; showDeleteDialog = true }"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
  >
    
    <template #body-cell-taskGraph="props">
      <q-btn
        v-if="props.row.taskGraph && props.row.taskGraph.length"
        outline dense no-caps color="grey-8" 
        label="YAML"
        icon="code"
        size="xs"
        class="q-px-sm q-py-xs"
        style="font-size:12px; font-weight:bold"
        @click.stop="displayYaml = props.row.taskGraph; showTaskGraphDialog = true;"
      />
      <span v-else class="text-grey-5 text-caption">Empty</span>
      <q-tooltip>View '{{ props.row.name || "Entrypoint" }}' Task Graph YAML</q-tooltip>
    </template>

<template #body-cell-plugins="props">
  <div class="q-py-xs" style="min-width: 200px;">
    <div 
      class="plugin-container column q-pa-xs q-gutter-y-xs cursor-pointer"
      @click.stop="openPluginDialog(props.row, 'plugins')"
    >
      <div class="absolute-top-right q-ma-xs plugin-edit-btn" style="z-index: 10">
        <q-btn round dense flat size="xs" icon="edit" color="grey-9" class="bg-white shadow-1" />
        <q-tooltip>Manage Attached Plugins</q-tooltip>
      </div>

      <template v-if="props.row.plugins.length > 0">
        <template v-for="(plugin, i) in props.row.plugins.slice(0, 3)" :key="i">
          <div class="row items-center no-wrap bg-white q-pa-none shadow-1" style="border-radius: 4px; border: 1px solid #eeeeee; width:fit-content; max-width:220px">
            
            <q-chip
              :color="getConceptStyle('plugin').color" 
              text-color="white"
              size="sm" outline square clickable
              class="text-weight-bold q-py-sm q-pr-sm q-ma-none no-border full-width"
              @click.stop="openPluginDialog(props.row, 'plugins')"
            >
              <span class="font-mono ellipsis" style="font-size: 11px; font-weight:500; max-width:140px">
                {{ plugin.name }}
              </span>

              <template v-if="!plugin.latestSnapshot">
                <div style="height: 12px; width: 1px; background-color: #ddd; margin: 0 6px;"></div>

                <q-badge rounded color="warning" class="q-mr-xs" style="padding: 2px;">
                  <q-icon name="warning" color="white" size="10px" />
                  <q-tooltip anchor="center right">Plugin out of date</q-tooltip>
                </q-badge>

                <q-btn 
                  flat round dense 
                  size="xs" 
                  color="red" 
                  icon="sync" 
                  @click.stop="syncPlugin(props.row.id, plugin.id, plugin.name, 'plugins')"
                >
                  <q-tooltip anchor="center right">Sync to latest</q-tooltip>
                </q-btn>
              </template>

              <q-tooltip>ID: {{ plugin.id }}</q-tooltip>
            </q-chip>
          </div>
        </template>

        <div v-if="props.row.plugins.length > 3">
          <q-chip
            dense clickable
            color="grey-3" text-color="grey-9"
            class="text-weight-bold"
            style="font-size: 11px; border:1px solid lightgrey;"
            @click.stop 
          >
            +{{ props.row.plugins.length - 3 }} more
            
            <q-menu anchor="bottom middle" self="top middle" class="bg-white shadow-5 border-grey-3">
              <div class="column q-pa-sm q-gutter-y-xs" style="min-width: 200px">
                <div class="text-caption text-grey-7 q-mb-xs text-weight-bold">Additional Plugins</div>
                <template v-for="(plugin, i) in props.row.plugins.slice(3)" :key="i">
                  <div class="row items-center justify-between no-wrap bg-grey-1 q-pa-xs border-radius-inherit">
                    <q-chip
                      :color="getConceptStyle('plugin').color" 
                      text-color="white" :icon="getConceptStyle('plugin').icon"
                      size="sm" outline square clickable class="text-weight-bold q-my-none"
                      @click.stop="openPluginDialog(props.row, 'plugins')"
                    >
                      {{ plugin.name }}
                    <q-tooltip>ID: {{ plugin.id }}</q-tooltip>
                    </q-chip>
                    <q-btn v-if="!plugin.latestSnapshot" flat round size="xs" color="red" icon="sync" @click.stop="syncPlugin(props.row.id, plugin.id, plugin.name, 'plugins')" />
                  </div>
                </template>
              </div>
            </q-menu>
          </q-chip>
        </div>
      </template>
      <div v-else class="text-caption text-center text-grey-9 q-pa-xs">No plugins</div>
    </div>
  </div>
</template>
<template #body-cell-artifactPlugins="props">
  <div class="q-py-xs" style="min-width: 200px;">
    <div 
      class="plugin-container column q-pa-xs q-gutter-y-xs cursor-pointer"
      @click.stop="openPluginDialog(props.row, 'artifactPlugins')"
    >
      <div class="absolute-top-right q-ma-xs plugin-edit-btn" style="z-index: 10">
        <q-btn round dense flat size="xs" icon="edit" color="grey-9" class="bg-white shadow-1" />
        <q-tooltip>Manage Attached Plugins</q-tooltip>
      </div>

      <template v-if="props.row.artifactPlugins.length > 0">
        <template v-for="(plugin, i) in props.row.artifactPlugins.slice(0, 3)" :key="i">
          <div class="row items-center no-wrap bg-white q-pa-none shadow-1" style="border-radius: 4px; border: 1px solid #eeeeee; width:fit-content; max-width:220px">
            
            <q-chip
              :color="getConceptStyle('plugin').color" 
              text-color="white"
              size="sm" outline square clickable
              class="text-weight-bold q-py-sm q-pr-sm q-ma-none no-border full-width"
              @click.stop="openPluginDialog(props.row, 'artifactPlugins')"
            >
              <span class="font-mono ellipsis" style="font-size: 11px; font-weight:500; max-width:140px">
                {{ plugin.name }}
              </span>

              <template v-if="!plugin.latestSnapshot">
                <div style="height: 12px; width: 1px; background-color: #ddd; margin: 0 6px;"></div>

                <q-badge rounded color="warning" class="q-mr-xs" style="padding: 2px;">
                   <q-icon name="warning" color="white" size="10px" />
                   <q-tooltip anchor="center right">Plugin out of date</q-tooltip>
                </q-badge>

                <q-btn 
                  flat round dense 
                  size="xs" 
                  color="red" 
                  icon="sync" 
                  @click.stop="syncPlugin(props.row.id, plugin.id, plugin.name, 'artifactPlugins')"
                >
                  <q-tooltip anchor="center right">Sync to latest</q-tooltip>
                </q-btn>
              </template>

              <q-tooltip>Plugin ID: {{ plugin.id }}</q-tooltip>
            </q-chip>
          </div>
        </template>

        <div v-if="props.row.artifactPlugins.length > 3">
          <q-chip
            dense clickable
            color="grey-3" text-color="grey-9"
            class="text-weight-bold"
            style="font-size: 11px; border:1px solid lightgrey;"
            @click.stop
          >
            +{{ props.row.artifactPlugins.length - 3 }} more
            <q-menu anchor="bottom middle" self="top middle" class="bg-white shadow-5 border-grey-3">
              <div class="column q-pa-sm q-gutter-y-xs" style="min-width: 200px">
                <div class="text-caption text-grey-7 q-mb-xs text-weight-bold">Additional Artifact Plugins</div>
                <template v-for="(plugin, i) in props.row.artifactPlugins.slice(3)" :key="i">
                  <div class="row items-center justify-between no-wrap bg-grey-1 q-pa-xs border-radius-inherit">
                    <q-chip
                      :color="getConceptStyle('plugin').color" 
                      text-color="white" :icon="getConceptStyle('plugin').icon"
                      size="sm" outline square clickable class="text-weight-bold q-my-none"
                      @click.stop="openPluginDialog(props.row, 'artifactPlugins')"
                    >
                      {{ plugin.name }}
                      <q-tooltip>ID: {{ plugin.id }}</q-tooltip>
                    </q-chip>
                    <q-btn v-if="!plugin.latestSnapshot" flat round size="xs" color="red" icon="sync" @click.stop="syncPlugin(props.row.id, plugin.id, plugin.name, 'artifactPlugins')" />
                  </div>
                </template>
              </div>
            </q-menu>
          </q-chip>
        </div>
      </template>
      <div v-else class="text-caption text-center text-grey-9 q-pa-xs">No artifact plugins</div>
    </div>
  </div>
</template>

  </TableComponent>

  <InfoPopupDialog v-model="showTaskGraphDialog">
    <template #title>Task Graph YAML</template>
    <CodeEditor v-model="displayYaml" style="height: auto;" :readOnly="true" />
  </InfoPopupDialog>

  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteEntryPoint"
    type="Entry Point"
    :name="selected[0]?.name || ''"
  />

  <AssignTagsDialog 
    v-model="showTagsDialog"
    :editObj="editObjTags"
    type="entrypoints"
    @refreshTable="tableRef.refreshTable()"
  />

  <AssignPluginsDialog 
    v-model="showAssignPluginsDialog"
    :pluginType="pluginType"
    :editObj="editEntrypoint"
    @refreshTable="tableRef.refreshTable()"
  />
</template>
<style scoped>

.plugin-container {
  position: relative;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fafafa; /* Very light grey */
  transition: all 0.2s ease;
  min-height: 40px; /* Ensure space even if empty */
  height:100%;
}

.plugin-container:hover {
  background-color: #f5f5f5; /* Slightly darker on hover */
  border-color: #bdbdbd;
}

/* Hide edit button by default */
.plugin-edit-btn {
  opacity: .4;
  transition: opacity 0.2s ease;
}

/* Show edit button when container is hovered */
.plugin-container:hover .plugin-edit-btn {
  opacity: 1;
}
</style>
<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import TableComponent from '@/components/table/TableComponent.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
import DeleteDialog from '@/dialogs/DeleteDialog.vue'
import PageTitle from '@/components/PageTitle.vue'
import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
import AssignPluginsDialog from '@/dialogs/AssignPluginsDialog.vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'
import { getConceptStyle } from '@/constants/tableStyles'

const router = useRouter()
const tableRef = ref(null)

// State
const entrypoints = ref([])
const isLoading = ref(false)
const selected = ref([])
const showDeleteDialog = ref(false)
const showAssignPluginsDialog = ref(false)
const showTaskGraphDialog = ref(false)
const showTagsDialog = ref(false)

const editEntrypoint = ref({})
const editObjTags = ref({})
const pluginType = ref('')
const displayYaml = ref('')

// Column Definitions
const computedColumns = computed(() => [
  { 
    name: 'id', 
    label: 'Entrypoint ID', 
    field: 'id', 
    align: 'left', 
    styleType: 'icon-id', 
    conceptType: 'entrypoint',
    includeIcon: true 
  },
  { 
    name: 'name', 
    label: 'Name', 
    field: 'name', 
    align: 'left', 
    styleType: 'resource-name', 
    conceptType: 'entrypoint',
    textType: 'capitalize',
    maxWidth: '180px',
    sortable: true
  },
  { 
    name: 'description', 
    label: 'Description', 
    field: 'description', 
    align: 'left', 
    styleType: 'long-text',
    maxWidth: '150px',
    maxLength: 60,
    useQuotes: false,
    style: 'max-width: 300px;',
    sortable: true
  },
  { 
    name: 'taskGraph', 
    label: 'Task Graph', 
    field: 'taskGraph', 
    align: 'left',
    // Handled by slot
  },
  { 
    name: 'plugins', 
    label: 'Plugins', 
    field: 'plugins', 
    align: 'left',
  },
  { 
    name: 'artifactPlugins', 
    label: 'Artifact Plugins', 
    field: 'artifactPlugins', 
    align: 'left',
  },
  { 
    name: 'group', 
    label: 'Group', 
    field: 'group', 
    align: 'left', 
    styleType: 'icon-badge',
    conceptType: 'group',
    showIcon: false
  },
  { 
    name: 'tags', 
    label: 'Tags', 
    field: 'tags', 
    align: 'left', 
    styleType: 'tag-list' 
  }
])

// --- ACTIONS ---

function openPluginDialog(row, type) {
  editEntrypoint.value = row
  pluginType.value = type
  showAssignPluginsDialog.value = true
}

async function getEntrypoints(pagination, showDrafts) {
  isLoading.value = true
  const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300))

  try {
    const [res] = await Promise.all([
      api.getData('entrypoints', pagination, showDrafts),
      minLoadTimePromise
    ])
    
    entrypoints.value = res.data.data
    tableRef.value.updateTotalRows(res.data.totalNumResults)
  } catch(err) {
    notify.error(err.response?.data?.message || 'Failed to fetch entrypoints')
  } finally {
    isLoading.value = false
  }
}

async function deleteEntryPoint() {
  try {
    const id = selected.value[0].id
    await api.deleteItem('entrypoints', id)
    notify.success(`Successfully deleted '${selected.value[0].name}'`)
    showDeleteDialog.value = false
    selected.value = []
    tableRef.value.refreshTable()
  } catch(err) {
    notify.error(err.response?.data?.message)
  }
}

async function syncPlugin(entrypointId, pluginId, pluginName, pType) {
  try {
    await api.addPluginsToEntrypoint(entrypointId, [pluginId], pType)
    tableRef.value.refreshTable()
    notify.success(`Updated '${pluginName}' to latest version`)
  } catch(err) {
    console.warn(err)
    notify.error('Failed to sync plugin')
  }
}
</script>