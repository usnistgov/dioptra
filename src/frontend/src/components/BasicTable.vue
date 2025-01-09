<template>
  <q-table
    :columns="columns"
    :rows="rows"
    dense
    flat
    bordered
    separator="cell"
    :filter="filter"
    :rows-per-page-options="[0]"
    :title="title"
  >
    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
          <div v-if="col.name === 'actions'">
            <q-btn icon="edit" round size="sm" color="primary" flat @click="$emit('edit', props.row, props.rowIndex)" v-if="!hideEditRow" />
            <q-btn icon="sym_o_delete" round size="sm" color="negative" flat @click="$emit('delete', props.row)" v-if="!hideDelete" />
          </div>
          <div v-if="typeof(col.value) === 'boolean' && editMode" class="text-body1" >
            <q-checkbox
              v-model="props.row[col.name]"
              @update:model-value="handleCheckboxUpdate(col.name, props.row[col.name], props.row)"
              size="xs"
              :disable="(col.name !== 'admin' && col.name !== 'owner') && (props.row.owner || props.row.admin)"
            />
          </div>
          <div v-else-if="typeof(col.value) === 'boolean'" class="text-body1">
            {{ col.value ? '✅' : 	'❌'}}
          </div>
          <div v-else-if="inlineEditFields && inlineEditFields.includes(col.name)" class="text-body1">
            {{ props.row.value }}
            <q-btn icon="edit" round size="sm" color="primary" flat />
            <q-popup-edit v-model="props.row.value" v-slot="scope">
              <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
            </q-popup-edit>
          </div>
          <div v-else>
            {{ col.value }}
          </div>
        </q-td>
      </q-tr>
    </template>
    <template #top-right v-if="!hideEditTable || !hideSearch">
      <q-btn 
        :color="editMode ? 'secondary' : 'primary'" 
        :icon="editMode ? 'save' : 'edit'" 
        :label="editMode ? 'Save' : 'Edit'" 
        class="q-mr-lg" 
        @click="editMode = !editMode" 
        v-if="!hideEditTable"
        style="width: 105px;"
      />
      <q-input v-model="filter" dense placeholder="Search" outlined v-if="!hideSearch">
          <template #append>
            <q-icon name="search" />
          </template>
        </q-input>
    </template>
  </q-table>
</template>

<script setup>
  import { ref } from 'vue'

  defineProps(['columns', 'rows', 'hideSearch', 'hideEditTable', 'hideEditRow', 'hideDelete', 'title', 'inlineEditFields'])

  const editMode = ref(false)

  const filter = ref('')

  function handleCheckboxUpdate(name, value, row) {
    if((name === 'admin' || name === 'owner') && value === true) {
      row.read = true
      row.write = true
      row.shareRead = true
      row.shareWrite = true
    }
  }

</script>