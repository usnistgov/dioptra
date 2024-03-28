<template>
  <TableComponent 
    :rows="store.entryPoints"
    :columns="columns"
    title="Entry Points"
    v-model="selected"
    :pagination="{sortBy: 'draft', descending: true}"
    @edit="store.editEntryPoint = selected[0]; router.push('/entrypoints/create')"
    @click="console.log(store.entryPoints)"
  >
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
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { ref } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'

  const store = useDataStore()

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, },
    { name: 'parameterNames', label: 'Parameter Name(s)', align: 'left', sortable: true },
    { name: 'parameterTypes', label: 'Parameter Type(s)', align: 'left', field: 'parameterTypes', sortable: true },
    { name: 'defaultValues', label: 'Default Values', align: 'left', field: 'defaultValues', sortable: true },
  ]

  const selected = ref([])

  // const entryPoints = ref([
  //   { 
  //     name: 'Entry Point 1', 
  //     parameters: [
  //       {name: 'data_dir', default_value: 'nfs/data', parameter_type: 'path'},
  //       {name: 'image_size', default_value: '28-28-1', parameter_type: 'String'},
  //       {name: 'test_param', default_value: 'hello', parameter_type: 'String'},
  //     ]
  //   }
  // ])

</script>