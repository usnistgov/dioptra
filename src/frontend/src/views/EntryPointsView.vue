<template>
  <TableComponent 
    :rows="store.entryPoints"
    :columns="columns"
    :showExpand="true"
    title="Entry Points"
    v-model:selected="selected"
    :pagination="{sortBy: 'draft', descending: true}"
    @edit="store.editEntryPoint = selected[0]; router.push('/entrypoints/create')"
  >
    <template #body-cell-taskGraph="props">
      <q-btn
        v-if="props.row.task_graph.length"
        label="View YAML"
        color="primary"
        @click.stop="displayYaml = props.row.task_graph; showTaskGraphDialog = true;"
      />
      <span v-else class="text-negative">
        EMPTY
      </span>
    </template>
    <template #body-cell-parameterNames="props">
      <label v-for="(param, i) in props.row.parameters" :key="i">
        {{ param.name }} <br>
      </label>
    </template>
    <template #body-cell-parameterTypes="props">
      <label v-for="(param, i) in props.row.parameters" :key="i">
        {{ param.parameter_type }} <br>
      </label>
    </template>
    <template #body-cell-defaultValues="props">
      <label v-for="(param, i) in props.row.parameters" :key="i">
        {{ param.default_value }} <br>
      </label>
    </template>
    <template #expandedSlot="{ row }">
      <CodeEditor v-model="row.task_graph" language="yaml" />
    </template>
  </TableComponent>

  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
    to="/entrypoints/create"
  >
    <span class="sr-only">Register new Entry Point</span>
    <q-tooltip>
      Register new Entry Point
    </q-tooltip>
  </q-btn>

  <InfoPopupDialog
    v-model="showTaskGraphDialog"
  >
    <template #title>
      <label id="modalTitle">
        Task Graph YAML
      </label>
    </template>
    <CodeEditor v-model="displayYaml" style="height: 500px;" />
  </InfoPopupDialog>
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import { useRouter } from 'vue-router'
  import CodeEditor from '@/components/CodeEditor.vue'
  import InfoPopupDialog from '@/dialogs/InfoPopupDialog.vue'
  
  const router = useRouter()

  const store = useDataStore()

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true, },
    { name: 'taskGraph', label: 'Task Graph', align: 'left', field: 'task_graph',sortable: true, },
    { name: 'parameterNames', label: 'Parameter Name(s)', align: 'left', sortable: true },
    { name: 'parameterTypes', label: 'Parameter Type(s)', align: 'left', field: 'parameterTypes', sortable: true },
    { name: 'defaultValues', label: 'Default Values', align: 'left', field: 'defaultValues', sortable: true },
  ]

  const selected = ref([])

  const showTaskGraphDialog = ref(false)
  const displayYaml = ref('')

</script>