<template>
  <q-table
    :columns="props.columns"
    :rows="props.rows"
    dense
    flat
    bordered
    class="q-mt-lg"
    separator="horizontal"
    :filter="filter"
  >
    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
          <div v-if="col.name === 'actions'">
            <q-btn icon="edit" round size="sm" color="primary" flat @click="$emit('edit', props.row, props.rowIndex)" />
            <q-btn icon="sym_o_delete" round size="sm" color="negative" flat @click="$emit('delete', props.row)" />
          </div>
          <div v-if="typeof(col.value) === 'boolean'" class="text-body1">
            {{ col.value ? '✅' : 	'❌'}}
          </div>
          <div v-else>
            {{ col.value }}
          </div>
        </q-td>
      </q-tr>
    </template>
    <template #body-cell-actions="props">
      <q-td :props="props">
        <q-btn icon="edit" round size="sm" color="primary" flat @click="$emit('edit', props.row, props.rowIndex)" />
        <q-btn icon="sym_o_delete" round size="sm" color="negative" flat @click="$emit('delete', props.row)" />
      </q-td>
    </template>
    <template #top-right>
      <q-input v-model="filter" dense placeholder="Search" outlined v-if="!props.hideSearch || props.hideSearch === undefined">
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
    </template>
  </q-table>
</template>

<script setup>
  import { ref } from 'vue'

  const props = defineProps(['columns', 'rows', 'hideSearch'])


  const filter = ref('')

</script>