<template>
  <PageTitle />

  <TableComponent 
    :rows="experiments"
    :columns="columns"
    title="Experiments"
    v-model="selected"
    @click="console.log(experiments)"
  >
    <template #body-cell-tags="props">
      <q-chip v-for="(tag, i) in props.row.tags" :key="i" color="primary" text-color="white">
        {{ tag }}
      </q-chip>
    </template>
  </TableComponent>

  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
  >
    <span class="sr-only">Create a new Experiment</span>
    <q-tooltip>
      Create a new Experiment
    </q-tooltip>
    <q-menu>
      <q-list>
        <q-item clickable to="/experiments/create">
          <q-item-section>Create Experiment</q-item-section>
        </q-item>
        <q-separator />
        <q-item clickable>
          <q-item-section>Create Job</q-item-section>
        </q-item>
        <q-separator />
        <q-item clickable>
          <q-item-section>Create Entry Point</q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>
</template>

<script setup>
  import PageTitle from '@/components/PageTitle.vue'
  import TableComponent from '@/components/TableComponent.vue'
  import { reactive, ref } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  const store = useDataStore()

  const experiments = store.experiments

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'draft', label: 'Draft', align: 'left', field: 'draft', sortable: true },
    { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true },
    { name: 'entryPoints', label: 'Entry Points', align: 'left', field: 'entryPoints', sortable: true },
    { name: 'tags', label: 'Tags', align: 'left',sortable: false },
  ]

  const selected = ref([])


</script>
@/stores/DataStore