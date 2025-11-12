<template>
  <PageTitle 
    title="Entrypoints"
  />
  <TableComponent 
    :rows="entrypoints"
    :columns="columns"
    title="Entrypoints"
    v-model:selected="selected"
    @edit="router.push(`/entrypoints/${selected[0].id}`)"
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
      <span
        v-for="(plugin, i) in props.row.plugins"
        :key="i"
      >
        <q-chip
          color="secondary" 
          text-color="white"
          clickable
          @click.stop="editEntrypoint = props.row; showAssignPluginsDialog = true"
        >
          {{ plugin.name }}
          <q-badge
            v-if="!plugin.latestSnapshot" 
            color="red" 
            label="outdated" 
            rounded
            class="q-ml-xs"
          />
        </q-chip>
        <q-btn
          v-if="!plugin.latestSnapshot"
          round 
          color="red" 
          icon="sync"
          size="sm"
          @click.stop="syncPlugin(props.row.id, plugin.id, plugin.name)"
          class="q-mr-md"
        >
          <q-tooltip>
            Sync to latest version of plugin
          </q-tooltip>
        </q-btn>
      </span>
      <q-btn
        round
        size="sm"
        icon="add"
        @click.stop="editEntrypoint = props.row; showAssignPluginsDialog = true"
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

  const router = useRouter()

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'description', label: 'Description', align: 'left', field: 'description', sortable: true, },
    { name: 'taskGraph', label: 'Task Graph', align: 'left', field: 'taskGraph',sortable: false, },
    { name: 'tags', label: 'Tags', align: 'left', field: 'tags', sortable: false },
    { name: 'plugins', label: 'Plugins', align: 'left', field: 'plugins', sortable: false },
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

  async function syncPlugin(entrypointId, pluginId, pluginName) {
    try {
      await api.addPluginsToEntrypoint(entrypointId, [pluginId], 'plugins')
      tableRef.value.refreshTable()
      notify.success(`Successfully updated plugin '${pluginName}' to latest version`)
    } catch(err) {
      console.warn(err)
    }
  }

</script>
