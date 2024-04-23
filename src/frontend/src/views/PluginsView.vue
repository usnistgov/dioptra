<template>
  <TableComponent 
    :rows="store.plugins"
    :columns="columns"
    title="Plugins"
    v-model="selected"
    :pagination="{sortBy: 'draft', descending: true}"
    @edit="store.editMode = true; router.push(`/plugins/${selected[0].id}`)"
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
    @click="showAddDialog = true"
  >
    <span class="sr-only">Register a new Plugin</span>
    <q-tooltip>
      Register a new Plugin
    </q-tooltip>
  </q-btn>
  <AddPluginDialog 
    v-model="showAddDialog"
    @addPlugin="addPlugin"
  />
</template>

<script setup>
  import TableComponent from '@/components/TableComponent.vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  import AddPluginDialog from '@/dialogs/AddPluginDialog.vue'
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const store = useDataStore()

  const selected = ref([])
  const showAddDialog = ref(false)
  const showDeleteDialog = ref(false)

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true, sort: (a, b) => a - b },
    { name: 'group', label: 'Group', align: 'left', field: 'group', sortable: true },
    { name: 'files', label: 'Files', align: 'left',sortable: false },
    { name: 'tags', label: 'Tags', align: 'left',sortable: false },
  ]

  function addPlugin(plugin) {
    store.plugins.push(plugin)
  }

</script>