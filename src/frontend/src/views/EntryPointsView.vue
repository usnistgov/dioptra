<template>
  <PageTitle 
    title="Entrypoints"
    resourceType="entrypoint"
    subtitle="Reusable workflows composed of Tasks"
  />
  <TableComponent 
    :rows="entrypoints"
    :columns="columns"
    title="Entrypoints"
    v-model:selected="selected"
    @open="openTab => (openTab
      ? openWindow.open(`/entrypoints/${selected[0].id}`, '_blank')
      : router.push(`/entrypoints/${selected[0].id}`)
    )"
    @delete="showDeleteDialog = true"
    @request="getEntrypoints"
    ref="tableRef"
    @editTags="(row) => { editObjTags = row; showTagsDialog = true }"
    @create="router.push('/entrypoints/new')"
    :loading="isLoading"
  >
    <template #body-cell-group="props">
      <div>{{ props.row.group.name }}</div>
    </template>
    <template #body-cell-taskGraph="props">
      <q-btn
        v-if="props.row.taskGraph.length"
        label="View YAML"
        color="primary"
        @click.stop="displayYaml = props.row.taskGraph; showTaskGraphDialog = true;"
      />
      <span v-else class="text-negative">
        EMPTY
      </span>
    </template>
    <template #body-cell-plugins="props">
      <ResourceBadge
        v-for="(plugin, i) in props.row.plugins"
        :key="i"
        :resource="plugin"
        resourceType="plugin"
        @sync="() => syncPlugin(props.row.id, plugin.id, plugin.name, 'plugins')"
      />
      <q-btn
        round
        size="sm"
        icon="add"
        @click.stop="editEntrypoint = props.row; pluginType = 'plugins'; showAssignPluginsDialog = true"
        class="q-ml-sm"
      />
    </template>
    <template #body-cell-artifactPlugins="props">
      <ResourceBadge
        v-for="(plugin, i) in props.row.artifactPlugins"
        :key="i"
        :resource="plugin"
        resourceType="plugin"
        @sync="() => syncPlugin(props.row.id, plugin.id, plugin.name, 'artifactPlugins')"
      />
      <q-btn
        round
        size="sm"
        icon="add"
        @click.stop="editEntrypoint = props.row; pluginType = 'artifactPlugins'; showAssignPluginsDialog = true"
        class="q-ml-sm"
      />
    </template>
  </TableComponent>

  <InfoPopupDialog
    v-model="showTaskGraphDialog"
  >
    <template #title>
      <label id="modalTitle">
        Task Graph YAML
      </label>
    </template>
    <CodeEditor v-model="displayYaml" style="height: auto;" :readOnly="true" />
  </InfoPopupDialog>
  <DeleteDialog 
    v-model="showDeleteDialog"
    @submit="deleteEntryPoint"
    type="Entry Point"
    :name="selected.length ? selected[0].name : ''"
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

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import CodeEditor from '@/components/CodeEditor.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
  import * as api from '@/services/dataApi'
  import * as notify from '../notify'
  import DeleteDialog from '@/dialogs/DeleteDialog.vue'
  import PageTitle from '@/components/PageTitle.vue'
  import AssignTagsDialog from '@/dialogs/AssignTagsDialog.vue'
  import AssignPluginsDialog from '@/dialogs/AssignPluginsDialog.vue'
  import ResourceBadge from '@/components/ResourceBadge.vue'

  const openWindow = window
  const router = useRouter()

  const columns = [
    { name: 'id', label: 'ID', align: 'left', field: 'id', sortable: false, },
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, },
    { name: 'taskGraph', label: 'Task Graph', align: 'left', field: 'taskGraph',sortable: false, },
    { name: 'plugins', label: 'Plugins', align: 'left', field: 'plugins', sortable: false },
    { name: 'artifactPlugins', label: 'Artifact Plugins', align: 'left', field: 'artifactPlugins', sortable: false },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
    { name: 'lastModifiedOn', label: 'Last Modified', align: 'left', field: 'lastModifiedOn', sortable: true },
  ]

  const selected = ref([])

  const showTaskGraphDialog = ref(false)
  const displayYaml = ref('')

  const tableRef = ref(null)
  
  const isLoading = ref(false)

  const entrypoints = ref([])

  const showDeleteDialog = ref(false)
  const showAssignPluginsDialog = ref(false)
  const editEntrypoint = ref('')
  const pluginType = ref('')

  async function getEntrypoints(pagination, showDrafts) {
    isLoading.value = true
      
    const minLoadTimePromise = new Promise(resolve => setTimeout(resolve, 300)); 

    try {
      const [res] = await Promise.all([
        api.getData('entrypoints', pagination, showDrafts),
        minLoadTimePromise
      ]);
        
      entrypoints.value = res.data.data;
      tableRef.value.updateTotalRows(res.data.totalNumResults);
    } catch(err) {
      console.log('err = ', err);
      notify.error(err.response.data.message);
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteEntryPoint() {
    try {
      await api.deleteItem('entrypoints', selected.value[0].id)
      notify.success(`Successfully deleted '${selected.value[0].name}'`)
      showDeleteDialog.value = false
      selected.value = []
      tableRef.value.refreshTable()
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  const editObjTags = ref({})
  const showTagsDialog = ref(false)

  async function syncPlugin(entrypointId, pluginId, pluginName, pluginType) {
    try {
      await api.addPluginsToEntrypoint(entrypointId, [pluginId], pluginType)
      tableRef.value.refreshTable()
      notify.success(`Successfully updated plugin '${pluginName}' to latest version`)
    } catch(err) {
      console.warn(err)
    }
  }

</script>
